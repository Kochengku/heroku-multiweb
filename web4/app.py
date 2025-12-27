from flask import Flask, render_template, send_from_directory
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from flask import Flask, Response, url_for
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'static/konfigurasi'))

from config_web4 import web_control, status_page, whatsapp_channel, whattsapp_admin, url_order
app = Flask(__name__)

#------ SISITEM ARTICLE ------#
# Path to article templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

ARTICLE_DIR = os.path.join(TEMPLATE_DIR, "Main-Article")

def get_articles():
    articles = {}

    if not os.path.exists(ARTICLE_DIR):
        print("[ERROR] Folder tidak ditemukan:", ARTICLE_DIR)
        return articles

    for file in os.listdir(ARTICLE_DIR):
        if file.endswith(".html"):
            slug = file.replace(".html", "")
            file_path = os.path.join(ARTICLE_DIR, file)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f, "html.parser")
            except Exception as e:
                print("[ERROR] Gagal baca:", file_path, e)
                continue

            title = soup.title.string if soup.title else slug.replace("-", " ").title()

            description_tag = soup.find("meta", attrs={"name": "description"})
            description = description_tag["content"] if description_tag else "No description available."

            category_tag = soup.find("meta", attrs={"name": "category"})
            categories = category_tag["content"].lower() if category_tag else "general"

            date_tag = soup.find("meta", attrs={"name": "date"})
            if date_tag:
                try:
                    date = datetime.strptime(date_tag["content"], "%Y-%m-%d")
                except ValueError:
                    date = datetime.min
            else:
                date = datetime.min

            articles[slug] = {
                "file": file,
                "title": title.strip(),
                "description": description.strip(),
                "categories": categories.strip(),
                "date": date
            }

    return dict(sorted(articles.items(), key=lambda x: x[1]["date"], reverse=True))

# Route untuk landing page (index)
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('.', 'robots.txt')
    
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    pages = [
        {'loc': 'https://skyforgia.web.id/', 'priority': '1.0'},
        {'loc': 'https://skyforgia.web.id/privacypolicy', 'priority': '0.8'},
        {'loc': 'https://skyforgia.web.id/tos', 'priority': '0.8'},
        {'loc': 'https://skyforgia.web.id/advertisingagreement', 'priority': '0.7'},
        {'loc': 'https://skyforgia.web.id/blog', 'priority': '0.6'},
    ]

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{page["loc"]}</loc>')
        xml.append(f'    <lastmod>{datetime.utcnow().date()}</lastmod>')
        xml.append(f'    <changefreq>weekly</changefreq>')
        xml.append(f'    <priority>{page["priority"]}</priority>')
        xml.append('  </url>')

    xml.append('</urlset>')
    sitemap_xml = '\n'.join(xml)
    return Response(sitemap_xml, mimetype='application/xml')
    
@app.route("/")
def home():
    return render_template("landing-page.html", web_control=web_control, status_page=status_page, whatsapp_channel=whatsapp_channel, whattsapp_admin=whattsapp_admin, url_order=url_order)
    
@app.route("/getstarted")
def home_two():
    return render_template("landing-page.html", web_control=web_control, status_page=status_page, whatsapp_channel=whatsapp_channel, whattsapp_admin=whattsapp_admin, url_order=url_order)
    
#------ ARTICLE AREA ------#
@app.route("/blog")
def blog():
    articles = get_articles()
    
    return render_template("Main-Page/blog.html", articles=articles)
    
@app.route("/privacypolicy")
def privacy():
	  
    return render_template("Main-Page/privacy.html")
    
@app.route("/tos")
def tos():
	
    return render_template("Main-Page/tos.html")
    
@app.route("/advertisingagreement")
def advertisingagreement():
	
    return render_template("Main-Page/ads.html")

@app.route("/blog/<slug>")
def blog_article(slug):
	
    articles = get_articles()
    article = articles.get(slug)
    if not article:
        abort(404)

    file_path = os.path.join(ARTICLE_DIR, article["file"])

    # Cek isi file biar tidak error decode
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            f.read()
    except Exception:
        return "File artikel rusak atau tidak bisa dibaca", 500

    # Render aman
    return render_template(f"Main-Article/{article['file']}", article=article)