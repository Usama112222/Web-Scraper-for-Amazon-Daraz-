import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # REMOVED: MAX_PRODUCTS = 10
    DEBUG = True
    TESTING = False
    
    # Exchange rate for approximate conversion
    PKR_TO_USD_RATE = 280
    
    # Platform settings
    AMAZON_DOMAIN = 'https://www.amazon.com'
    DARAZ_DOMAIN = 'https://www.daraz.pk'
    
    # Request settings
    REQUEST_TIMEOUT = 30
    MIN_DELAY = 2  # Minimum delay between requests
    MAX_DELAY = 5  # Maximum delay between requests
    
    # Performance settings for large scrapes
    CHUNK_SIZE = 100  # Process products in chunks
    MAX_RETRIES = 3    # Retry failed requests