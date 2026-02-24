from flask import Flask, render_template, request, jsonify, session, Response
from scrapers import AmazonConsoleScraper, DarazConsoleScraper
from config import Config
import json
import time
from datetime import datetime
import pandas as pd
import csv
from io import StringIO
import threading
import os

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Store scraping progress (for large scrapes)
scraping_progress = {}

# Template filters
@app.template_filter('format_price')
def format_price(product):
    """Format price based on currency"""
    if not product or 'price_numeric' not in product:
        return 'N/A'
    
    price = product.get('price_numeric', 0)
    currency = product.get('currency', 'USD')
    
    if price <= 0:
        return 'Price unavailable'
    
    if currency == 'USD':
        if price >= 1000:
            return f"${price:,.0f}"
        else:
            return f"${price:.2f}"
    elif currency == 'PKR':
        return f"Rs. {price:,.0f}"
    else:
        return str(price)

@app.template_filter('format_number')
def format_number(value):
    """Format number with commas"""
    try:
        return f"{value:,.0f}"
    except:
        return value

@app.template_filter('truncate_title')
def truncate_title(title, length=80):
    """Truncate long titles"""
    if len(title) > length:
        return title[:length] + "..."
    return title

def scrape_platform_async(platform, query, pages, session_id):
    """Async scraping function with progress tracking"""
    global scraping_progress
    
    scraping_progress[session_id] = {
        'platform': platform,
        'status': 'in_progress',
        'current_page': 0,
        'total_pages': 0,
        'products_found': 0,
        'message': f'Starting {platform} scrape...'
    }
    
    try:
        if platform == 'amazon':
            scraper = AmazonConsoleScraper()
            products = scraper.search_products(query, pages, progress_callback=lambda p, t, c: update_progress(session_id, p, t, c))
        elif platform == 'daraz':
            scraper = DarazConsoleScraper()
            products = scraper.search_products(query, pages, progress_callback=lambda p, t, c: update_progress(session_id, p, t, c))
        else:
            products = []
        
        # Ensure currency is set
        for p in products:
            p['currency'] = 'USD' if platform == 'amazon' else 'PKR'
        
        scraping_progress[session_id]['status'] = 'completed'
        scraping_progress[session_id]['products_found'] = len(products)
        scraping_progress[session_id]['message'] = f'Completed! Found {len(products)} products'
        
        return products
        
    except Exception as e:
        scraping_progress[session_id]['status'] = 'error'
        scraping_progress[session_id]['message'] = f'Error: {str(e)}'
        return []

def update_progress(session_id, page, total, count):
    """Update scraping progress"""
    global scraping_progress
    if session_id in scraping_progress:
        scraping_progress[session_id]['current_page'] = page
        scraping_progress[session_id]['total_pages'] = total
        scraping_progress[session_id]['products_found'] = count
        scraping_progress[session_id]['message'] = f'Scraping page {page}... Found {count} products so far'

def scrape_platform(platform, query, pages=None):
    """Scrape products from specified platform (unlimited pages if pages=None)"""
    if platform == 'amazon':
        scraper = AmazonConsoleScraper()
        products = scraper.search_products(query, pages)
        # Ensure currency is set
        for p in products:
            p['currency'] = 'USD'
        return products
    elif platform == 'daraz':
        scraper = DarazConsoleScraper()
        products = scraper.search_products(query, pages)
        # Ensure currency is set
        for p in products:
            p['currency'] = 'PKR'
        return products
    return []

