import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict
from datetime import datetime

class AmazonConsoleScraper:
    """Amazon product scraper - Fixed for PKR prices"""
    
    def __init__(self):
        self.session = requests.Session()
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
    def get_headers(self) -> Dict:
        """Generate headers for request"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        return headers
    
    def search_products(self, query: str, max_pages: int = None, progress_callback=None) -> List[Dict]:
        """Search for products on Amazon"""
        all_products = []
        base_url = "https://www.amazon.com/s"
        
        print(f"🔍 Searching Amazon for: '{query}'")
        
        page = 1
        consecutive_empty_pages = 0
        
        while True:
            try:
                params = {
                    'k': query,
                    'page': page,
                    'ref': f'nb_sb_noss_{page}'
                }
                
                print(f"📄 Scraping Amazon page {page}...")
                time.sleep(random.uniform(3, 5))
                
                response = self.session.get(
                    base_url,
                    params=params,
                    headers=self.get_headers(),
                    timeout=15
                )
                
                if response.status_code == 200:
                    page_products = self.parse_search_results(response.text)
                    
                    if not page_products:
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= 2:
                            print(f"✅ No more products found. Total: {len(all_products)}")
                            break
                    else:
                        consecutive_empty_pages = 0
                        
                        # Add page number to each product
                        for product in page_products:
                            product['page_number'] = page
                        
                        all_products.extend(page_products)
                        print(f"   Found {len(page_products)} products (Total: {len(all_products)})")
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(page, max_pages or 999, len(all_products))
                    
                    # Check if we've reached max_pages
                    if max_pages and page >= max_pages:
                        break
                        
                    page += 1
                else:
                    print(f"❌ Failed to fetch page {page}. Status: {response.status_code}")
                    break
                        
            except Exception as e:
                print(f"❌ Error scraping page {page}: {str(e)}")
                break
        
        print(f"✅ Amazon scraping complete! Total products: {len(all_products)}")
        return all_products
    
    def parse_search_results(self, html: str) -> List[Dict]:
        """Parse Amazon search results"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Find all product containers
        containers = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        if not containers:
            containers = soup.find_all('div', class_='s-result-item')
        
        for container in containers:
            try:
                asin = container.get('data-asin', '')
                if not asin or len(asin) < 5:
                    continue
                
                # Extract title
                title_elem = container.find('h2')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                if len(title) < 10:
                    continue
                
                # Extract price - FIXED for PKR (no smart correction)
                price_data = self.extract_price_pkr(container)
                
                # Extract rating
                rating, rating_numeric, review_count = self.extract_rating_and_reviews(container)
                
                # Extract image
                img_elem = container.find('img', class_='s-image')
                image_url = img_elem.get('src') if img_elem else "https://via.placeholder.com/200?text=No+Image"
                
                # Extract URL
                link_elem = container.find('a', class_='a-link-normal')
                if link_elem and link_elem.get('href'):
                    url = "https://www.amazon.com" + link_elem.get('href')
                else:
                    url = f"https://www.amazon.com/dp/{asin}"
                
                # Check if sponsored
                is_sponsored = self.check_sponsored(container)
                
                product = {
                    'title': title,
                    'asin': asin,
                    'url': url,
                    'price': price_data['display'],
                    'price_numeric': price_data['numeric'],
                    'currency': 'PKR',  # Changed to PKR
                    'rating': f"{rating_numeric} out of 5 stars" if rating_numeric > 0 else "No ratings",
                    'rating_numeric': rating_numeric,
                    'reviews': review_count or "0",
                    'image_url': image_url,
                    'is_sponsored': is_sponsored,
                    'platform': 'Amazon',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                products.append(product)
                    
            except Exception as e:
                print(f"⚠️ Error parsing product: {str(e)}")
                continue
        
        return products
    
    def extract_price_pkr(self, container) -> dict:
        """Extract price for PKR (no division)"""
        
        # Try different price selectors
        price_selectors = [
            ('span.a-price span.a-offscreen', 'offscreen'),
            ('span.a-price[data-a-size="xl"] span.a-offscreen', 'xl'),
            ('span.a-price[data-a-size="l"] span.a-offscreen', 'l'),
            ('span.a-price[data-a-size="m"] span.a-offscreen', 'm'),
            ('span.a-price-whole', 'whole'),
        ]
        
        for selector, price_type in price_selectors:
            price_elem = container.select_one(selector)
            if price_elem:
                price_text = price_elem.text.strip()
                
                if price_type == 'whole':
                    # Remove commas
                    price_text = price_text.replace(',', '')
                    if price_text.endswith('.'):
                        price_text = price_text[:-1]
                    
                    # Check for fraction
                    fraction_elem = container.select_one('span.a-price-fraction')
                    if fraction_elem:
                        fraction = fraction_elem.text.strip()
                        if fraction and fraction != '00':
                            price_text = f"{price_text}.{fraction}"
                    else:
                        price_text = f"{price_text}.00"
                
                # Clean the price
                cleaned = re.sub(r'[^\d.]', '', price_text)
                
                # Handle multiple decimal points
                if cleaned.count('.') > 1:
                    parts = cleaned.split('.')
                    cleaned = parts[0] + '.' + parts[1]
                
                try:
                    numeric_price = float(cleaned)
                    
                    # For PKR, we keep the price as-is (no division)
                    # Format display price with Rs. prefix
                    if numeric_price >= 1000:
                        display_price = f"Rs. {numeric_price:,.0f}"
                    else:
                        display_price = f"Rs. {numeric_price:.2f}"
                    
                    return {
                        'display': display_price,
                        'numeric': numeric_price
                    }
                except:
                    continue
        
        # Try regex as fallback
        container_text = container.get_text()
        price_pattern = r'(?:Rs\.?|PKR)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        matches = re.findall(price_pattern, container_text, re.I)
        
        if matches:
            try:
                numeric_price = float(matches[0].replace(',', ''))
                if numeric_price >= 1000:
                    display_price = f"Rs. {numeric_price:,.0f}"
                else:
                    display_price = f"Rs. {numeric_price:.2f}"
                
                return {
                    'display': display_price,
                    'numeric': numeric_price
                }
            except:
                pass
        
        return {'display': 'Price unavailable', 'numeric': 0.0}
    
    def extract_rating_and_reviews(self, container):
        """Extract rating and review count"""
        rating = 0.0
        review_count = None
        rating_text = "No ratings"
        
        # Find rating
        rating_elem = container.find('span', class_='a-icon-alt')
        if rating_elem:
            rating_text = rating_elem.text.strip()
            try:
                match = re.search(r'(\d+\.?\d*)', rating_text)
                if match:
                    rating = float(match.group(1))
            except:
                pass
        
        # Find review count
        review_selectors = [
            'span.a-size-base.s-underline-text',
            'span.a-size-base[aria-label]',
            'span.a-size-base:has(+ span.a-icon-alt)',
            'span.a-size-base[data-component-type="s-client-side-analytics"]'
        ]
        
        for selector in review_selectors:
            review_elem = container.select_one(selector)
            if review_elem:
                review_text = review_elem.text.strip()
                match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?K?)', review_text, re.I)
                if match:
                    review_count = match.group(1)
                    break
        
        return rating_text, rating, review_count
    
    def check_sponsored(self, container) -> bool:
        """Check if product is sponsored"""
        sponsored_text = container.find(string=re.compile(r'Sponsored|Ad', re.I))
        return bool(sponsored_text)