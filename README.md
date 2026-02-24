🛒 Amazon & Daraz Product Comparison Scraper

A powerful Flask-based web application that scrapes and compares products from Amazon (USD) and Daraz (PKR) in real-time.

This tool allows users to search for any product keyword and instantly compare:

💰 Prices

⭐ Ratings

📦 Sponsored listings

📊 Summary statistics

🔄 Cross-platform product comparison

🚀 Features
🔎 Multi-Platform Scraping

Scrapes products from:

Amazon (USD)

Daraz (PKR)

Supports unlimited page scraping

Optional page limit input

📊 Product Comparison

Compare products across both platforms

View detailed product comparisons

Currency-aware price formatting

⚡ Async Scraping (For Large Searches)

Background scraping using threading

Live progress tracking API

Session-based progress monitoring

📤 Export Options

Export summary statistics (JSON)

View average price, min/max price

Sponsored product percentage

🌐 REST API Support

/api/search – JSON product search

/api/search/async – Async scraping

/api/progress/<id> – Track scraping progress

🏗️ Built With

Python 3

Flask

Pandas

Threading

Custom Web Scrapers

📂 Project Structure
project/
│── app.py
│── scrapers/
│── templates/
│── static/
│── config.py
│── requirements.txt
│── .gitignore
⚙️ Installation
1️⃣ Clone the repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
2️⃣ Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
3️⃣ Install dependencies
pip install -r requirements.txt
4️⃣ Run the app
python app.py

Open in browser:

http://127.0.0.1:5000
📌 Available Routes
Method	Route	Description
GET	/	Home page
POST	/search	Search products
GET	/compare	View last results
POST	/api/search	JSON API search
POST	/api/search/async	Async search
GET	/api/progress/<id>	Track progress
GET	/export/summary	Export summary stats
GET	/clear	Clear session
🔐 Configuration


⚠️ Disclaimer

This project is for educational purposes only.
Web scraping should comply with each platform's Terms of Service.