@app.route('/')
def index():
    """Home page with search form"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search request and return results (unlimited products)"""
    query = request.form.get('query', '').strip()
    platforms = request.form.getlist('platforms')
    pages_input = request.form.get('pages', 'all')
    
    if not query:
        return jsonify({'error': 'Please enter a search term'}), 400
    
    if not platforms:
        platforms = ['amazon', 'daraz']
    
    # Handle pages parameter
    if pages_input.lower() == 'all' or pages_input == '':
        pages = None  # Scrape all pages
    else:
        try:
            pages = int(pages_input)
        except:
            pages = None
    
    results = {}
    total_products = 0
    
    # Scrape from selected platforms
    for platform in platforms:
        if platform in ['amazon', 'daraz']:
            print(f"\n{'='*50}")
            print(f"Starting {platform} scrape for: '{query}'")
            print(f"{'='*50}")
            
            start_time = time.time()
            products = scrape_platform(platform, query, pages)
            elapsed_time = time.time() - start_time
            
            results[platform] = products
            total_products += len(products)
            
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            
            print(f"\n✅ Completed {platform}: {len(products)} products in {minutes}m {seconds}s")
    
    # Store results in session
    session['last_query'] = query
    session['last_results'] = results
    session['total_products'] = {
        'amazon': len(results.get('amazon', [])),
        'daraz': len(results.get('daraz', []))
    }
    session['scrape_time'] = {
        'amazon': f"{int((time.time() - start_time)//60)}m {int((time.time() - start_time)%60)}s" if platforms else "0s",
        'daraz': f"{int((time.time() - start_time)//60)}m {int((time.time() - start_time)%60)}s" if platforms else "0s"
    }
    
    return render_template('compare.html', 
                         query=query,
                         amazon_results=results.get('amazon', []),
                         daraz_results=results.get('daraz', []),
                         total_amazon=len(results.get('amazon', [])),
                         total_daraz=len(results.get('daraz', [])),
                         total_products=total_products,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/search', methods=['POST'])
def api_search():
    """JSON API endpoint for search (unlimited products)"""
    data = request.get_json()
    query = data.get('query', '').strip()
    platforms = data.get('platforms', ['amazon', 'daraz'])
    pages = data.get('pages', None)  # None means all pages
    
    if not query:
        return jsonify({'error': 'Please enter a search term'}), 400
    
    results = {}
    total_products = 0
    
    for platform in platforms:
        if platform in ['amazon', 'daraz']:
            products = scrape_platform(platform, query, pages)
            results[platform] = products
            total_products += len(products)
    
    return jsonify({
        'query': query,
        'results': results,
        'total_products': total_products,
        'platform_counts': {
            'amazon': len(results.get('amazon', [])),
            'daraz': len(results.get('daraz', []))
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/search/async', methods=['POST'])
def api_search_async():
    """Async JSON API endpoint for large searches"""
    data = request.get_json()
    query = data.get('query', '').strip()
    platforms = data.get('platforms', ['amazon', 'daraz'])
    pages = data.get('pages', None)
    
    if not query:
        return jsonify({'error': 'Please enter a search term'}), 400
    
    # Generate unique session ID
    session_id = f"{query}_{datetime.now().timestamp()}"
    
    # Start scraping in background thread
    def scrape_all():
        results = {}
        for platform in platforms:
            if platform in ['amazon', 'daraz']:
                products = scrape_platform_async(platform, query, pages, f"{session_id}_{platform}")
                results[platform] = products
        # Store results somewhere (database, file, etc.)
        
    thread = threading.Thread(target=scrape_all)
    thread.start()
    
    return jsonify({
        'session_id': session_id,
        'status': 'started',
        'message': 'Scraping started. Check progress using /api/progress/<session_id>',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Get scraping progress for async search"""
    global scraping_progress
    
    # Return progress for all platforms in this session
    platform_progress = {}
    for key, value in scraping_progress.items():
        if key.startswith(session_id):
            platform_progress[key.replace(f"{session_id}_", "")] = value
    
    if not platform_progress:
        return jsonify({'error': 'Session not found'}), 404
    
    all_completed = all(p['status'] in ['completed', 'error'] for p in platform_progress.values())
    
    return jsonify({
        'session_id': session_id,
        'all_completed': all_completed,
        'platforms': platform_progress,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/export/summary')
def export_summary():
    """Export summary statistics"""
    results = session.get('last_results', {})
    query = session.get('last_query', 'search')
    
    if not results:
        return jsonify({'error': 'No results to export'}), 404
    
    summary = {
        'query': query,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_products': 0,
        'platforms': {}
    }
    
    for platform, products in results.items():
        if not products:
            continue
            
        # Calculate statistics
        prices = [p.get('price_numeric', 0) for p in products if p.get('price_numeric', 0) > 0]
        ratings = [p.get('rating_numeric', 0) for p in products if p.get('rating_numeric', 0) > 0]
        sponsored = sum(1 for p in products if p.get('is_sponsored', False))
        
        summary['platforms'][platform] = {
            'count': len(products),
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'min_price': min(prices) if prices else 0,
            'max_price': max(prices) if prices else 0,
            'avg_rating': sum(ratings) / len(ratings) if ratings else 0,
            'sponsored_count': sponsored,
            'sponsored_percentage': (sponsored / len(products) * 100) if products else 0
        }
        
        summary['total_products'] += len(products)
    
    return jsonify(summary)

@app.route('/compare')
def compare():
    """Redirect to index if no results"""
    if 'last_results' not in session:
        return render_template('index.html', error='No previous search results found')
    
    results = session.get('last_results', {})
    query = session.get('last_query', '')
    
    return render_template('compare.html',
                         query=query,
                         amazon_results=results.get('amazon', []),
                         daraz_results=results.get('daraz', []),
                         total_amazon=len(results.get('amazon', [])),
                         total_daraz=len(results.get('daraz', [])),
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/compare/<platform1>/<platform2>/<product_id>')
def compare_products(platform1, platform2, product_id):
    """Compare specific products"""
    results = session.get('last_results', {})
    
    product1 = None
    product2 = None
    
    # Find the products in the results
    if platform1 in results:
        for p in results[platform1]:
            if p.get('asin') == product_id or p.get('id') == product_id:
                product1 = p
                break
    
    if platform2 in results:
        for p in results[platform2]:
            if p.get('asin') == product_id or p.get('id') == product_id:
                product2 = p
                break
    
    return render_template('compare_detail.html',
                         platform1=platform1,
                         platform2=platform2,
                         product1=product1,
                         product2=product2,
                         product_id=product_id,
                         timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/clear')
def clear_session():
    """Clear session data"""
    session.clear()
    return render_template('index.html', message='Session cleared successfully')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(413)
def too_large_error(error):
    return jsonify({'error': 'Request entity too large'}), 413

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Product Comparison App Starting...")
    print("=" * 60)
    print(f"📊 Mode: {'Debug' if Config.DEBUG else 'Production'}")
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔌 Port: 5000")
    print(f"📈 Unlimited Scraping: ENABLED")
    print(f"💾 Session Secret Key: {'Configured' if app.secret_key else '⚠️ NOT SET'}")
    print("=" * 60)
    print("\n📝 Available Routes:")
    print("   GET  /                    - Home page")
    print("   POST /search              - Search products")
    print("   GET  /compare              - View last results")
    print("   POST /api/search           - JSON API search")
    print("   POST /api/search/async     - Async JSON API")
    print("   GET  /api/progress/<id>    - Check async progress")
    print("   GET  /export/<format>      - Export results (json/csv)")
    print("   GET  /export/summary        - Export summary stats")
    print("   GET  /clear                 - Clear session")
    print("   GET  /health                - Health check")
    print("=" * 60)
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)