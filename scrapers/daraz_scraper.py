import requests
import json
import time
import random
import re
from typing import List, Dict
from datetime import datetime

class DarazConsoleScraper:
    """Daraz API-based scraper - NO LIMIT version"""
    
    def __init__(self, country="pk"):
        self.base_domain = f"https://www.daraz.{country}"
        self.session = requests.Session()
        # REMOVED: self.max_products = 10
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        ]
    
    def get_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.base_domain,
            "Connection": "keep-alive"
        }
    
    def search_products(self, query: str, max_pages: int = None) -> List[Dict]:
        """
        Search for products on Daraz
        If max_pages is None, scrapes ALL available pages
        """
        all_products = []
        
        print(f"🔍 Searching Daraz for: '{query}'")
        
        page = 1
        consecutive_empty_pages = 0
        
        while True:
            try:
                url = f"{self.base_domain}/catalog/"
                
                params = {
                    "ajax": "true",
                    "q": query,
                    "page": page
                }
                
                headers = self.get_headers()
                
                print(f"📄 Scraping Daraz page {page}...")
                time.sleep(random.uniform(1.5, 3))
                
                response = self.session.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"❌ Failed to fetch page {page}. Status: {response.status_code}")
                    break
                
                data = response.json()
                items = data.get("mods", {}).get("listItems", [])
                
                if not items:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 2:
                        print(f"✅ No more products found. Total: {len(all_products)}")
                        break
                else:
                    consecutive_empty_pages = 0
                    
                    for item in items:
                        product = self.parse_product(item)
                        product['page_number'] = page
                        all_products.append(product)
                    
                    print(f"   Found {len(items)} products (Total: {len(all_products)})")
                
                # Check if we've reached max_pages (if specified)
                if max_pages and page >= max_pages:
                    break
                
                page += 1
                
            except Exception as e:
                print(f"❌ Error scraping Daraz page {page}: {str(e)}")
                break
        
        print(f"✅ Daraz scraping complete! Total products: {len(all_products)}")
        return all_products
    
    def parse_product(self, item: Dict) -> Dict:
        """Parse individual Daraz product"""
        # Generate a product ID from the URL
        item_url = item.get("itemUrl", "")
        product_id_match = re.search(r'-i(\d+)', item_url)
        product_id = product_id_match.group(1) if product_id_match else str(random.randint(100000, 999999))
        
        # Extract title
        title = item.get("name", "N/A")
        
        # Extract price (PKR)
        price_raw = item.get("price", "0")
        price_numeric = self.clean_pkr_price(price_raw)
        
        # Format price
        if price_numeric > 0:
            price_display = f"Rs. {price_numeric:,.0f}"
        else:
            price_display = "Price unavailable"
        
        # Extract old price if available
        old_price_raw = item.get("originalPrice", "0")
        old_price_numeric = self.clean_pkr_price(old_price_raw)
        if old_price_numeric > 0:
            old_price_display = f"Rs. {old_price_numeric:,.0f}"
        else:
            old_price_display = "N/A"
        
        # Format rating
        rating_score = item.get("ratingScore", 0)
        if rating_score and rating_score != "No rating":
            try:
                rating_score = float(rating_score)
                rating = f"{rating_score} out of 5 stars"
                rating_numeric = rating_score
            except:
                rating = "No ratings"
                rating_numeric = 0.0
        else:
            rating = "No ratings"
            rating_numeric = 0.0
        
        # Format reviews
        reviews_raw = item.get("review", "0")
        try:
            reviews_count = int(reviews_raw)
            if reviews_count > 1000:
                reviews_display = f"{reviews_count//1000}k+"
            else:
                reviews_display = str(reviews_count)
        except:
            reviews_display = "0"
        
        # Extract image
        image_url = item.get("image", "https://via.placeholder.com/200?text=No+Image")
        
        # Check if sponsored
        is_sponsored = item.get("isSponsored", False)
        
        return {
            'title': title,
            'asin': f"DZ{product_id}",
            'url': self.base_domain + item.get("itemUrl", ""),
            'price': price_display,
            'price_numeric': price_numeric,
            'currency': 'PKR',
            'old_price': old_price_display,
            'old_price_numeric': old_price_numeric,
            'rating': rating,
            'rating_numeric': rating_numeric,
            'reviews': reviews_display,
            'image_url': image_url,
            'is_sponsored': is_sponsored,
            'platform': 'Daraz',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def clean_pkr_price(self, price) -> float:
        """Clean PKR price string to float"""
        if isinstance(price, (int, float)):
            return float(price)
        cleaned = re.sub(r"[^\d.]", "", str(price))
        try:
            return float(cleaned)
        except:
            return 0.0