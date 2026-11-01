from flask import Flask, render_template, send_from_directory
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from flask import Flask, Response, url_for
import sys
import os
import re
import unicodedata
sys.path.append(os.path.join(os.path.dirname(__file__), 'static/konfigurasi'))

from config_web2 import web_control, status_page, whatsapp_channel, whattsapp_admin, url_order
app = Flask(__name__)

#------ SISITEM ARTICLE ------#
# Path to article templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

ARTICLE_DIR = os.path.join(TEMPLATE_DIR, "Main-Article")

def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def get_articles():
    articles = {}

    if not os.path.exists(ARTICLE_DIR):
        print("[ERROR] Folder tidak ditemukan:", ARTICLE_DIR)
        return articles

    for file in os.listdir(ARTICLE_DIR):
        if not file.endswith(".html"):
            continue

        old_slug = file[:-5]
        file_path = os.path.join(ARTICLE_DIR, file)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception as e:
            print("[ERROR] Gagal baca:", file_path, e)
            continue

        title = (
            soup.title.get_text(strip=True)
            if soup.title else old_slug.replace("-", " ").title()
        )

        description_tag = soup.find(
            "meta", attrs={"name": "description"}
        )
        description = (
            description_tag.get("content", "")
            if description_tag else "No description available."
        )

        category_tag = soup.find(
            "meta", attrs={"name": "category"}
        )
        categories = (
            category_tag.get("content", "").lower()
            if category_tag else "general"
        )

        date_tag = soup.find("meta", attrs={"name": "date"})
        if date_tag:
            try:
                date = datetime.strptime(
                    date_tag["content"], "%Y-%m-%d"
                )
            except (ValueError, KeyError):
                date = datetime.min
        else:
            date = datetime.min

        # Gunakan slug khusus jika tersedia
        slug_tag = soup.find("meta", attrs={"name": "slug"})

        if slug_tag and slug_tag.get("content"):
            new_slug = slugify(slug_tag["content"])
        else:
            new_slug = slugify(title)

        if not new_slug:
            new_slug = slugify(old_slug)

        if not new_slug:
            print("[ERROR] Slug kosong:", file)
            continue

        if new_slug in articles:
            print("[ERROR] Slug duplikat:", new_slug)
            continue

        articles[new_slug] = {
            "file": file,
            "old_slug": old_slug,
            "slug": new_slug,
            "title": title.strip(),
            "description": description.strip(),
            "categories": categories.strip(),
            "date": date
        }

    return dict(
        sorted(
            articles.items(),
            key=lambda x: x[1]["date"],
            reverse=True
        )
    )

# Route untuk landing page (index)
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('.', 'robots.txt')
    
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    pages = [
        {'loc': 'https://kocheng.biz.id/', 'priority': '1.0'},
        {'loc': 'https://kocheng.biz.id/privacypolicy', 'priority': '0.8'},
        {'loc': 'https://kocheng.biz.id/tos', 'priority': '0.8'},
        {'loc': 'https://kocheng.biz.id/advertisingagreement', 'priority': '0.7'},
        {'loc': 'https://kocheng.biz.id/blog', 'priority': '0.6'},
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
    
@app.route("/about")
def aboutus():
	
    return render_template("Main-Page/aboutus.html")
    
@app.route("/contact")
def contact():
	
    return render_template("Main-Page/contact.html")

@app.route("/blog/<slug>")
def blog_article(slug):

    articles = get_articles()

    # Cari berdasarkan slug baru
    article = articles.get(slug)

    if not article:
        # Cari URL lama berdasarkan nama file
        for new_slug, item in articles.items():
            if item["old_slug"] == slug:
                return redirect(
                    url_for("blog_article", slug=new_slug),
                    code=301
                )

        abort(404)

    # Jika memakai URL lama, arahkan ke URL baru
    if slug != article["slug"]:
        return redirect(
            url_for("blog_article", slug=article["slug"]),
            code=301
        )

    return render_template(
        f"Main-Article/{article['file']}",
        article=article
    )