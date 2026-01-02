# FILE APP.PY
# DI BUAT 95% OLEH KECERDASAN BUATAN

from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify, Response, stream_with_context, send_from_directory
from flask_session import Session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from dateutil.parser import parse
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from random import randint
import random
import base64
from uuid import uuid4
import logging
import requests
import sqlite3
import string
import math
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
import zipfile
import subprocess
from bs4 import BeautifulSoup
from flask_wtf.csrf import generate_csrf
from flask import make_response
import logging, calendar
import pytz
from sqlalchemy import and_
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
from threading import Thread

import difflib
from sqlalchemy import or_
import uuid
from collections import defaultdict
from sqlalchemy import func
from flask_caching import Cache
from hashlib import sha256
import qrcode
import time
import io

from authlib.integrations.flask_client import OAuth
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'static/konfigurasi'))

from config_web1 import EMAIL_API_TOKEN, G_CLIENT_ID, G_CLIENT_SECRET, admin_mail, telegrambotlink, ouolink, whatsapp_number, whatsapp_channel, telegram_user, telegram_channel, FROM_NAME, FROM_EMAIL, ZEPTO_API_KEY, ZEPTO_API_URL, moderator_mail
from pterodactyl_web1 import create_user, create_server, get_all_nodes, hapus_user_tanpa_server, fetch_node_server_counts, get_all_servers, get_all_users, fetch_egg_list, delete_server, PANELS, get_client_headers, get_headers
from werkzeug.security import generate_password_hash, check_password_hash
os.environ["WERKZEUG_RUN_MAIN"] = "true"

db = SQLAlchemy()

app = Flask(__name__)
app.secret_key = "Kocheng"

raw_uri = os.getenv("DATABASE_URL")
if not raw_uri:
    raise RuntimeError("DATABASE_URL tidak ditemukan")

if raw_uri.startswith("postgres://"):
    raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)

app.config.update(
    SQLALCHEMY_DATABASE_URI=raw_uri,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        "pool_size": 3,
        "max_overflow": 2,
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
)

db.init_app(app)

DEFAULT_NODES = [
    {"id": 1, "name": "Node 1", "limit_server": 35},
    {"id": 2, "name": "Node 2", "limit_server": 35},
    {"id": 3, "name": "Node 3", "limit_server": 35},
    {"id": 4, "name": "Node 4", "limit_server": 35},
    {"id": 5, "name": "Node 5", "limit_server": 35},
    {"id": 6, "name": "Node 6", "limit_server": 35},
    {"id": 7, "name": "Node 7", "limit_server": 35},
    {"id": 8, "name": "Node 8", "limit_server": 35},
]

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    bio = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(128))

    is_verified = db.Column(db.Boolean, default=False)
    login_google = db.Column(db.Boolean, default=False)

    photo_url = db.Column(db.String(255))
    photo_google = db.Column(db.String(255))

    server = db.Column(db.Integer, default=0)
    cpu = db.Column(db.Integer, default=0)
    ram = db.Column(db.Integer, default=0)
    disk = db.Column(db.Integer, default=0)

    coin = db.Column(db.Integer, default=0)
    special_ram_last_used = db.Column(db.DateTime)
    trialramused = db.Column(db.Integer, default=0)

    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    last_boost = db.Column(db.DateTime)
    last_boost_used = db.Column(db.DateTime)

    ram_upgrade_start = db.Column(db.DateTime)
    ram_upgrade_end = db.Column(db.DateTime)

    harian_coin = db.Column(db.Integer, default=0)
    harian_coin_tanggal = db.Column(db.Date)

    token = db.Column(db.String(64), unique=True)
    timestamp = db.Column(db.Integer)

    iklan = db.Column(db.Integer, default=0)
    iklan_expiry = db.Column(db.DateTime)

    boostserver = db.Column(db.Integer, default=0)

    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20))

    milestone_3 = db.Column(db.Boolean, default=False)
    milestone_5 = db.Column(db.Boolean, default=False)
    milestone_10 = db.Column(db.Boolean, default=False)
    milestone_15 = db.Column(db.Boolean, default=False)
    milestone_20 = db.Column(db.Boolean, default=False)
    milestone_25 = db.Column(db.Boolean, default=False)
    milestone_30 = db.Column(db.Boolean, default=False)

    device_id = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    daily_claim_day = db.Column(db.Integer, default=0)
    daily_claim_last = db.Column(db.Date)

    afk_total_coin_bulanan = db.Column(db.Integer, default=0)
    afk_bonus_bulan = db.Column(db.String(7))
    afk_bonus_50 = db.Column(db.Boolean, default=False)
    afk_bonus_100 = db.Column(db.Boolean, default=False)
    afk_bonus_200 = db.Column(db.Boolean, default=False)

    created_server_before = db.Column(db.Boolean, default=False)
    create_mission_rewarded = db.Column(db.Boolean, default=False)

    is_moderator = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)

    is_backup_mega = db.Column(db.Boolean, default=False)
    auto_backup_enabled = db.Column(db.Boolean, default=False)

    last_backup = db.Column(db.DateTime)
    next_backup = db.Column(db.DateTime)
    last_filename = db.Column(db.String(255))

    serverid = db.Column(db.String(50))
    mega_link = db.Column(db.Text)
    
class ServerSpec(db.Model):
    __tablename__ = "server_spec"

    id = db.Column(db.String, primary_key=True)
    ram = db.Column(db.Integer, default=1024)
    cpu = db.Column(db.Integer, default=80)
    disk = db.Column(db.Integer, default=5024)


class Node(db.Model):
    __tablename__ = "node"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    limit_server = db.Column(db.Integer, default=35)


class Server(db.Model):
    __tablename__ = "server"

    id = db.Column(db.Integer, primary_key=True)
    serverid = db.Column(db.String(50))
    name = db.Column(db.String(100), nullable=False)
    uuid = db.Column(db.String(36), unique=True, nullable=False)

    user_id = db.Column(db.Integer, nullable=False)

    server = db.Column(db.Integer, default=0)
    cpu = db.Column(db.Integer, default=0)
    ram = db.Column(db.Integer, default=0)
    disk = db.Column(db.Integer, default=0)

    allocation_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class Ticket(db.Model):
    __tablename__ = "ticket"

    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_notified_admin = db.Column(db.Boolean, default=False)

    replies = db.relationship(
        "Reply",
        backref="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Reply(db.Model):
    __tablename__ = "reply"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id", ondelete="CASCADE"))
    sender = db.Column(db.String(50))
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_notified_user = db.Column(db.Boolean, default=False)
    is_notified_admin = db.Column(db.Boolean, default=False)

    images = db.relationship(
        "ReplyImage",
        backref="reply",
        cascade="all, delete-orphan"
    )


class ReplyImage(db.Model):
    __tablename__ = "reply_image"

    id = db.Column(db.Integer, primary_key=True)
    reply_id = db.Column(db.Integer, db.ForeignKey("reply.id"), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    
class ReferralActivity(db.Model):
    __tablename__ = "referral_activity"

    id = db.Column(db.Integer, primary_key=True)
    inviter_id = db.Column(db.Integer)
    invited_id = db.Column(db.Integer)
    action = db.Column(db.String(50))
    reward = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSetting(db.Model):
    __tablename__ = "site_setting"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    @staticmethod
    def get(key, default=None):
        s = SiteSetting.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value):
        s = SiteSetting.query.filter_by(key=key).first()
        if s:
            s.value = str(value)
        else:
            db.session.add(SiteSetting(key=key, value=str(value)))
        db.session.commit()
    
update_queue = []
update_logs = []
update_status = "idle"

#------ ERROR PAGE ------#
@app.errorhandler(404)
def not_found_error(error):
    return render_template("Main-Page/error-page.html"), 404

# Error 500: Server error
@app.errorhandler(500)
def internal_error(error):
    return render_template("Main-Page/error-page.html"), 500

def add_log(msg: str):
    from datetime import datetime
    global update_logs
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    update_logs.append(line)
    if len(update_logs) > 200:
        update_logs.pop(0)
    print(line)
    
def init_nodes():
    if Node.query.count() == 0:
        for n in DEFAULT_NODES:
            node = Node(id=n["id"], name=n["name"], limit_server=n["limit_server"])
            db.session.add(node)
        db.session.commit()
        print("Node default berhasil ditambahkan!")
        
def init_server_spec():
    for panel_id in PANELS.keys():
        existing = ServerSpec.query.get(panel_id)
        if not existing:
            default_server = ServerSpec(
                id=panel_id,   # <-- ID diambil dari key dict
                ram=1024,
                cpu=80,
                disk=5024
            )
            db.session.add(default_server)
            print(f"[INIT] ServerSpec untuk {panel_id} berhasil ditambahkan")
        else:
            print(f"[INIT] ServerSpec untuk {panel_id} sudah ada, dilewati")

    db.session.commit()
        
with app.app_context():
    db.create_all()
    init_nodes()
    init_server_spec()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Konfigurasi cek maintenance 
def check_maintenance():
    maintenance_mode = SiteSetting.get("maintenance_mode", "false") == "true"

    user_id = session.get("user_id")
    user = User.query.get(user_id) if user_id else None

    if maintenance_mode:
        if not user or user.email != admin_mail:
            return redirect(url_for("dashboard_maintenance"))
    return None
            
# Konfigurasi auto lock dashboard 
LOCAL_TZ = pytz.timezone("Asia/Jakarta")

def calculate_dashboard_lock():
    manual_lock = SiteSetting.get("lock_dashboard", "false") == "true"
    force_unlock = SiteSetting.get("force_unlock_dashboard", "false") == "true"
    disable_auto_lock = SiteSetting.get("disable_auto_lock", "false") == "true"

    now_local = datetime.now(LOCAL_TZ)

    days_in_month = calendar.monthrange(now_local.year, now_local.month)[1]
    last_day = datetime(now_local.year, now_local.month, days_in_month, tzinfo=LOCAL_TZ)

    mid_lock = datetime(now_local.year, now_local.month, 14, tzinfo=LOCAL_TZ)
    mid_unlock = datetime(now_local.year, now_local.month, 15, tzinfo=LOCAL_TZ)
    lock_before_end = last_day - timedelta(days=1)

    # =========================
    # AUTO LOCK
    # =========================
    auto_locked = False
    if not disable_auto_lock:
        if mid_lock.date() <= now_local.date() < mid_unlock.date():
            auto_locked = True
        elif now_local.date() >= lock_before_end.date():
            auto_locked = True

    # =========================
    # FINAL LOCK LOGIC (FIX)
    # =========================
    if force_unlock:
        locked = False
    elif manual_lock:
        locked = True
    else:
        locked = auto_locked

    # =========================
    # COUNTDOWN (AUTO ONLY)
    # =========================
    if auto_locked:
        if mid_lock.date() <= now_local.date() < mid_unlock.date():
            reset_date = mid_unlock
        else:
            reset_date = (
                datetime(now_local.year + 1, 1, 1, tzinfo=LOCAL_TZ)
                if now_local.month == 12
                else datetime(now_local.year, now_local.month + 1, 1, tzinfo=LOCAL_TZ)
            )
    else:
        reset_date = mid_lock if now_local.day < 14 else lock_before_end

    countdown_seconds = max(0, int((reset_date - now_local).total_seconds()))
    countdown_days = countdown_seconds // 86400

    return locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds
    
# Konfigurasi send notifikasi sebelum lock
def send_batch_email(email_list):
    if not email_list:
        print("⚠️ Tidak ada email untuk dikirim.")
        return

    html_body = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Platform Reset Notification</title>
  </head>
  <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:600px;margin:30px auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
      <div style="text-align:center;padding:20px;border-bottom:1px solid #e5e7eb;">
        <img src="https://kocheng.biz.id/static/logo.webp" alt="Kocheng Logo" style="height:120px;">
      </div>

      <div style="padding:30px;color:#111827;">
        <h2 style="margin-top:0;font-size:20px;color:#0b5fff;">⚠️ Upcoming Platform Reset</h2>
        <p style="margin:0 0 15px;font-size:15px;color:#374151;">
          This is an important notice to inform you that <strong>our platform will undergo a scheduled reset soon</strong>.
          All servers, user data, and related content will be permanently cleared as part of this reset.
        </p>
        <p style="margin:0 0 20px;font-size:15px;color:#374151;">
          To avoid data loss, we highly recommend that you <strong>back up your scripts and important files in advance</strong>.
        </p>

        <div style="text-align:center;margin:30px 0;">
          <a href="https://control.kocheng.biz.id/panel/backup" target="_blank" 
            style="display:inline-block;background-color:#0b5fff;color:#ffffff;text-decoration:none;padding:14px 26px;font-size:15px;font-weight:bold;border-radius:6px;">
            Go to Backup Panel
          </a>
        </div>

        <p style="margin:0;font-size:14px;color:#6b7280;">
          If you have any questions or need assistance with backups, feel free to contact our support team.
        </p>
      </div>

      <footer style="background:#ffffff;border-top:1px solid #e5e7eb;padding:16px;font-size:12px;text-align:center;color:#6b7280;line-height:1.5;">
        <p style="margin:4px 0;font-weight:600;color:#374151;">Kocheng's |> Sahabat Ai Nusantara</p>
        <p style="margin:4px 0;">
          <a href="https://kocheng.biz.id/privacypolicy" style="color:#2563eb;text-decoration:none;">Privacy Policy</a> | 
          <a href="https://kocheng.biz.id/tos" style="color:#2563eb;text-decoration:none;">Terms of Service</a> | 
          <a href="https://kocheng.biz.id/advertisingagreement" style="color:#2563eb;text-decoration:none;">Ads Disclosure</a> | 
          <a href="https://kocheng.biz.id/blog" style="color:#2563eb;text-decoration:none;">Blog</a>
        </p>
        <p style="margin:4px 0;">JL. Anggrek Klagenserut, Jiwan Kabupaten Madiun (6311).</p>
        <p style="margin:4px 0;">📧 supporthosting@kocheng.tech</p>
      </footer>
    </div>
  </body>
</html>
"""

    # Konversi daftar email ke format ZeptoMail
    recipients = [{"email_address": {"address": email}} for email in email_list]

    payload = {
        "from": {"address": FROM_EMAIL, "name": FROM_NAME},
        "to": recipients,
        "subject": "⚠️ Platform Reset Notice",
        "htmlbody": html_body,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": ZEPTO_API_KEY,
    }

    try:
        response = requests.post(ZEPTO_API_URL, headers=headers, data=json.dumps(payload))

        if response.status_code in [200, 201]:
            print(f"✅ Email berhasil dikirim ke {len(email_list)} penerima.")
        else:
            print(f"❌ Gagal kirim email. Status: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"⚠️ Terjadi kesalahan saat mengirim email: {e}")

def chunk_list(lst, chunk_size):
    """Bagi list menjadi beberapa bagian berukuran chunk_size."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]
        
def send_lock_email_to_eligible_users(lock_date):
    """
    Kirim email notifikasi ke semua user yang memenuhi kriteria (user.server == 1)
    menggunakan sistem batching agar tidak overload API Resend.
    """

    tanggal_lock_str = lock_date.strftime("%d %B %Y")

    # Ambil semua email user dengan server == 1
    users = User.query.filter(and_(User.server == 1, User.email != None)).all()
    all_emails = [u.email for u in users if u.email]

    # Kirim dalam batch (misal 50 email per batch)
    BATCH_SIZE = 50
    for batch_emails in chunk_list(all_emails, BATCH_SIZE):
        send_batch_email(batch_emails)
        time.sleep(2)  # jeda antar batch

    print(f"[BROADCAST] Total {len(all_emails)} email terkirim untuk lock {tanggal_lock_str}.")
        
def broadcast_lock_notification():
    """
    Kirim email 3 hari sebelum:
    - Lock tengah bulan (tanggal 14)
    - Lock akhir bulan (H-1 dari akhir bulan)
    """
    today = datetime.now(LOCAL_TZ).date()

    # =========================
    # 1. Lock tengah bulan (14)
    # =========================
    mid_lock_date = datetime(today.year, today.month, 14, tzinfo=LOCAL_TZ).date()
    mid_notify_date = mid_lock_date - timedelta(days=3)
    if today == mid_notify_date:
        send_lock_email_to_eligible_users(mid_lock_date)

    # =========================
    # 2. Lock akhir bulan (H-1)
    # =========================
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    last_day = datetime(today.year, today.month, days_in_month, tzinfo=LOCAL_TZ).date()
    end_lock_date = last_day - timedelta(days=1)
    end_notify_date = end_lock_date - timedelta(days=3)
    if today == end_notify_date:
        send_lock_email_to_eligible_users(end_lock_date)

# Konfigurasi get device & ip
def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"

def get_or_create_device_id(resp):
    device_id = request.cookies.get("device_id")
    if not device_id:
        device_id = str(uuid.uuid4())
        resp.set_cookie(
            "device_id",
            device_id,
            max_age=60*60*24*365,  # 1 tahun
            httponly=True,
            samesite="Lax"
        )
    return device_id

# Konfigurasi ambil server tidak aktif  & hapus server 
# Konfigurasi cache
_node_cache = {}
_node_cache_time = {}
CACHE_TTL = 86400
jumlahrender = 20

def get_node_data_cached(panel_id, force_refresh=False):
    global _node_cache, _node_cache_time

    now = time.time()
    if (not force_refresh
        and panel_id in _node_cache
        and (now - _node_cache_time.get(panel_id, 0) < CACHE_TTL)):
        return _node_cache[panel_id]

    print(f"[CACHE] Refreshing node data for {panel_id} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Ambil ringkasan server tidak aktif
    _, inactive_summary = get_server_tidak_aktif(
        panel_id=panel_id,
        threshold_days=7,
        max_to_check=jumlahrender
    )

    totals = {}
    try:
        servers = get_all_servers(panel_id)  # fungsi existing tapi harus pakai panel_id
        for srv in servers:
            node_id = str(srv["attributes"]["node"])
            totals[node_id] = totals.get(node_id, 0) + 1
    except Exception as e:
        print(f"[ERROR] Gagal ambil total server ({panel_id}):", e)

    node_data = []
    for node_id, total in totals.items():
        inactive_info = inactive_summary.get(node_id, {})
        node_data.append({
            "id": int(node_id),
            "name": inactive_info.get("name", f"Node {node_id}"),
            "total": total,
            "inactive": inactive_info.get("inactive", 0)
        })

    for node_id, data in inactive_summary.items():
        if node_id not in totals:
            node_data.append({
                "id": int(node_id),
                "name": data["name"],
                "total": 0,
                "inactive": data["inactive"]
            })

    _node_cache[panel_id] = node_data
    _node_cache_time[panel_id] = now
    return node_data
    
headers_client = {
    "Authorization": f"Bearer ptlc_J4J5V9bM9eYe8bVNndNw9h59VsZkk2wgSdOuZz4vFkN",
    "Accept": "application/json"
}

def delete_pterodactyl_server(user):
    if not user.serverid:
        return False, "User tidak punya serverid."

    panel_id = str(user.serverid)
    panel = PANELS.get(panel_id)

    if not panel:
        return False, "Panel tidak ditemukan pada konfigurasi."

    # Ambil URL dan API key panel
    panel_url = panel["url"]
    api_key = panel["api_key"]

    # Ambil server spec dari database
    server = ServerSpec.query.filter_by(id=panel_id).first()
    if not server:
        return False, "ServerSpec tidak ditemukan."

    ptero_server_id = server.id  # ID server Pterodactyl

    # URL API DELETE server
    delete_url = f"{panel_url}/api/application/servers/{ptero_server_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    try:
        response = requests.delete(delete_url, headers=headers, timeout=10)

        if response.status_code in (200, 204):
            return True, "Server berhasil dihapus."
        else:
            return False, f"Gagal menghapus server: {response.text}"

    except Exception as e:
        return False, f"Error koneksi: {str(e)}"

def update_server_build(panel_id: str, server_id: int, allocation: int, ram: int, disk: int, cpu: int):
    """Update spesifikasi server Pterodactyl sesuai panel"""
    panel = PANELS[panel_id]
    url = f"{panel['url']}/api/application/servers/{server_id}/build"
    payload = {
        "allocation": allocation,
        "memory": ram,
        "swap": 0,
        "disk": disk,
        "io": 500,
        "cpu": cpu,
        "threads": None,
        "feature_limits": {"databases": 5, "allocations": 5, "backups": 5}
    }
    r = requests.patch(url, headers=get_headers(panel_id), json=payload)
    return r.status_code == 200

def enqueue_spec_update(panel_id: str, ram: int, disk: int, cpu: int):
    """
    Masukkan semua server dari panel_id ke dalam queue.
    Diproses bertahap oleh scheduler (10 per menit).
    """
    global update_queue, update_status
    update_queue.clear()
    update_status = "running"
    add_log(f"🚀 Mulai enqueue server untuk update spesifikasi di {panel_id}...")

    panel = PANELS[panel_id]
    url = f"{panel['url']}/api/application/servers"
    page = 1

    while True:
        r = requests.get(f"{url}?page={page}", headers=get_headers(panel_id))
        if r.status_code != 200:
            add_log(f"❌ Gagal mengambil data server dari panel {panel_id}")
            break

        data = r.json()
        for s in data["data"]:
            attrs = s["attributes"]
            server_id = attrs["id"]          # numeric id
            server_uuid = attrs["uuid"]      # uuid string
            node_id = attrs["node"]
            allocation = attrs["allocation"]

            # Gunakan UUID, bukan numeric id
            server_db = Server.query.filter_by(uuid=server_uuid).first()
            if not server_db:
                add_log(f"⚠️ Server {server_uuid} tidak ditemukan di db")
                continue

            user = User.query.filter_by(id=server_db.user_id).first()
            if not user:
                add_log(f"⚠️ User {server_db.user_id} tidak ditemukan")
                continue

            if user.ram_upgrade_start is not None or user.last_boost is not None:
                add_log(f"⏩ Skip server {server_uuid}, user {user.id} masih punya upgrade/boost aktif")
                continue

            update_queue.append({
                "panel_id": panel_id,
                "id": server_id,
                "uuid": server_uuid,
                "allocation": allocation,
                "ram": ram,
                "disk": disk,
                "cpu": cpu
            })

            # Update spec di db
            user.cpu = cpu
            user.ram = ram
            user.disk = disk
            db.session.commit()

        if data["meta"]["pagination"]["current_page"] >= data["meta"]["pagination"]["total_pages"]:
            break
        page += 1

    add_log(f"📌 Total {len(update_queue)} server masuk ke queue {panel_id} untuk diproses batch")
            
def get_server_status(panel_id, identifier):
    """Ambil status server dari API client (running/starting/offline)."""
    url = f"{PANELS[panel_id]['url']}/api/client/servers/{identifier}/resources"
    try:
        res = requests.get(url, headers=get_client_headers(panel_id), timeout=10)
        res.raise_for_status()
        return res.json()["attributes"]["current_state"]
    except requests.exceptions.RequestException as e:
        print(f"[ERROR][{panel_id}] get_server_status {identifier}: {e}")
        return None

def get_server_activity(panel_id, identifier, max_logs=10000):
    """Ambil riwayat aktivitas server (event logs) dari API client."""
    logs = []
    page = 1
    per_page = 50

    while len(logs) < max_logs:
        url = f"{PANELS[panel_id]['url']}/api/client/servers/{identifier}/activity?page={page}&per_page={per_page}"
        try:
            res = requests.get(url, headers=get_client_headers(panel_id), timeout=10)
            if res.status_code != 200:
                print(f"[ERROR {res.status_code}][{panel_id}] Server {identifier}")
                break
        except requests.exceptions.Timeout:
            print(f"[TIMEOUT][{panel_id}] Server {identifier}")
            break
        except requests.exceptions.RequestException as e:
            print(f"[ERROR][{panel_id}] Server {identifier}: {e}")
            break

        data = res.json().get("data", [])
        if not data:
            break

        logs.extend(data)
        if len(data) < per_page:
            break  # tidak ada halaman berikutnya

        page += 1

    return logs[:max_logs]

def get_server_tidak_aktif(panel_id, threshold_days=7, max_to_check=jumlahrender):
    threshold = datetime.now(timezone.utc) - timedelta(days=threshold_days)

    try:
        servers = get_all_servers(panel_id)
        users = get_all_users(panel_id)
        raw_nodes = get_all_nodes(panel_id)
    except Exception as e:
        print(f"[ERROR] Gagal ambil data panel {panel_id}:", e)
        return [], {}

    nodes = {str(k): v for k, v in raw_nodes.items()}
    user_map = {u["attributes"]["id"]: u["attributes"]["username"] for u in users}

    daftar = []
    node_summary = {}
    count = 0

    for srv in servers:
        try:
            attr = srv["attributes"]
            server_id = attr["id"]
            uuid = attr["uuid"]
            identifier = uuid[:8]
            server_name = attr["name"]
            user_id = attr["user"]
            node_id = str(attr["node"])

            node_name = nodes.get(node_id, f"Node {node_id}")
            username = user_map.get(user_id, f"User {user_id}")

            # Inisialisasi summary node
            if node_id not in node_summary:
                node_summary[node_id] = {
                    "name": node_name,
                    "total": 0,
                    "inactive": 0
                }
            node_summary[node_id]["total"] += 1

            # Cek status server
            status = get_server_status(panel_id, identifier)
            if status in ["running", "starting"]:
                continue  # skip server yang masih aktif

            # Cek aktivitas log
            logs = get_server_activity(panel_id, identifier)
            print(f"[DEBUG][{panel_id}] server_name='{server_name}' logs count={len(logs)}")

            if not logs:
                updated_at = "-"
            else:
                logs.sort(key=lambda l: l["attributes"]["timestamp"], reverse=True)
                last_time = parse(logs[0]["attributes"]["timestamp"])
                updated_at = last_time.strftime("%d %B %Y %H:%M:%S")

                if last_time >= threshold:
                    print(f"[DEBUG][{panel_id}]   >> {server_name} masih aktif dalam {threshold_days} hari terakhir, skip")
                    continue

            # Tambahkan ke daftar tidak aktif
            daftar.append({
                "id": server_id,
                "uuid": identifier,
                "server_name": server_name,
                "username": username,
                "updated_at": updated_at,
                "node_ip": "-",
                "state": status,
                "node_id": node_id,
                "node_name": node_name
            })
            node_summary[node_id]["inactive"] += 1
            count += 1

            if count >= max_to_check:
                break

        except Exception as e:
            print(f"[ERROR PER SERVER][{panel_id}] {e}")
            continue

    # Sort dari yang terbaru
    daftar.sort(
        key=lambda s: parse(s['updated_at']) if s['updated_at'] != "-" else datetime.min,
        reverse=True
    )

    return daftar, node_summary
    
def hapus_server_tidak_aktif(panel_id, threshold_days=7, dry_run=False, selected_node_ids=None):
    output = []
    total_dihapus = 0

    inactive_servers, summary = get_server_tidak_aktif(panel_id, threshold_days=threshold_days, max_to_check=jumlahrender)

    if selected_node_ids:
        selected_node_ids = set(map(str, selected_node_ids))
        inactive_servers = [s for s in inactive_servers if str(s["node_id"]) in selected_node_ids]

    processed_servers = []
    for server in inactive_servers:
        updated_at_str = server["updated_at"]

        try:
            updated_at = None if updated_at_str == "-" else parse(updated_at_str)
        except Exception:
            output.append(f"Gagal parsing waktu untuk server '{server['server_name']}', dilewati.")
            continue

        processed_servers.append({**server, "updated_at": updated_at})

    processed_servers.sort(key=lambda s: s["updated_at"] or datetime.min)

    for server in processed_servers:
        if server["updated_at"] is None:
            output.append(f"Server '{server['server_name']}' milik {server['username']} tidak memiliki log aktivitas.")
        else:
            output.append(
                f"Server '{server['server_name']}' milik {server['username']} di {server['node_name']}, "
                f"terakhir aktif {server['updated_at'].strftime('%d %B %Y %H:%M:%S')}."
            )

        if dry_run:
            output.append("  [DRY RUN] Tidak dihapus.")
        else:
            if delete_server(panel_id, server["id"]):  # <-- FIX disini
                output.append(f"  Server '{server['server_name']}' berhasil dihapus.")
                total_dihapus += 1
            else:
                output.append(f"  Gagal menghapus server '{server['server_name']}'.")

    output.append("\nRingkasan:")
    output.append(f"  Total server tidak aktif ditemukan: {len(processed_servers)}")
    output.append(f"  Total server dihapus: {total_dihapus}")
    output.append(f"  Total server tersisa: {len(processed_servers) - total_dihapus}")
    return output


# Konfigurasi clear data server user
def hapus_server_tidak_valid(panel_id, simulasi=True):
    import requests
    output = []

    def ambil_id_server_dari_pterodactyl():
        semua_id = set()
        page = 1
        while True:
            res = requests.get(
                f"{PANELS[panel_id]['url']}/api/application/servers?page={page}",
                headers=get_headers(panel_id)
            )
            if res.status_code != 200:
                break

            data = res.json()
            for srv in data.get("data", []):
                semua_id.add(srv["attributes"]["id"])

            if not data.get("meta", {}).get("pagination", {}).get("links", {}).get("next"):
                break
            page += 1

        return semua_id

    # Ambil semua ID server valid dari Pterodactyl
    id_valid = ambil_id_server_dari_pterodactyl()
    servers = Server.query.all()

    total_dihapus = 0
    total_dilewatkan = 0

    for srv in servers:
        server_id = srv.id
        server_name = srv.name
        user_id = srv.user_id
        cpu, ram, disk = srv.cpu, srv.ram, srv.disk

        user = User.query.get(user_id)
        user_email = user.email if user else f"User {user_id}"

        # Skip server admin
        if user_email == admin_mail:
            output.append(
                f"Server '{server_name}' milik '{user_email}' dilewatkan karena merupakan admin."
            )
            total_dilewatkan += 1
            continue
            
        if user_email == moderator_mail:
            output.append(
                f"Server '{server_name}' milik '{user_email}' dilewatkan karena merupakan moderator."
            )
            total_dilewatkan += 1
            continue

        if server_id not in id_valid:
            output.append(
                f"Server '{server_name}' milik '{user_email}' (ID: {server_id}) tidak ditemukan di Pterodactyl."
            )

            if simulasi:
                output.append("  [DRY RUN] Tidak dihapus.")
            else:
                if user:
                    # Kurangi resource user
                    user.server = max(0, user.server - 1)
                    user.cpu = max(0, user.cpu - cpu)
                    user.ram = max(0, user.ram - ram)
                    user.disk = max(0, user.disk - disk)

                    # =========================
                    # ✅ RESET STATE BOOST & RAM UPGRADE
                    # =========================
                    user.last_boost = None
                    user.last_boost_used = None
                    user.ram_upgrade_start = None
                    user.ram_upgrade_end = None

                db.session.delete(srv)
                total_dihapus += 1
                output.append("Server berhasil dihapus dan state user di-reset.")

        else:
            total_dilewatkan += 1

    if not simulasi:
        db.session.commit()

    output.append("")
    output.append("Ringkasan:")
    output.append(f"  - Total server dicek: {len(servers)}")
    output.append(f"  - Server tidak valid & dihapus: {total_dihapus}")
    output.append(f"  - Server valid & dilewatkan: {total_dilewatkan}")

    return output
    
# Trial
def mark_trial(user):
    now = datetime.utcnow()

    user.ram_upgrade_start = now
    user.ram_upgrade_end = now + timedelta(days=2)

    user.ram = 1024
    user.cpu = 80
    user.trialramused = 1

    db.session.commit()
    
def mark_trial_two(user):
    now = datetime.utcnow()

    user.ram_upgrade_start = now
    user.ram_upgrade_end = now + timedelta(days=2)

    user.ram = 1024
    user.cpu = 80
    user.trialramused = 1
    
    if not user.serverid:
        return False

    panel_id = str(user.serverid)

    # 5️⃣ Validasi panel
    if panel_id not in PANELS:
        return False

    # 6️⃣ Ambil server
    server = Server.query.filter_by(user_id=user.id).first()
    if not server:
        return False

    # 7️⃣ Revert ke default 1024
    DEFAULT_RAM = 1024
    try:
        ok = revert_ram(panel_id, user, server, DEFAULT_RAM)
        if not ok:
            return False
    except Exception as e:
        print(f"⚠️ Revert gagal {user.email}:", e)
        return False

    db.session.commit()
    
def ensure_trial_on_dashboard(user):

    if user.trialramused == 1:
        return False

    # 1️⃣ Tidak punya server
    if user.server != 1:
        return False

    # 2️⃣ Sedang trial / upgrade
    if user.ram_upgrade_start is not None:
        return False

    # 3️⃣ HANYA RAM 1024 YANG DIPROSES
    if user.ram != 1024:
        return False

    # 4️⃣ Wajib punya serverid
    if not user.serverid:
        return False

    panel_id = str(user.serverid)

    # 5️⃣ Validasi panel
    if panel_id not in PANELS:
        return False

    # 6️⃣ Ambil server
    server = Server.query.filter_by(user_id=user.id).first()
    if not server:
        return False

    # 7️⃣ Revert ke default 512
    DEFAULT_RAM = 512
    try:
        ok = revert_ram(panel_id, user, server, DEFAULT_RAM)
        if not ok:
            return False
    except Exception as e:
        print(f"⚠️ Revert gagal {user.email}:", e)
        return False

    mark_trial_two(user)
    return True

# Konfigurasi ram spesial
SPECIAL_COOLDOWN = timedelta(days=7)
def can_use_special_ram(user: User):
    if not user.special_ram_last_used:
        return True, None

    now = datetime.utcnow()
    diff = now - user.special_ram_last_used

    if diff >= SPECIAL_COOLDOWN:
        return True, None

    remaining = SPECIAL_COOLDOWN - diff
    return False, remaining
    
# Konfigurasi sync coin 
COIN_JSON_URL = os.getenv("COIN_JSON_URL_KOCHENG")
def load_coin_data():
    try:
        response = requests.get(COIN_JSON_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("[ERROR] Gagal load coin JSON:", e)
        return {}

def get_user_coin(email):
    data = load_coin_data()
    return data.get(email, {}).get("coin", 0)
    
# Konfigurasi captcha
def verify_hcaptcha(token):
    secret_key = "ES_15f1b4711e9546d88d0a4371971da199"  # Ganti dengan Secret Key dari hCaptcha
    response = requests.post("https://hcaptcha.com/siteverify", data={
        'secret': secret_key,
        'response': token
    })
    result = response.json()
    return result.get("success", False)
    
# Fungsi referral code
def check_invite_milestone(user, inviter):
    total = User.query.filter_by(referred_by=inviter.referral_code).count()

    milestones = [
        (3, 20, "milestone_3"),
        (5, 50, "milestone_5"),
        (10, 100, "milestone_10"),
        (15, 150, "milestone_15"),
        (20, 210, "milestone_20"),
        (25, 300, "milestone_25"),
        (30, 500, "milestone_30"),
    ]

    for jumlah, reward, attr in milestones:
        if total >= jumlah and not getattr(inviter, attr):
            setattr(inviter, attr, True)
            inviter.coin += reward
            activity = ReferralActivity(
                inviter_id=inviter.id,
                invited_id=user.id,
                action=attr,
                reward=reward
            )
            db.session.add(inviter)
            db.session.add(activity)
            db.session.commit()
    
def log_referral_activity(user, action):
    if not user.referred_by:
        return

    inviter = User.query.filter_by(referral_code=user.referred_by).first()
    if not inviter:
        return

    existing = ReferralActivity.query.filter_by(invited_id=user.id, action=action).first()
    if existing:
        return

    reward = 0
    if action == "create_server":
        reward = 15
    elif action == "input_code":
        reward = 5
    elif action == "get_50_coin":
        reward = 20
    elif action == "get_100_coin":
        reward = 50
    elif action == "get_200_coin":
        reward = 100

    inviter.coin += reward
    db.session.add(inviter)

    activity = ReferralActivity(
        inviter_id=inviter.id,
        invited_id=user.id,
        action=action,
        reward=reward
    )
    db.session.add(activity)
    db.session.commit()

    check_invite_milestone(user, inviter)    
    
# Konfigurasi OAuth Google
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id= G_CLIENT_ID,
    client_secret= G_CLIENT_SECRET,
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile',
    },
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Tentukan folder upload dan extension yang diizinkan
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Fungsi untuk memeriksa apakah file yang diupload valid (hanya gambar)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
def get_profile_photo(user):
    if user.photo_url:
        return url_for('static', filename=user.photo_url)
    else:
        inisial = user.nama[0].upper()
        return f"https://ui-avatars.com/api/?name={inisial}&background=random&color=fff"

def send_verification_email(email_penerima, kode):
    RESEND_API_KEY = EMAIL_API_TOKEN  # Ganti dengan API Key kamu
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
    "from": "Kocheng App <noreply@kocheng.biz.id>",
    "to": email_penerima,
    "subject": "Code for verification process",
    "html": f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Email Verification</title>
  </head>
  <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,Helvetica,sans-serif;">
    <div style="max-width:600px;margin:30px auto;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
      <div style="text-align:center;padding:20px;border-bottom:1px solid #e5e7eb;">
        <img src="https://kocheng.biz.id/static/logo.webp" alt="Company Logo" style="height:120px;">
      </div>
      <div style="padding:30px;color:#111827;">
        <h2 style="margin-top:0;font-size:20px;">Your Verification Code</h2>
        <p style="margin:0 0 20px;font-size:15px;color:#374151;">
          Please use the code below to verify your account. This code will expire in <strong>10 minutes</strong>.
        </p>
        <div style="text-align:center;margin:25px 0;">
          <div style="display:inline-block;padding:16px 28px;font-size:26px;letter-spacing:6px;font-weight:bold;color:#0b5fff;border:2px solid #0b5fff;border-radius:8px;background:#f9fbff;">
            {kode}
          </div>
        </div>
        <p style="margin:0;font-size:14px;color:#6b7280;">
          If you did not request this code, please ignore this email or contact our support team.
        </p>
      </div>
      <footer style="background:#ffffff;border-top:1px solid #e5e7eb;padding:16px;font-size:12px;text-align:center;color:#6b7280;line-height:1.5;">
        <p style="margin:4px 0;font-weight:600;color:#374151;">Kocheng's |> Sahabat Ai Nusantara</p>
        <p style="margin:4px 0;">
          <a href="https://kocheng.biz.id/privacypolicy" style="color:#2563eb;text-decoration:none;">Privacy Policy</a> | 
          <a href="https://kocheng.biz.id/tos" style="color:#2563eb;text-decoration:none;">Terms of Service</a> | 
          <a href="https://kocheng.biz.id/advertisingagreement" style="color:#2563eb;text-decoration:none;">Ads Disclosure</a> | 
          <a href="https://kocheng.biz.id/blog" style="color:#2563eb;text-decoration:none;">Blog</a>
        </p>
        <p style="margin:4px 0;">JL. Anggrek Klagenserut, Jiwan Kabupaten Madiun (6311).</p>
        <p style="margin:4px 0;">📧 supporthosting@kocheng.tech</p>
      </footer>
    </div>
  </body>
</html>
"""
}

    response = requests.post(url, headers=headers, json=data)

    print("Status:", response.status_code)
    print("Respon:", response.text)

def revert_ram(panel_id, user, server_data, ramasli):
    """Kembalikan RAM ke spesifikasi normal untuk server tertentu di panel tertentu"""
    if panel_id not in PANELS:
        print(f"[ERROR] Panel {panel_id} tidak ditemukan di konfigurasi PANELS")
        return False

    panel = PANELS[panel_id]
    headers = {
        "Authorization": f"Bearer {panel['api_key']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    url = f"{panel['url']}/api/application/servers/{server_data.id}/build"

    payload = {
        "allocation": server_data.allocation_id,
        "memory": ramasli,
        "swap": 0,
        "disk": user.disk,
        "io": 500,
        "cpu": user.cpu,
        "threads": None,
        "feature_limits": {
            "databases": 1,
            "backups": 1,
            "allocations": 1
        }
    }

    try:
        r = requests.patch(url, headers=headers, json=payload)
        r.raise_for_status()
        print(f"[INFO] PATCH sukses untuk {user.email} - server_id {server_data.id} ({panel_id})")
        return True
    except Exception as e:
        print(f"[ERROR] PATCH gagal untuk {user.email} ({panel_id}) - Status: {r.status_code} - Response: {r.text}")
        return False


def get_allocation_from_api(panel_id, server_id):
    """Ambil allocation_id dari server di panel tertentu"""
    if panel_id not in PANELS:
        print(f"[ERROR] Panel {panel_id} tidak ditemukan di konfigurasi PANELS")
        return None

    panel = PANELS[panel_id]
    headers = {
        "Authorization": f"Bearer {panel['api_key']}",
        "Accept": "application/json",
    }

    url = f"{panel['url']}/api/application/servers/{server_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        return data["attributes"]["allocation"]
    except Exception as e:
        print(f"[ERROR] Gagal ambil allocation dari API ({panel_id}) server {server_id}: {e}")
        return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Pastikan user sudah login
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Ambil data user dari database
        user = User.query.get(session['user_id'])
        if not user:
            return redirect(url_for('login'))
        
        # Cek apakah user adalah admin atau moderator
        admin_emails = admin_mail
        
        if user.email == admin_emails:
            return f(*args, **kwargs)
        else:
            return redirect('/dashboard')
    
    return decorated_function
    
def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Pastikan user sudah login
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Ambil data user dari database
        user = User.query.get(session['user_id'])
        if not user:
            return redirect(url_for('login'))
        
        if user.is_moderator == True:
            return f(*args, **kwargs)
        else:
            return redirect('/dashboard')
    
    return decorated_function
    
#------ SISTEM BACKUP ------#
MEGA_API = "https://railway-megaapp.fly.dev"

def get_ptero_user(email, panel_id):
    panel = PANELS.get(panel_id)
    if not panel:
        print(f"[ERROR] Panel {panel_id} tidak ditemukan")
        return None

    url = f"{panel['url']}/api/application/users?filter[email]={email}"
    res = requests.get(url, headers=get_headers(panel_id)).json()
    if "data" not in res or res["meta"]["pagination"]["total"] == 0:
        return None
    return res["data"][0]["attributes"]

def get_servers_by_userid(user_id, panel_id):
    panel = PANELS.get(panel_id)
    if not panel:
        return []
    url = f"{panel['url']}/api/application/users/{user_id}?include=servers"
    res = requests.get(url, headers=get_headers(panel_id)).json()
    if "relationships" not in res["attributes"]:
        return []
    return res["attributes"]["relationships"]["servers"]["data"]

def list_files(panel_id, uuid, directory="/"):
    panel = PANELS.get(panel_id)
    url = f"{panel['url']}/api/client/servers/{uuid}/files/list?directory={directory}"
    res = requests.get(url, headers=get_client_headers(panel_id)).json()
    return res

def ptero_download_file(panel_id, uuid, path):
    panel = PANELS.get(panel_id)
    url = f"{panel['url']}/api/client/servers/{uuid}/files/contents?file={path}"
    res = requests.get(url, headers=get_client_headers(panel_id))
    if res.status_code == 200:
        return res.content
    return None
    
def is_panel_alive(panel_id, timeout=5):
    panel = PANELS.get(panel_id)
    if not panel:
        return False

    try:
        r = requests.get(panel["url"], timeout=timeout)
        return r.status_code < 500
    except requests.RequestException:
        return False
        
def reset_user_server_data(user):
    print(f"[RESET] Server user {user.email} tidak ditemukan di Pterodactyl")

    # hapus semua server milik user
    Server.query.filter_by(user_id=user.id).delete()

    # reset field user
    user.serverid = None
    user.uuid = None
    user.cpu = 0
    user.ram = 0
    user.disk = 0
    user.server = 0
    user.last_boost = None
    user.last_boost_used = None
    user.ram_upgrade_start = None
    user.ram_upgrade_end = None

    db.session.commit()

def sync_user_multi_panel(user):
    email = user.email
    found_server = False

    for panel_id in PANELS.keys():

        # 0. CEK PANEL AKTIF
        if not is_panel_alive(panel_id):
            print(f"[SKIP] Panel {panel_id} tidak bisa diakses")
            continue

        # 1. CARI USER DI PANEL
        ptero_user = get_ptero_user(email, panel_id)
        if not ptero_user:
            continue

        ptero_user_id = ptero_user["id"]

        # 2. AMBIL SERVER USER
        servers = get_servers_by_userid(ptero_user_id, panel_id)
        if not servers:
            continue

        # 3. AMBIL SERVER PERTAMA
        server_data = servers[0]["attributes"]
        limits = server_data.get("limits", {})

        server_cpu = limits.get("cpu", 0)
        server_ram = limits.get("memory", 0)
        server_disk = limits.get("disk", 0)

        serverspec = ServerSpec.query.filter_by(id=panel_id).first()
        if not serverspec:
            print(f"[ERROR] ServerSpec tidak ditemukan untuk {panel_id}")
            continue

        # =========================
        # ✅ SERVER DITEMUKAN
        # =========================
        found_server = True

        # UPDATE USER (DEFAULT)
        user.serverid = panel_id
        user.uuid = server_data["uuid"]
        user.cpu = server_cpu
        user.ram = server_ram
        user.disk = server_disk
        user.server = 1

        allocation_id = get_allocation_from_api(panel_id, server_data["id"])

        # UPDATE / SIMPAN SERVER
        server_entry = Server(
            id=server_data["id"],
            serverid=panel_id,
            name=server_data.get("name"),
            uuid=server_data["uuid"],
            user_id=user.id,
            server=1,
            cpu=server_cpu,
            ram=server_ram,
            disk=server_disk,
            allocation_id=allocation_id
        )
        db.session.merge(server_entry)

        # COIN DEFAULT
        from web1.scheduler_tasks import sync_coin_to_github
        if user.coin == 0:
            user.coin = 20
            sync_coin_to_github()

        # CEK & REVERT RAM
        try:
            current_ram = server_data["limits"]["memory"]

            allow_revert = (
                current_ram > 1024 and
                user.boostserver <= 0 and
                user.ram_upgrade_start is None and
                user.ram_upgrade_end is None
            )

            if allow_revert:
                print(f"[RAM REVERT] {current_ram}MB → 1024MB | {panel_id}")
                revert_ram(panel_id, user, server_entry, 512)
            else:
                print(f"[RAM SKIP] {current_ram}MB | boost={user.boostserver}")

        except Exception as e:
            print(f"[WARN] Gagal cek/revert RAM: {e}")

        db.session.commit()
        return True  # ⬅️ STOP, SERVER SUDAH DITEMUKAN

    # =========================
    # ❌ TIDAK DITEMUKAN DI SEMUA PANEL
    # =========================
    if not found_server and user.server == 1:
        reset_user_server_data(user)

    return False

def build_zip_memory(panel_id, uuid):
    global visited_paths
    visited_paths = set()

    zip_buffer = io.BytesIO()
    zipf = zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED)

    def add_path(base_dir="/"):
        if base_dir in visited_paths:
            return
        visited_paths.add(base_dir)

        files = list_files(panel_id, uuid, base_dir)
        for f in files.get("data", []):
            name = f["attributes"]["name"]
            is_file = f["attributes"]["is_file"]
            size = f["attributes"]["size"]
            rel_path = os.path.join(base_dir, name).replace("//", "/")

            if name in ("node_modules", ".", ".."):
                continue

            if is_file and size > 50 * 1024 * 1024:  # skip >50MB
                continue

            if is_file:
                content = ptero_download_file(panel_id, uuid, rel_path)
                if content:
                    zipf.writestr(rel_path.lstrip("/"), content)
            else:
                add_path(rel_path)

    # mulai dari root
    add_path("/")
    zipf.close()

    zip_buffer.seek(0)
    return zip_buffer
           
def trigger_backup_process(email, panel_id):
    zip_api_url = f"{MEGA_API}/build/kocheng/backup"
    payload = {
        "email": email,
        "panel_id": panel_id
    }

    try:
        print("[BACKUP] Trigger start:", email)

        r = requests.post(
            zip_api_url,
            json=payload,
            timeout=300
        )

        print("[BACKUP] Status:", r.status_code)
        print("[BACKUP] Response:", r.text)

        if r.status_code not in [200, 202]:
            print("❌ Backup API gagal")

    except requests.exceptions.Timeout:
        print("❌ Backup timeout")

    except Exception as e:
        print("❌ Backup trigger error:", e)
        
def backup_and_upload(user):
    panel_id = str(user.serverid) if user.serverid else None

    t = Thread(
        target=trigger_backup_process,
        args=(user.email, panel_id)
    )
    t.start()
    
    # === JIKA SUKSES ===
    backup_name = f"backup_{user.email}.zip"
    print(f"[OK] Backup {backup_name} berhasil diupload ke Mega")

    user.last_backup = datetime.utcnow()
    user.next_backup = user.last_backup + timedelta(weeks=1)
    user.auto_backup_enabled = True
    user.is_backup_mega = True
    user.last_filename = backup_name

    db.session.commit()
    return True
    
#------ SISTEM UPDATE LAST LOGIN ------#
@app.before_request
def update_last_login():
    user_email = session.get("email")
    if not user_email:
        return None

    user = User.query.filter_by(email=user_email).first()
    if user:
        user.last_login = datetime.utcnow()
        db.session.commit()
#------ IKLAN ------#
def aktifkan_iklan(user):
    user.iklan = 1
    user.iklan_expiry = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
def cek_iklan_kedaluwarsa(user):
    if user.iklan == 1 and user.iklan_expiry:
        if datetime.utcnow() > user.iklan_expiry:
            user.iklan = 0
            user.iklan_expiry = None
            db.session.commit()
            
@app.route("/iklan-selesai")
def iklan_selesai():
    if not session.get("user_id"):
        flash("Please Login First To Complete The Ad.", "error")
        return redirect("/signup")

    if request.args.get("done") != "yes":
        flash("The Ad Is Not Finished Yet.", "error")
        return redirect("/dashboard")

    user = User.query.get(session["user_id"])
    panel_id = request.args.get("panel_id")
    if not user:
        flash("User not found.", "error")
        return redirect("/signup")

    email = user.email
    user.serverid = panel_id
    ts = int(datetime.utcnow().timestamp())
    secret = "ganti_secretmu"
    raw = f"{email}:{secret}:{ts}"
    token = sha256(raw.encode()).hexdigest()

    aktifkan_iklan(user)
    session["sudah_buka_create"] = True

    return redirect(f"/panel/create?email={email}&token={token}&ts={ts}")
#------ HALAMAN DASHBOARD UTAMA------#
@app.route("/")
def awal():
    return redirect("/signup", code=301)
    
@app.route("/getstarted")
def getstarted():
    return redirect("https://kocheng.biz.id", code=301)
    
@app.route("/privacy")
def privacypolicy():
    return redirect("https://kocheng.biz.id/privacypolicy", code=301)
    
@app.route("/tos")
def tos():
    return redirect("https://kocheng.biz.id/tos", code=301)
    
@app.route("/advertisingagreement")
def advertisingagreement():
    return redirect("https://kocheng.biz.id/advertisingagreement", code=301)
    
@app.route("/blog")
def blog():
    return redirect("https://kocheng.biz.id/blog", code=301)
    
@app.route("/signup")
def halaman_login():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:  # kalau user valid
            return redirect("/dashboard")
        else:
            session.pop('user_id', None)

    return render_template('Login-Daftar-Page/login-page.html')
    
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        logging.warning("[DASHBOARD] Session tidak punya user_id, redirect ke /")
        return redirect('/')

    user = User.query.get(session['user_id'])
    resp = check_maintenance()
    if resp:
        return resp
        
    if not user:
        logging.warning(f"[DASHBOARD] User ID {session.get('user_id')} tidak ditemukan di db. Session direset.")
        session.clear()
        return redirect('/')

    if user.is_banned:
        logging.info(f"[DASHBOARD] User {user.email} dibanned. Redirect ke signin.")
        return redirect('/signin/email?banned=success')

    session.modified = True

    try:
        locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )

        if locked and user.email != admin_mail:
            logging.info(f"[DASHBOARD] Locked=True, redirect user {user.email} ke /dashboard/lock")
            return redirect(url_for("dashboard_lock"))

        # ===== HITUNG DATA USER =====
        photo = get_profile_photo(user)
        server = ServerSpec.query.filter_by(id="server1").first()
        now = datetime.utcnow()
        last_login = user.last_login or now
        batas_shutdown = last_login + timedelta(days=5)
        sisa_hari = (batas_shutdown - now).days

        # ===== DETEKSI DUPLIKAT DEVICE/IP =====
        ip_addr = get_client_ip()
        blokir_create = False
        ip_users = []  # list email akun lain
        user.ip_address = ip_addr
        db.session.commit()
        
        if ip_addr:
           ip_users = User.query.filter(
           User.ip_address == ip_addr,
           User.id != user.id
             ).all()

        total_ip = len(ip_users)
        if total_ip >= 3:
           blokir_create = True

        cek_iklan_kedaluwarsa(user)
        ensure_trial_on_dashboard(user)
        
        if not session.get("coin_synced"):
           print("[SYNC] Sinkronisasi coin pertama kali dilakukan")

           coin_sync = get_user_coin(user.email)

           if coin_sync > user.coin:
               user.coin = coin_sync
               db.session.commit()
               session["coin_synced"] = True
        else:
            print("[SYNC] Dilewati (sudah pernah sync di session ini)")
           
        do_sync = False
        if not session.get("sync_done"):
            print("[SYNC] Sinkronisasi pertama kali dilakukan")
            
            do_sync = True

            sync_ok = sync_user_multi_panel(user)

            session["sync_done"] = True
        else:
            print("[SYNC] Dilewati (sudah pernah sync di session ini)")

        html = render_template(
            'Main-Page/dashboard.html',
            user=user,
            photo=photo,
            admin_mail=admin_mail,
            panel_cpu=server.cpu,
            panel_ram=server.ram,
            panel_disk=server.disk,
            last_login=last_login,
            sisa_login_hari=sisa_hari,
            blokir_create=blokir_create,
            countdown_days=countdown_days,
            countdown_seconds=countdown_seconds,
            locked=locked,
            telegrambotlink=telegrambotlink,
            whatsapp_number=whatsapp_number,
            whatsapp_channel=whatsapp_channel,
            ip_users=ip_users,
            do_sync=do_sync,
            ram_upgrade_start=user.ram_upgrade_start,
            ram_upgrade_end=user.ram_upgrade_end
        )

        resp = make_response(html)
        device_id = get_or_create_device_id(resp)
        resp.set_cookie("csrf_token", generate_csrf(), samesite="Lax", secure=True)
        return resp

    except Exception as e:
        logging.error(f"[DASHBOARD] Error render dashboard: {str(e)}")
        flash("Terjadi error saat membuka dashboard, silakan login ulang.", "error")
        session.clear()
        return redirect('/signin/email')
      
@app.route("/hapus-akun-ip", methods=["POST"])
def hapus_akun_ip():
    if 'user_id' not in session:
        return redirect('/signin/email')

    email = request.form.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return redirect("/dashboard")

    if user.server and user.server > 0:
        # ---- Hapus server Pterodactyl ----
        try:
            success, msg = delete_pterodactyl_server(user)
            print("[DELETE SERVER] Server deletion:", msg)
        except Exception as e:
            print("[DELETE SERVER ERROR]", str(e))
    else:
        print("[SKIP DELETE SERVER] User tidak punya server (>0). Tidak menghapus server Pterodactyl.")

    try:
        db.session.delete(user)
        db.session.commit()
        print("[DELETE USER] User berhasil dihapus.")
    except Exception as e:
        print("[DELETE USER ERROR]", str(e))

    return redirect("/dashboard?deleteaccount=success")
    
@app.route("/hapus-akun", methods=["POST"])
def hapus_akun():
    if 'user_id' not in session:
        return redirect('/signin/email')

    user = User.query.get(session['user_id'])

    if not user:
        return redirect("/dashboard")

    if user.server and user.server > 0:
        # ---- Hapus server Pterodactyl ----
        try:
            success, msg = delete_pterodactyl_server(user)
            print("[DELETE SERVER] Server deletion:", msg)
        except Exception as e:
            print("[DELETE SERVER ERROR]", str(e))
    else:
        print("[SKIP DELETE SERVER] User tidak punya server (>0). Tidak menghapus server Pterodactyl.")

    try:
        db.session.delete(user)
        db.session.commit()
        print("[DELETE USER] User berhasil dihapus.")
    except Exception as e:
        print("[DELETE USER ERROR]", str(e))

    return redirect("/signin/email?deleteaccount=success")
     
@app.route('/dashboard/lock')
def dashboard_lock():
    locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )

    if not locked:
        logging.info("[DASHBOARD_LOCK] Lock tidak aktif, redirect ke /dashboard")
        return redirect(url_for("dashboard"))

    return render_template(
        "Main-Page/dashboard_lock.html",
        countdown_days=countdown_days,
        countdown_seconds=countdown_seconds
    )
    
@app.route("/dashboard/maintenance")
def dashboard_maintenance():
    return render_template("Main-Page/dashboard_maintenance.html")
        
@app.route("/panel/create/viatelegram", methods=["GET"])
def guide_create_viatele():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
        
    resp = check_maintenance()
    if resp:
        return resp

    return render_template("Panel-Page/guide_create_viatelegram.html", telegrambotlink=telegrambotlink)
    
@app.route("/panel/create/viawebsite", methods=["GET"])
def guide_create_viawebsite():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')
      
    resp = check_maintenance()
    if resp:
        return resp

    return render_template("Panel-Page/guide_create_viawebsite.html", telegrambotlink=telegrambotlink, ouolink=ouolink, whatsapp_number=whatsapp_number)
#------ PROFILE AREA ------#

@app.route('/profile')
def profil():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')

    user = User.query.get(user_id)
    if not user:
        return "User tidak ditemukan", 404
        
    resp = check_maintenance()
    if resp:
        return resp

    photo = get_profile_photo(user)
    return render_template('Main-Page/profile.html', user=user, photo=photo)

@app.route('/profile/edit-profile', methods=['GET', 'POST'])
def edit_profil():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
        
    resp = check_maintenance()
    if resp:
        return resp

    message = None

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        bio = request.form.get('bio', '').strip()
        password = request.form.get('password_hash', '').strip()
        password_ip_page = request.form.get('password_ip_page', '').strip()
        new_email = request.form.get('email', '').strip()

        if not nama or not bio or not new_email:
            message = "Name, bio, and email are required.."
            return render_template('Main-Page/edit_profile.html', user=user, message=message)

        # Proses jika email berbeda
        if new_email != user.email:
            existing_user = User.query.filter(User.email == new_email, User.id != user.id).first()
            if existing_user:
                message = "This email is already in use by another account!"
                return render_template('Main-Page/edit_profile.html', user=user, message=message)

            if not user.login_google:
                otp_kode = str(randint(100000, 999999))
                pending = {
                    'nama': nama,
                    'bio': bio,
                    'password_hash': password,
                    'password_ip_page': password_ip_page,
                    'new_email': new_email,
                    'otp': otp_kode
                }

                if 'photo' in request.files:
                    file = request.files['photo']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        pending['photo_url'] = f'uploads/{filename}'

                session['pending_update'] = pending
                session['terakhir_kirim_kode_mail'] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                send_verification_email(new_email, otp_kode)

                flash('The OTP code has been sent to your new email.')
                return redirect(url_for('verifikasi_edit_email'))

        # Jika tidak mengubah email atau user Google
        user.nama = nama
        user.bio = bio

        if not user.login_google and new_email == user.email:
            user.email = new_email

        if password:
            user.password_hash = generate_password_hash(password)

        if password_ip_page:
            user.password_ip_page = password_ip_page

        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user.photo_url = f'uploads/{filename}'

        db.session.commit()
        return redirect('/profile?change=success')

    return render_template('Main-Page/edit_profile.html', user=user, message=message)
        
@app.route('/profile/verification/new-email', methods=['GET', 'POST'])
def verifikasi_edit_email():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/')

    pending = session.get('pending_update')
    if not pending:
        return redirect('/profile/edit-profil')

    if request.method == 'POST':
        input_kode = request.form.get('kode', '').strip()
        if input_kode == pending.get('otp'):
            user = User.query.get(user_id)
            if not user:
                return "User tidak ditemukan", 404
                
            resp = check_maintenance()
            if resp:
             return resp

            user.nama = pending.get('nama', '')
            user.bio = pending.get('bio', '')
            user.email = pending.get('new_email', '')

            pw = pending.get('password_hash', '')
            if pw:
                user.password_hash = generate_password_hash(pw)

            if 'photo_url' in pending:
                user.photo_url = pending['photo_url']

            db.session.commit()
            session.pop('pending_update', None)
            return redirect('/profile?changemail=success')
        else:
            flash("Incorrect verification code. Please try again.", "warning")

    return render_template('Login-Daftar-Page/verifikasi-ubah-mail.html')

@app.route('/profile/verification/new-code', methods=['POST'])
def kirim_ulang_mail_code():
    pending = session.get('pending_update')
    if not pending or 'new_email' not in pending:
        return redirect('/profile/edit-profil')
        
    resp = check_maintenance()
    if resp:
        return resp

    now = datetime.utcnow()
    terakhir_kirim_new = session.get('terakhir_kirim_kode_mail')

    if terakhir_kirim_new:
        terakhir_kirim_dt = datetime.strptime(terakhir_kirim_new, "%Y-%m-%d %H:%M:%S")
        if now < terakhir_kirim_dt + timedelta(seconds=60):
            flash("Please wait a moment before resending the code.")
            return redirect('/profile/verification/new-email')

    # Kirim ulang kode
    kode_baru = str(randint(100000, 999999))
    pending['otp'] = kode_baru
    session['pending_update'] = pending
    session['terakhir_kirim_kode_mail'] = now.strftime("%Y-%m-%d %H:%M:%S")
    send_verification_email(pending['new_email'], kode_baru)

    flash("A new verification code has been sent.")
    return redirect('/profile/verification/new-email')

    
#------ REGISTRASI AREA ------#
@app.route('/signup/email', methods=['GET', 'POST'])
def register():
    referral_arg = request.args.get('referral', '').strip().upper() 
    
    if 'user_id' in session:
        usercheck = User.query.get(session['user_id'])
        if usercheck:
            return redirect("/dashboard")
        else:
            session.pop('user_id', None)

    if request.method == 'POST':
        nama = request.form['nama']
        email = request.form['email']
        password = request.form['password']
        referral_code = request.form.get('referral_code', '').strip().upper()
        device_id = request.form.get('device_id', '').strip()
        ip_address = request.remote_addr

        if User.query.filter_by(email=email).first():
            return render_template("Login-Daftar-Page/register.html", message="Email is already registered!", referral_code=referral_code)

        if referral_code:
            inviter = User.query.filter_by(referral_code=referral_code).first()
            if not inviter:
                return render_template("Login-Daftar-Page/register.html", message="Referral code not found!", referral_code=referral_code)

            if inviter.email == email:
                return render_template("Login-Daftar-Page/register.html", message="Can't use own referral!", referral_code=referral_code)

            existing = User.query.filter(
                (User.ip_address == ip_address) | (User.device_id == device_id),
                User.referred_by.isnot(None)
            ).first()

            if existing:
                return render_template("Login-Daftar-Page/register.html", message="Referral from this IP/device is already in use!", referral_code=referral_code)

            session['pending_referral'] = referral_code

        session['pending_nama'] = nama
        session['pending_email'] = email
        session['pending_password'] = generate_password_hash(password)
        session['pending_device_id'] = device_id
        session['pending_ip'] = ip_address

        kode = str(randint(100000, 999999))
        session['kode_verifikasi'] = kode
        session['email_verifikasi'] = email

        send_verification_email(email, kode)
        return redirect('/signup/email/verification')

    return render_template('Login-Daftar-Page/register.html', referral_code=referral_arg)

@app.route('/signin/email', methods=['GET', 'POST'])
def login2():
    message = None
    
    if 'user_id' in session:
        usercheck = User.query.get(session['user_id'])
        if usercheck:
            return redirect("/dashboard")
        else:
            session.pop('user_id', None)

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user:
            if user.password_hash:
                if check_password_hash(user.password_hash, password):
                    session['user_id'] = user.id

                    if not user.is_verified:
                        # Kirim kode verifikasi
                        kode = str(randint(100000, 999999))
                        session['kode_verifikasi'] = kode
                        session['email_verifikasi'] = email
                        send_verification_email(email, kode)

                        return redirect('/signup/email/verification')
                    else:
                        return redirect('/dashboard?signin=success')
                else:
                    message = "Wrong password!"
            else:
                message = "This account is registered through Google. Please log in using Google.."
        else:
            message = "Email not found!"

    return render_template("Login-Daftar-Page/login-email.html", message=message)

@app.route('/signup/email/verification', methods=['GET', 'POST'])
def verifikasi():
    if request.method == 'POST':
        input_kode = request.form['kode']
        if input_kode == session.get('kode_verifikasi'):
            nama = session.get('pending_nama')
            email = session.get('pending_email')
            password_hash = session.get('pending_password')
            referred_by = session.get('pending_referral')
            device_id = session.get('pending_device_id')
            ip_address = session.get('pending_ip')
            

            if not User.query.filter_by(email=email).first():
                referral_code = uuid.uuid4().hex[:8].upper()
                new_user = User(
                    nama=nama,
                    email=email,
                    password_hash=password_hash,
                    is_verified=True,
                    referral_code=referral_code,
                    referred_by=referred_by if referred_by else None,
                    device_id=device_id,
                    ip_address=ip_address,
                    coin=20 if referred_by else 0  # bonus koin 20 kalau referral
                )
                db.session.add(new_user)
                db.session.commit()

                # ✅ set session lengkap biar konsisten dengan login google
                session['user_id'] = new_user.id
                session['email'] = new_user.email
                session['nama'] = new_user.nama
                session.modified = True

                if referred_by:
                    log_referral_activity(new_user, "input_code")

            # bersihkan session sementara
            for key in [
                'pending_nama', 'pending_email', 'pending_password',
                'pending_referral', 'pending_device_id', 'pending_ip',
                'kode_verifikasi', 'email_verifikasi'
            ]:
                session.pop(key, None)

            return redirect('/dashboard?signup=success')
        else:
            flash("Incorrect verification code. Please try again.", "warning")
            return redirect('/signup/email/verification')

    return render_template("Login-Daftar-Page/verifikasi.html")
    
@app.route('/signup/email/verification/new-code', methods=['POST'])
def kirim_ulang():
    email = session.get('email_verifikasi')
    if not email:
        return redirect('/signin/email')
        
    # Cek cooldown 60 detik
    now = datetime.utcnow()
    terakhir_kirim = session.get('terakhir_kirim_kode')  # timestamp string

    if terakhir_kirim:
        terakhir_kirim_dt = datetime.strptime(terakhir_kirim, "%Y-%m-%d %H:%M:%S")
        if now < terakhir_kirim_dt + timedelta(seconds=60):
            flash("Please wait a moment before resending the code.")
            return redirect('/signup/email/verification')

    # Lanjutkan pengiriman ulang
    kode = str(randint(100000, 999999))
    session['kode_verifikasi'] = kode
    session['terakhir_kirim_kode'] = now.strftime("%Y-%m-%d %H:%M:%S")
    send_verification_email(email, kode)

    flash("A new verification code has been sent.")
    return redirect('/signup/email/verification')
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop("sync_done", None)
    session.pop("coin_synced", None)
    return redirect('/signin/email?logout=success')
    
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google')
def authorize_google():
    if 'error' in request.args:
        error_description = request.args.get('error_description', 'Authorization failed or was cancelled.')
        logging.error(f"Google OAuth error: {error_description}")
        return redirect('/')

    try:
        token = google.authorize_access_token()
    except Exception as e:
        logging.error(f"Exception during Google OAuth: {str(e)}")
        return redirect(url_for('awal'))

    user_info = google.get('userinfo').json()

    email = user_info['email']
    nama = user_info.get('name', '')
    photo_google = user_info["picture"]
    referral_code = uuid.uuid4().hex[:8].upper()

    existing_user = db.session.query(User).filter_by(email=email).first()

    if not existing_user:
        new_user = User(email=email, nama=nama, photo_google=photo_google, login_google=True, referral_code=referral_code)
        db.session.add(new_user)
        db.session.commit()
        user = new_user
    else:
        user = existing_user

    session['user_id'] = user.id
    session['email'] = user.email
    session['nama'] = user.nama

    return redirect('/dashboard?signin=success')
    
#------ SUPPORT & TICKET AREA ------#
@app.route("/support", methods=["GET", "POST"])
def support_page():
    user = None  # default supaya tidak error

    if "user_id" in session:
        user = User.query.get(session["user_id"])

    if request.method == "POST":
        if not user:  # kalau user belum login
            return redirect("/signup")

        subject = request.form.get("subject")
        category = request.form.get("category")
        message = request.form.get("message", "").strip()

        if user.email and subject and message:
            # 1. Buat tiket baru
            new_ticket = Ticket(
                user_email=user.email,
                subject=subject,
                category=category,
                status="Open",
                is_notified_admin=False
            )
            db.session.add(new_ticket)
            db.session.commit()

            # 2. Tambahkan reply pertama
            first_reply = Reply(
                ticket_id=new_ticket.id,
                sender="user",
                message=message,
                is_notified_admin=False
            )
            db.session.add(first_reply)
            db.session.commit()

            return redirect('/tickets?newticket=success')

    return render_template("Ticket-Page/support.html", user=user)
    
 
@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    user = None  # default supaya tidak error

    if "user_id" in session:
        user = User.query.get(session["user_id"])

    if request.method == "POST":
        if not user:  # kalau user belum login
            return redirect("/signup")

    return render_template("Ticket-Page/contact.html", whatsapp_number=whatsapp_number, telegram_user=telegram_user, whatsapp_channel=whatsapp_channel, telegram_channel=telegram_channel)

@app.route("/tickets")
def tickets_page():
    if "user_id" not in session:
        return redirect("/signup")

    user = User.query.get(session["user_id"])
    if not user:
        return redirect("/signup")

    # 🧠 Jika admin membuka halaman daftar tiket → tandai semua tiket user yang baru sebagai sudah "dibaca"
    if user.email == admin_mail:
        # Tandai semua reply dari user yang belum dibaca admin → is_notified_admin = True
        Reply.query.filter(
            Reply.sender == "user",
            Reply.is_notified_admin == False
        ).update({"is_notified_admin": True})

        # Kalau kamu juga pakai flag di Ticket (misalnya is_notified_admin), tandai juga
        if hasattr(Ticket, "is_notified_admin"):
            Ticket.query.filter_by(is_notified_admin=False).update({"is_notified_admin": True})

        db.session.commit()

        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    else:
        # User biasa → hanya tiketnya sendiri
        tickets = Ticket.query.filter_by(user_email=user.email).order_by(Ticket.created_at.desc()).all()

    return render_template("Ticket-Page/ticket.html", tickets=tickets, user=user, admin_mail=admin_mail)

@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not session.get("user_id"):
        return redirect("/signup")

    user = User.query.get(session["user_id"])

    # 📨 Kirim pesan / gambar
    if request.method == "POST":
        sender = request.form.get("sender")
        message = request.form.get("message", "").strip()
        image_files = request.files.getlist("images")

        if message or any(img.filename for img in image_files):
            reply = Reply(
                ticket_id=ticket.id,
                sender=sender,
                message=message if message else None
            )

            # Notifikasi untuk pihak lawan
            if sender == "admin":
                reply.is_notified_user = False  # User perlu dapat notif
            else:
                reply.is_notified_admin = False  # Admin perlu dapat notif

            db.session.add(reply)
            db.session.commit()

            # Simpan gambar jika ada
            image_urls = []
            for img in image_files:
                if img and img.filename:
                    filename = secure_filename(img.filename)
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    img.save(filepath)
                    image_url = f"/{filepath}"
                    image_urls.append(image_url)

                    reply_image = ReplyImage(reply_id=reply.id, image_url=image_url)
                    db.session.add(reply_image)

            db.session.commit()

            return jsonify({
                "sender": sender,
                "message": reply.message,
                "images": image_urls,
                "created_at": reply.created_at.strftime("%Y-%m-%d %H:%M")
            })

        return jsonify({"error": "No message or image provided"}), 400

    # 🌐 GET Ticket Detail
    replies = Reply.query.filter_by(ticket_id=ticket.id).order_by(Reply.created_at.asc()).all()

    # ✅ Tandai notifikasi sebagai "sudah dibaca"
    if user.email == admin_mail:
        # Admin membuka ticket → tandai semua balasan user sebagai sudah dibaca oleh admin
        Reply.query.filter(
            Reply.ticket_id == ticket.id,
            Reply.sender == "user",
            Reply.is_notified_admin == False
        ).update({"is_notified_admin": True})

        # Kalau kamu punya flag di Ticket, tandai juga
        if hasattr(ticket, "is_notified_admin"):
            ticket.is_notified_admin = True

    else:
        # User membuka ticket → tandai semua balasan admin sebagai sudah dibaca user
        Reply.query.filter(
            Reply.ticket_id == ticket.id,
            Reply.sender == "admin",
            Reply.is_notified_user == False
        ).update({"is_notified_user": True})

    db.session.commit()

    return render_template(
        "Ticket-Page/ticket_detail.html",
        ticket=ticket,
        replies=replies,
        admin_mail=admin_mail,
        user=user
    )

@app.route("/ticket/<int:ticket_id>/status/<string:new_status>")
def update_status(ticket_id, new_status):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = new_status
    db.session.commit()
    return redirect('/tickets?changestatus=success')

@app.route("/ticket/<int:ticket_id>/delete")
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    return redirect('/tickets?delete=success')
    
@app.route("/check_notifications")
def check_notifications():
    if "user_id" not in session:
        return jsonify({"notifications": []})

    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"notifications": []})

    notifications = []

    # ==================================================
    # 🧠 Admin: Notifikasi TIKET BARU atau pesan user baru
    # ==================================================
    if user.email == admin_mail:
        # Ambil reply dari user yang belum ditandai sebagai dibaca admin
        unread_replies = Reply.query.filter(
            Reply.sender == "user",
            Reply.is_notified_admin == False
        ).order_by(Reply.created_at.desc()).all()

        # Bisa juga ambil tiket baru yang belum ditandai, kalau pakai flag di Ticket
        # new_tickets = Ticket.query.filter_by(is_notified_admin=False).order_by(Ticket.created_at.desc()).all()

        if unread_replies:
            # Ambil satu notifikasi saja, cukup untuk men-trigger box
            r = unread_replies[0]
            notifications.append({
                "type": "new_ticket",
                "ticket_id": r.ticket_id,
                "sender": r.sender,
                "message_preview": (r.message[:50] + "...") if len(r.message) > 50 else r.message,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

    # ==================================================
    # 👤 User: Notifikasi BALASAN ADMIN yang belum dibaca user
    # ==================================================
    else:
        # Ambil semua reply dari admin untuk tiket milik user yang belum ditandai sebagai dibaca
        user_ticket_ids = Ticket.query.with_entities(Ticket.id).filter_by(user_email=user.email).subquery()

        unread_admin_replies = Reply.query.filter(
            Reply.ticket_id.in_(user_ticket_ids),
            Reply.sender == "admin",
            Reply.is_notified_user == False
        ).order_by(Reply.created_at.desc()).all()

        if unread_admin_replies:
            r = unread_admin_replies[0]
            notifications.append({
                "type": "new_reply",
                "ticket_id": r.ticket_id,
                "sender": r.sender,
                "message_preview": (r.message[:50] + "...") if len(r.message) > 50 else r.message,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

    return jsonify({"notifications": notifications})

#------ GET COIN AREA ------#
@app.route("/getcoin/afk")
def afk_coin_page():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect('/signup')
        
    resp = check_maintenance()
    if resp:
        return resp

    return render_template("Main-Page/afk-page.html", user=user)
    
@app.route('/getcoin/afk/earn', methods=['POST'])
def afk_earn():
    data = request.get_json()
    earned_coin = int(data.get('coin', 0))

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"success": False, "message": "Email not found"}), 404

    MAX_HARIAN = 200
    MAX_TOTAL = 1000
    today = datetime.utcnow().date()
    bulan_ini = datetime.utcnow().strftime("%Y-%m")

    if user.harian_coin_tanggal != today:
        user.harian_coin = 0
        user.harian_coin_tanggal = today

    if user.harian_coin >= MAX_HARIAN:
        return jsonify({"success": False, "message": "Daily limit of 200 coins has been reached"}), 403

    coin_boleh = min(earned_coin, MAX_HARIAN - user.harian_coin)
    user.coin = min(user.coin + coin_boleh, MAX_TOTAL)
    user.harian_coin += coin_boleh

    if user.afk_bonus_bulan != bulan_ini:
        user.afk_bonus_bulan = bulan_ini
        user.afk_total_coin_bulanan = 0
        user.afk_bonus_50 = False
        user.afk_bonus_100 = False
        user.afk_bonus_200 = False

    user.afk_total_coin_bulanan += coin_boleh
    bonus = 0
    bonus_text = ""

    if user.afk_total_coin_bulanan >= 200 and not user.afk_bonus_200:
        bonus = 70
        user.coin += bonus
        user.afk_bonus_200 = True
        bonus_text = "+70 bonus (AFK 200)"
    elif user.afk_total_coin_bulanan >= 100 and not user.afk_bonus_100:
        bonus = 50
        user.coin += bonus
        user.afk_bonus_100 = True
        bonus_text = "+50 bonus (AFK 100)"
    elif user.afk_total_coin_bulanan >= 50 and not user.afk_bonus_50:
        bonus = 20
        user.coin += bonus
        user.afk_bonus_50 = True
        bonus_text = "+20 bonus (AFK 50)"

    db.session.commit()

    return jsonify({
        "success": True,
        "coin_now": user.coin,
        "harian_now": user.harian_coin,
        "bulanan_afk": user.afk_total_coin_bulanan,
        "bonus": bonus,
        "bonus_text": bonus_text
    })

@app.route('/getcoin/afk/status')
def afk_status():

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    today = datetime.utcnow().date()
    harian_coin = 0 if user.harian_coin_tanggal != today else user.harian_coin

    return jsonify({
        "success": True,
        "harian_now": harian_coin,
        "coin_now": user.coin
    })
    
@app.route("/getcoin/referral", methods=["GET", "POST"])
def referral():
    if not session.get("user_id"):
        return redirect("/signup")

    user = User.query.get(session["user_id"])
    if not user:
        return redirect("/signup")
        
    resp = check_maintenance()
    if resp:
        return resp

    if request.method == "POST":
        if user.referred_by:
            flash("You have already entered the referral code.", "message")
            return redirect("/getcoin/referral")

        referral_code = request.form.get("referral_code", "").strip().upper()
        device_id = request.form.get("device_id")
        inviter = User.query.filter_by(referral_code=referral_code).first()

        if not inviter:
            flash("Referral code not found.", "error")
            return redirect("/getcoin/referral")

        if inviter.id == user.id:
            flash("You cannot enter your own referral code.", "error")
            return redirect("/getcoin/referral")

        user_ip = request.remote_addr
        existing = User.query.filter(
            or_(
                User.ip_address == user_ip,
                User.device_id == device_id
            ),
            User.referred_by.isnot(None),
            User.id != user.id
        ).first()

        if existing:
            flash("Referral from this IP or device is already in use.", "error")
            return redirect("/getcoin/referral")

        # ✅ Simpan ke user
        user.referred_by = referral_code
        user.ip_address = user_ip
        user.device_id = device_id
        user.coin += 20

        db.session.add(user)
        db.session.commit()

        # ✅ Catat aktivitas
        log_referral_activity(user, "input_code")

        flash("Success! You got 20 coins from referral.", "success")
        return redirect("/getcoin/referral")

    # ===================== GET ======================

    inviter = None
    if user.referred_by:
        inviter = User.query.filter_by(referral_code=user.referred_by).first()

    total_referred = ReferralActivity.query.filter_by(
        inviter_id=user.id,
        action="input_code"
    ).count()

    total_coin = db.session.query(func.sum(ReferralActivity.reward)).filter(
        ReferralActivity.inviter_id == user.id
    ).scalar() or 0

    # Ambil aktivitas referral log
    logs = ReferralActivity.query.filter_by(inviter_id=user.id).order_by(ReferralActivity.timestamp.desc()).all()
    invited_ids = list(set([log.invited_id for log in logs if log.invited_id]))
    invited_users = User.query.filter(User.id.in_(invited_ids)).all()
    invited_map = {u.id: u.nama for u in invited_users}

    # ✅ Label aksi
    action_labels = {
        "input_code": "Enter your code",
        "create_server": "Creating a server",
        "get_50_coin": "AFK get 50 coins",
        "get_100_coin": "AFK get 100 coins",
        "get_200_coin": "AFK get 200 coins",
        "milestone_3": "Invite 3 friends",
        "milestone_5": "Invite 5 friends",
        "milestone_10": "Invite 10 friends",
        "milestone_15": "Invite 15 friends",
        "milestone_20": "Invite 20 friends",
        "milestone_25": "Invite 25 friends",
        "milestone_30": "Invite 30 friends"
    }

    # ✅ Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 5

    full_activity_log = []
    for log in logs:
        full_activity_log.append({
            "username": invited_map.get(log.invited_id, "Unknown") if log.invited_id else "System",
            "action": action_labels.get(log.action, log.action.replace("_", " ")),
            "reward": log.reward
        })

    total_logs = len(full_activity_log)
    total_pages = (total_logs + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    activity_log = full_activity_log[start:end]

    # ✅ Leaderboard fix: semua reward dihitung (bukan cuma input_code)
    referral_activities = ReferralActivity.query.all()
    summary = defaultdict(lambda: {"jumlah": 0, "coin": 0})
    for act in referral_activities:
        if act.action == "input_code":
            summary[act.inviter_id]["jumlah"] += 1  # hitung undangan
        summary[act.inviter_id]["coin"] += act.reward  # hitung total koin (termasuk milestone, dll)

    user_ids = list(summary.keys())
    users = User.query.filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u for u in users}

    leaderboard = []
    for uid, data in summary.items():
        userx = user_map.get(uid)
        if userx:
            leaderboard.append({
                "nama": userx.nama,
                "email": userx.email,
                "total_undangan": data["jumlah"],
                "total_koin": data["coin"]
            })

    leaderboard = sorted(leaderboard, key=lambda x: x["total_undangan"], reverse=True)[:5]

    return render_template("Main-Page/input-refferal.html",
                           user=user,
                           inviter=inviter,
                           total_referred=total_referred,
                           total_referral_coin=total_coin,
                           leaderboard=leaderboard,
                           activity_log=activity_log,
                           total_pages=total_pages,
                           current_page=page)
                           
@app.route("/validate/referral")
def validate_referral():
    referral_code = request.args.get("code", "").strip().upper()
    device_id = request.args.get("device_id", "").strip()
    user_ip = request.remote_addr

    inviter = User.query.filter_by(referral_code=referral_code).first()
    if not inviter:
        return jsonify({"valid": False, "message": "Referral code not found."})

    # Cek apakah pengguna mencoba memasukkan kode referral miliknya sendiri
    if session.get("user_id") and session["user_id"] == inviter.id:
        return jsonify({"valid": False, "message": "You cannot enter your own referral code.."})

    # Deteksi apakah IP atau device_id sudah pernah dipakai (oleh user lain)
    existing = User.query.filter(
        (User.ip_address == user_ip) | (User.device_id == device_id),
        User.referred_by.isnot(None),
        User.id != inviter.id  # penting: pengecualian untuk user yang input kode referral sendiri
    ).first()

    if existing:
        return jsonify({"valid": False, "message": "Referral from this IP or device is already in use."})

    return jsonify({"valid": True})
    
@app.route("/getcoin/daily", methods=["POST"])
def klaim_harian():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    today = datetime.utcnow().date()

    if user.daily_claim_last == today:
        return jsonify({"success": False, "message": "You have claimed today."}), 400

    hari_ke = user.daily_claim_day + 1
    if hari_ke > 30:
        hari_ke = 1

    # Weighted random: 1–5 (sering), 6–10 (sedang), 11–20 (susah)
    coin_options = list(range(1, 21))
    weights = [10]*5 + [5]*5 + [1]*10
    reward = random.choices(coin_options, weights=weights)[0]

    user.coin += reward
    user.daily_claim_day = hari_ke
    user.daily_claim_last = today

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Successful claim +{reward} coin!",
        "reward": reward
    })
    
@app.route("/getcoin/misi")
def misi():
    if not session.get("user_id"):
        return redirect("/signup")
    user = User.query.get(session["user_id"])
    resp = check_maintenance()
    if resp:
        return resp
    
    return render_template("Main-Page/misi-page.html", user=user, now=datetime.utcnow())
#------ ADMIN AREA ------#
@app.route("/admin/users/delete/<int:user_id>", methods=["POST"])
@moderator_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User Successfully Deleted.", "success")
    return redirect('/admin/list/user?delete=success')

@app.route('/admin/list/user')
@moderator_required
def admin_users():
    page        = request.args.get('page', 1, type=int)
    email_query = request.args.get('email', '').strip()

    query = User.query
    if email_query:
        query = query.filter(User.email.ilike(f"%{email_query}%"))

    users = query.order_by(User.id.desc()).paginate(page=page, per_page=10)

    return render_template(
        'Admin-Page/admin-listuser.html',
        users=users,
        email_query=email_query
    )
    
@app.route('/admin/list/server')
@moderator_required
def admin_servers():
    page        = request.args.get('page', 1, type=int)
    email_query = request.args.get('email', '').strip()
    user_ids = []
    user = None

    if email_query:
        # cari user dari email
        user = User.query.filter(User.email.ilike(f"%{email_query}%")).first()
        if user:
            user_ids = [user.id]
        else:
            servers = Server.query.filter(False).paginate(page=page, per_page=10)
            return render_template(
                'Admin-Page/admin-listserver.html',
                servers=servers,
                email_query=email_query,
                user=None,
                PANELS=PANELS
            )

    query = Server.query
    if user_ids:
        query = query.filter(Server.user_id.in_(user_ids))

    servers = query.order_by(Server.created_at.desc()).paginate(page=page, per_page=10)

    # tambahin panel_url sesuai user.serverid
    for s in servers.items:
        u = User.query.get(s.user_id)
        if u and u.serverid in PANELS:
            s.panel_url = PANELS[u.serverid]["url"]
        else:
            s.panel_url = None

    return render_template(
        'Admin-Page/admin-listserver.html',
        servers=servers,
        email_query=email_query,
        user=user,
        PANELS=PANELS
    )
    
@app.route('/admin/server/delete/<int:server_id>', methods=['POST'])
@moderator_required
def delete_server_web(server_id):
    server = Server.query.get_or_404(server_id)
    user = User.query.get(server.user_id)

    try:
        db.session.delete(server)
        user.server = 0
        user.cpu = 0
        user.ram = 0
        user.disk = 0
        db.session.commit()
        flash('Server Successfully Deleted.', 'success')
    except SQLAlchemyError:
        db.session.rollback()
        flash('Gagal menghapus server.', 'error')

    return redirect('/admin/list/server?delete=success')
    
@app.route('/admin/server/clear-stream')
@admin_required
def clear_stream():
    action = request.args.get("action", "hapus_server")
    dry_run = request.args.get("dry_run") == "true"
    selected_node = request.args.get("selected_node")
    panel_id = request.args.get("panel_id", "server1")

    if panel_id not in PANELS:
        return Response("data: ⚠️ Panel tidak valid.\n\n", mimetype="text/event-stream")

    def generate():
        yield f"data: 🔄 Memulai aksi: {action} (Panel: {panel_id}, Node: {selected_node})\n\n"

        if action == "hapus_server":
            hasil = hapus_server_tidak_aktif(
                panel_id=panel_id,
                threshold_days=7,
                dry_run=dry_run,
                selected_node_ids=[selected_node] if selected_node else []
            )
            for line in hasil:
                yield f"data: {line}\n\n"

        elif action == "hapus_user":
            hasil = hapus_user_tanpa_server(panel_id=panel_id, dry_run=dry_run)
            for line in hasil:
                yield f"data: {line}\n\n"

        elif action == "cek_server_invalid":
            hasil = hapus_server_tidak_valid(panel_id=panel_id, simulasi=dry_run)
            for line in hasil:
                yield f"data: {line}\n\n"

        else:
            yield "data: ⚠️ Aksi tidak dikenal.\n\n"

        yield "data: 🟢 Proses selesai.\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")
    
@app.route("/admin/server/clear", methods=["GET"])
@admin_required
def page_clear():
    return render_template("Admin-Page/admin-cleanserver.html", PANELS=PANELS)

@app.route('/admin/get-node')
@admin_required
def get_node():
    panel_id = request.args.get("panel_id", "server1")  # default server1
    if panel_id not in PANELS:
        return jsonify({"error": "Invalid panel_id"}), 400

    refresh = request.args.get("refresh", "false").lower() == "true"
    query = request.args.get("q", "").strip().lower()

    data = get_node_data_cached(panel_id, force_refresh=refresh)

    if query:
        # Cocokkan nama dan ID
        names = [node["name"].lower() for node in data]
        ids = [str(node["id"]).lower() for node in data]

        matches = difflib.get_close_matches(query, names, n=5, cutoff=0.3)

        data = [
            node for node in data
            if query in str(node["id"]).lower()
            or query in node["name"].lower()
            or node["name"].lower() in matches
        ]

    return jsonify(data)
    
@app.route('/admin/coin/control', methods=['GET', 'POST'])
@moderator_required
def kelola_koin():
    if request.method == 'POST':
        email = request.form.get('email')
        jumlah = int(request.form.get('jumlah', 0))
        aksi = request.form.get('aksi')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash(f"User with email {email} not found.", "error")
        else:
            if aksi == 'tambah':
                user.coin += jumlah
            elif aksi == 'kurangi':
                user.coin = max(0, user.coin - jumlah)
            else:
                flash("Invalid action.", "error")
                return redirect(url_for('kelola_koin'))

            db.session.commit()
            flash(f"Coins successfully in{'plus' if aksi == 'tambah' else 'reduce'} for {email}.", "success")

    # Query user dengan filter pencarian dan min coin
    search = request.args.get('search')
    filter_min_100 = request.args.get('filter_min_100')

    query = User.query

    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))

    if filter_min_100:
        query = query.filter(User.coin >= 100)
    else:
        query = query.filter(User.coin > 0)

    users = query.order_by(User.coin.desc()).all()

    return render_template("Admin-Page/admin-coindata.html", users=users)

@app.route("/admin/update_logs")
@admin_required
def get_update_logs():
    """API untuk mengambil log dan status update spesifikasi server"""
    return jsonify({
        "logs": update_logs,
        "status": update_status,
        "queue_length": len(update_queue)
    })

@app.route("/admin/setting", methods=["GET", "POST"])
@admin_required
def admin_panel():

    # =========================
    # POST ACTIONS
    # =========================
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("user_id")
        node_id = request.form.get("node_id")

        if action == "toggle_moderator" and user_id:
            user = User.query.get(user_id)
            if user:
                user.is_moderator = not user.is_moderator
                db.session.commit()

        elif action == "toggle_banned" and user_id:
            user = User.query.get(user_id)
            if user:
                user.is_banned = not user.is_banned
                db.session.commit()

        elif action == "update_spec":
            ram = int(request.form.get("ram"))
            cpu = int(request.form.get("cpu"))
            disk = int(request.form.get("disk"))

            panel_id = request.args.get("panel_id", "server1")
            server_spec = ServerSpec.query.filter_by(id=panel_id).first()

            if server_spec:
                server_spec.ram = ram
                server_spec.cpu = cpu
                server_spec.disk = disk
                db.session.commit()
                enqueue_spec_update(panel_id=panel_id, ram=ram, disk=disk, cpu=cpu)

        elif action == "update_node" and node_id:
            limit = int(request.form.get("limit_server"))
            node = Node.query.get(node_id)
            if node:
                node.limit_server = limit
                db.session.commit()

        elif action == "toggle_maintenance":
            maintenance_mode = SiteSetting.get("maintenance_mode", "false") == "true"
            SiteSetting.set("maintenance_mode", "false" if maintenance_mode else "true")

        # =========================
        # 🔥 DASHBOARD LOCK CONTROL (FIXED)
        # =========================
        elif action == "toggle_dashboard_lock":
            force_unlock = SiteSetting.get("force_unlock_dashboard", "false") == "true"

            if force_unlock:
                # Matikan force unlock → balik ke auto
                SiteSetting.set("force_unlock_dashboard", "false")
            else:
                # Aktifkan force unlock → override auto
                SiteSetting.set("force_unlock_dashboard", "true")
                SiteSetting.set("lock_dashboard", "false")  # safety

        # POST → REDIRECT
        return redirect(url_for("admin_panel", change="success"))

    # =========================
    # GET DATA
    # =========================
    search_query = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    per_page = 10
    panel_id = request.args.get("panel_id", "server1")

    if panel_id not in PANELS:
        flash("Invalid panel ID.", "error")
        return redirect(url_for("admin_panel", q=search_query, page=page))

    # === USERS ===
    query = User.query
    if search_query:
        query = query.filter(User.email.ilike(f"%{search_query}%"))
    users = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page)

    # === SERVER SPEC ===
    server_spec = ServerSpec.query.filter_by(id=panel_id).first()
    if not server_spec:
        server_spec = ServerSpec(id=panel_id, ram=1024, cpu=80, disk=5072)
        db.session.add(server_spec)
        db.session.commit()

    nodes = Node.query.all()

    # === STATUS FLAGS ===
    maintenance_mode = SiteSetting.get("maintenance_mode", "false") == "true"
    manual_lock = SiteSetting.get("lock_dashboard", "false") == "true"
    force_unlock = SiteSetting.get("force_unlock_dashboard", "false") == "true"

    locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )

    # =========================
    # RENDER
    # =========================
    return render_template(
        "Admin-Page/admin-setting.html",
        users=users,
        server_spec=server_spec,
        nodes=nodes,
        search_query=search_query,
        PANELS=PANELS,
        panel_id=panel_id,
        maintenance_mode=maintenance_mode,
        locked=locked,
        auto_locked=auto_locked,
        manual_lock=manual_lock,
        force_unlock=force_unlock,
        countdown_days=countdown_days,
        countdown_seconds=countdown_seconds,
    )

#------ CREATE PANEL PTERODACTYL OTOMATIS AREA ------#
@app.route('/get-eggs')
def get_eggs():
    panel_id = request.args.get("panel_id")
    if not panel_id or panel_id not in PANELS:
        panel_id = next(iter(PANELS.keys()))  # default panel pertama

    result = fetch_egg_list(panel_id)
    if result is not None:
        return jsonify({"panel": panel_id, "eggs": result})
    else:
        return jsonify({"error": f"Gagal mengambil data dari panel {panel_id}"}), 500
        
@app.route('/get-node-server-counts')
def get_node_server_counts():
    # Ambil panel_id dari query param, default ke panel pertama
    panel_id = request.args.get("panel_id")
    if not panel_id or panel_id not in PANELS:
        panel_id = next(iter(PANELS.keys()))

    result = fetch_node_server_counts(panel_id)  # { "1": {"name": "...", "count": 10}, ... }
    if result is None:
        return jsonify({"error": f"Gagal mengambil data dari panel {panel_id}"}), 500

    # Ambil limit terbaru dari db
    nodes = Node.query.all()
    node_limits = {str(node.id): node.limit_server for node in nodes}

    # Gabungkan result dengan limit dari db
    for node_id, info in result.items():
        info["limit"] = node_limits.get(str(node_id), 35)  # default 35

    return jsonify({ "panel": panel_id, "nodes": result })
    
@app.route('/get-all-panels-status')
def get_all_panels_status():
    result = {}

    # Ambil limit terbaru dari db
    nodes = Node.query.all()
    node_limits = {str(node.id): node.limit_server for node in nodes}

    for panel_id, panel_info in PANELS.items():
        node_data = fetch_node_server_counts(panel_id)
        if node_data is None:
            result[panel_id] = {"error": f"Gagal ambil data dari {panel_id}"}
            continue

        all_nodes_full = True
        for node_id, info in node_data.items():
            limit = node_limits.get(str(node_id), 35)
            info["limit"] = limit
            if info["count"] < limit:
                all_nodes_full = False

        result[panel_id] = {
            "nodes": node_data,
            "all_full": all_nodes_full
        }

    return jsonify(result)
    

@app.route("/panel/detail")
def detail_akun():
    email = request.args.get("email")
    username = request.args.get("username")
    panel_id = request.args.get("panel_id")  # ambil dari query
    
    resp = check_maintenance()
    if resp:
        return resp

    if not email or not username:
        flash("Invalid account data.", "error")
        return redirect("/dashboard")

    if not panel_id or panel_id not in PANELS:
        panel_id = next(iter(PANELS.keys()))  # fallback ke panel pertama

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "error")
        return redirect("/dashboard")
        
    locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )
    if locked and user.email != admin_mail:
            logging.info(f"[DASHBOARD] Locked=True, redirect user {user.email} ke /dashboard/lock")
            return redirect(url_for("dashboard_lock"))

    account = {
        "email": user.email,
        "username": username,
        "panel_url": PANELS[panel_id]['url']  # ambil URL panel sesuai panel_id
    }

    now = datetime.utcnow()

    # ======= BOOST STATUS =======
    boost_used = False
    remaining_time = 0
    remaining_daily_seconds = 0

    if user.last_boost and (now - user.last_boost) < timedelta(hours=1):
        remaining_time = int((user.last_boost + timedelta(hours=1) - now).total_seconds())

    if user.last_boost_used and (now - user.last_boost_used) < timedelta(hours=24):
        boost_used = True
        remaining_daily_seconds = int((user.last_boost_used + timedelta(hours=24) - now).total_seconds())

    now = datetime.utcnow()
    active_boost_count = User.query.filter(
        User.last_boost != None,
        (now - User.last_boost) < timedelta(hours=1)
    ).count()

    slot_sisa = max(0, 5 - active_boost_count)

    session["email"] = user.email
    
    ram_upgrade_active = (
        user.ram_upgrade_start is not None and
        user.ram_upgrade_end is not None and
        user.ram_upgrade_end > datetime.utcnow()
    )

    return render_template(
        "Panel-Page/account_details.html",
        account=account,
        boost_used=boost_used,
        remaining_time=remaining_time,
        remaining_daily_seconds=remaining_daily_seconds,
        slot_sisa=slot_sisa,
        ram_upgrade_active=ram_upgrade_active
    )

@app.route("/panel/detail/noads")
def detail_akun_noads():
    email = request.args.get("email")
    username = request.args.get("username")
    panel_id = request.args.get("panel_id")
    
    resp = check_maintenance()
    if resp:
        return resp

    if not email or not username:
        flash("Invalid Account Data.", "error")
        return redirect("/dashboard")
        
    if not panel_id or panel_id not in PANELS:
        panel_id = next(iter(PANELS.keys()))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "error")
        return redirect("/dashboard")
        
    locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )
    if locked and user.email != admin_mail:
            logging.info(f"[DASHBOARD] Locked=True, redirect user {user.email} ke /dashboard/lock")
            return redirect(url_for("dashboard_lock"))

    account = {
        "email": user.email,
        "username": username,
        "panel_url": PANELS[panel_id]['url']  # ambil URL panel sesuai panel_id
    }

    now = datetime.utcnow()

    # ======= BOOST STATUS =======
    boost_used = False                   # Untuk info 1/1
    remaining_time = 0                  # Sisa RAM aktif (1 jam)
    remaining_daily_seconds = 0         # Sisa limit harian boost

    # Cek durasi boost RAM aktif (1 jam)
    if user.last_boost and (now - user.last_boost) < timedelta(hours=1):
        remaining_time = int((user.last_boost + timedelta(hours=1) - now).total_seconds())

    # Cek limit harian (1x per 24 jam)
    if user.last_boost_used and (now - user.last_boost_used) < timedelta(hours=24):
        boost_used = True
        remaining_daily_seconds = int((user.last_boost_used + timedelta(hours=24) - now).total_seconds())
        
        # Hitung slot boost aktif saat ini
    now = datetime.utcnow()
    active_boost_count = User.query.filter(
    User.last_boost != None,
    (now - User.last_boost) < timedelta(hours=1)
     ).count()

    slot_sisa = max(0, 5 - active_boost_count)

    # Simpan email untuk dipakai saat POST boost
    session["email"] = user.email
    
    ram_upgrade_active = (
        user.ram_upgrade_start is not None and
        user.ram_upgrade_end   is not None and
        user.ram_upgrade_end > datetime.utcnow()
    )

    return render_template(
    "Panel-Page/account_details_noads.html",
    account=account,
    boost_used=boost_used,
    remaining_time=remaining_time,
    remaining_daily_seconds=remaining_daily_seconds,
    slot_sisa=slot_sisa,
    ram_upgrade_active=ram_upgrade_active
)
    
@app.route("/boost-ram", methods=["POST"])
def boost_ram():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"success": False, "message": "User not found."})

    panel_id = str(user.serverid) if user.serverid else None
    if not panel_id or panel_id not in PANELS:
        return jsonify({"success": False, "message": f"Invalid panel ID: {panel_id}"})

    panel_url = PANELS[panel_id]["url"]
    api_key   = PANELS[panel_id]["api_key"]

    now = datetime.utcnow()

    # Limit harian boost (1x / 24 jam)
    if user.last_boost_used and (now - user.last_boost_used) < timedelta(hours=24):
        return jsonify({
            "success": False,
            "message": "The boost limit is only once per 24 hours. Please try again tomorrow."
        })

    # Cek slot boost aktif (maks 5)
    active_boosts = User.query.filter(
        User.last_boost != None,
        (now - User.last_boost) < timedelta(hours=1)
    ).count()

    if active_boosts >= 5:
        return jsonify({
            "success": False,
            "message": "Boost slot is full (5/5). Please try again later."
        })

    # Ambil server user
    server_data = Server.query.filter_by(user_id=user.id).first()
    if not server_data:
        return jsonify({"success": False, "message": f"Server not found on {panel_id}."})

    # Ambil allocation ID aktif langsung dari panel
    get_url = f"{panel_url}/api/application/servers/{server_data.id}"
    headers_get = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    try:
        res = requests.get(get_url, headers=headers_get)
        res.raise_for_status()
        allocation_id = res.json()["attributes"]["allocation"]
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to get active allocation: {e}"})

    # Payload update RAM
    patch_url = f"{panel_url}/api/application/servers/{server_data.id}/build"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "allocation": int(allocation_id),  # ✅ Harus dikirim, ambil dari API
        "limits": {
            "memory": 1536,  # 1.5 GB
            "swap": 0,
            "disk": int(user.disk),
            "io": 500,
            "cpu": int(user.cpu)
        },
        "feature_limits": {
            "databases": 1,
            "allocations": 1,
            "backups": 1
        }
    }

    # Kirim patch ke panel
    try:
        response = requests.patch(patch_url, headers=headers, json=payload)
        if not response.ok:
            return jsonify({
                "success": False,
                "message": f"⚠️ RAM boost failed ({response.status_code}): {response.text}"
            })
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"⚠️ RAM boost failed: {e}"})

    # Update waktu boost di db
    user.last_boost = now
    user.last_boost_used = now
    user.boostserver = 1
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"✅ RAM successfully upgraded to 1.5 GB on {panel_id} for 1 hour!"
    })

@app.route("/panel/upgrade/ram", methods=["GET"])
def upgrade_ram_page():
    resp = check_maintenance()
    if resp:
        return resp

    user = User.query.get(session["user_id"])
    if not user:
        return redirect("/signup")

    if user.server < 1:
        return redirect("/dashboard?noserver=success")

    ram_boost_active = user.boostserver == 1

    return render_template(
        "Panel-Page/upgrade_ram.html",
        coin=user.coin,
        ram_boost_active=ram_boost_active,
        ram_upgrade_start=user.ram_upgrade_start,
        ram_upgrade_end=user.ram_upgrade_end
    )

@app.route("/panel/upgrade/ram/start", methods=["POST"])
def upgrade_ram():
    try:
        # ================= AUTH =================
        if "email" not in session:
            return jsonify({
                "success": False,
                "message": "User is not logged in."
            }), 401

        user = User.query.filter_by(email=session["email"]).first()
        if not user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        # ================= PANEL =================
        panel_id = str(user.serverid) if user.serverid else None
        if panel_id not in PANELS:
            return jsonify({
                "success": False,
                "message": f"Invalid panel ID: {panel_id}"
            }), 400

        panel = PANELS[panel_id]

        # ================= LOCK ACTIVE UPGRADE =================
        now = datetime.utcnow()
        if user.ram_upgrade_end and user.ram_upgrade_end > now:
            return jsonify({
                "success": False,
                "message": "You've already upgraded RAM. Please wait until it expires."
            }), 403

        # ================= INPUT =================
        data = request.get_json(silent=True) or {}
        try:
            ram = int(data.get("ram", 0))
            durasi = int(data.get("durasi", 0))
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "Invalid data format."
            }), 400

        if ram not in (1, 2, 3, 4, 5) or durasi not in (3, 5, 7):
            return jsonify({
                "success": False,
                "message": "Invalid RAM or duration selection."
            }), 400

        # ================= PRICE =================
        harga_coin = {
            3: {1: 0,   2: 100, 3: 150, 4: 200, 5: 250},
            5: {1: 50,  2: 150, 3: 190, 4: 310, 5: 510},
            7: {1: 100, 2: 200, 3: 250, 4: 450, 5: 650},
        }

        harga = harga_coin.get(durasi, {}).get(ram)
        if harga is None:
            return jsonify({
                "success": False,
                "message": "Invalid price configuration."
            }), 400

        if user.coin < harga:
            return jsonify({
                "success": False,
                "message": "Not enough coins."
            }), 403

        # ================= SERVER =================
        server = Server.query.filter_by(user_id=user.id).first()
        if not server:
            return jsonify({
                "success": False,
                "message": "Server not found."
            }), 404

        # ================= PANEL REQUEST =================
        url = f"{panel['url']}/api/application/servers/{server.id}/build"

        headers = {
            "Authorization": f"Bearer {panel['api_key']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        payload = {
            "allocation": server.allocation_id,
            "memory": ram * 1024,  # MB (WAJIB)
            "swap": 0,
            "disk": server.disk,
            "io": 500,
            "cpu": server.cpu,
            "threads": None,
            "feature_limits": {
                "databases": 1,
                "backups": 1,
                "allocations": 1
            }
        }

        res = requests.patch(url, headers=headers, json=payload, timeout=10)

        if not res.ok:
            return jsonify({
                "success": False,
                "message": "Failed to apply RAM upgrade on panel.",
                "panel_status": res.status_code
            }), 502

        # ================= SAVE =================
        user.coin -= harga
        user.ram = ram * 1024
        user.ram_upgrade_start = now
        user.ram_upgrade_end = now + timedelta(days=durasi)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"RAM upgraded to {ram} GB for {durasi} days.",
            "coin_now": user.coin,
            "redirect_url": "/dashboard?upram=success"
        })

    except Exception as e:
        app.logger.exception("Upgrade RAM failed")
        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

# Route halaman form
@app.route("/panel/set-serverid", methods=["POST"])
def panel_set_serverid():
    try:
        # ambil email dari query string
        email = request.args.get("email")
        if not email:
            return {"success": False, "message": "Email missing"}, 400

        user = User.query.filter_by(email=email).first()
        if not user:
            app.logger.error(f"❌ User dengan email {email} tidak ditemukan")
            return {"success": False, "message": "User not found"}, 404

        # ambil panel_id dari form atau JSON
        panel_id = request.form.get("panel_id") or (request.json.get("panel_id") if request.is_json else None)
        if not panel_id:
            return {"success": False, "message": "Panel ID missing"}, 400

        if panel_id not in PANELS:
            return {"success": False, "message": f"Invalid panel {panel_id}"}, 400

        # update serverid user
        user.serverid = panel_id
        db.session.commit()

        app.logger.info(f"✅ User {user.id} set serverid = {panel_id}")
        return {"success": True, "message": f"Serverid set to {panel_id}"}

    except Exception as e:
        app.logger.exception("🔥 Error di /panel/set-serverid")
        return {"success": False, "message": f"Internal error: {str(e)}"}, 500
    
@app.route("/panel/create-user", methods=["POST"])
def create_ptero_user():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "msg": "Email required"}), 400

    # Kalau session kosong → cari user berdasarkan email
    if not session.get("user_id"):
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
            print(f"[DEBUG] Auto-create user {email} dengan id={user.id}")

        session["user_id"] = user.id
        print(f"[DEBUG] Auto-assign session user_id={user.id}")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"success": False, "msg": "User not found"}), 404

    panel_id = str(user.serverid) if user.serverid else "server1"
    username = user.email.split("@")[0]

    ptero_user = create_user(panel_id, user.email, username)
    if ptero_user and "id" in ptero_user:
        user.ptero_id = ptero_user["id"]
        db.session.commit()
        return jsonify({"success": True, "id": user.ptero_id})
    else:
        return jsonify({"success": False, "msg": "Failed to create Ptero user"}), 500

@app.route("/panel/create", methods=["GET"])
def panel_create_get():
    if not session.get("user_id"):
        flash("Login first!", "error")
        return redirect("/signup")

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect("/signup")
        
    resp = check_maintenance()
    if resp:
        return resp

    session.modified = True

    panel_id = str(user.serverid) if user.serverid else "server1"
    if not panel_id or panel_id not in PANELS:
        flash("Panel tidak valid.", "error")
        return redirect("/dashboard")

    # ✅ FIX: ip_addr HARUS DI-DEFINISIKAN DI SINI
    ip_addr = get_client_ip()

    # Cek limit IP
    if ip_addr:
        ip_users = User.query.filter(
            User.ip_address == ip_addr,
            User.id != user.id
        ).all()

        total_ip = len(ip_users)
        if total_ip >= 3:
            flash("❌ Pembuatan server diblokir: perangkat/IP ini sudah dipakai 3x oleh user lain yang punya server.", "error")
            return redirect("/dashboard")

    # ---- Jika user sudah punya server ----
    if user.server == 1:
        username = user.email.split("@")[0]
        flash("You already have a server!", "has_server")
        return redirect(f"/panel/detail?email={user.email}&username={username}&panel_id={panel_id}")

    # ---- Wizard untuk create server ----
    if user.iklan == 1:
        if not user.iklan_expiry or datetime.utcnow() <= user.iklan_expiry:
            session["sudah_buka_create"] = True
            panels = [{"id": k, "name": k.capitalize()} for k in PANELS.keys()]

            response = make_response(render_template(
                "Panel-Page/pterodactyl.html",
                panel_id=panel_id,
                panels=panels,
                user=user,
                telegrambotlink=telegrambotlink,
                whatsapp_number=whatsapp_number
            ))
            response.set_cookie(
                "csrf_token",
                generate_csrf(),
                samesite="Lax",
                secure=True
            )
            return response

        # reset iklan jika kadaluarsa
        user.iklan = 0
        user.iklan_expiry = None
        db.session.commit()

    # ---- Token ----
    email = request.args.get("email")
    token = request.args.get("token")
    ts = request.args.get("ts")

    if not all([email, token, ts]):
        flash("Incomplete token link.", "error")
        return redirect("/dashboard")

    try:
        ts_int = int(ts)
    except:
        flash("Invalid timestamp.", "error")
        return redirect("/dashboard")

    secret = "ganti_secretmu"
    expected = sha256(f"{email}:{secret}:{ts}".encode()).hexdigest()
    now = int(datetime.utcnow().timestamp())

    if token != expected or abs(now - ts_int) > 60:
        flash("Token is invalid or expired.", "error")
        return redirect("/dashboard")

    session["sudah_buka_create"] = True
    panels = [{"id": k, "name": k.capitalize()} for k in PANELS.keys()]

    response = make_response(render_template(
        "Panel-Page/pterodactyl.html",
        panel_id=panel_id,
        panels=panels,
        user=user,
        telegrambotlink=telegrambotlink,
        whatsapp_number=whatsapp_number
    ))
    response.set_cookie(
        "csrf_token",
        generate_csrf(),
        samesite="Lax",
        secure=True
    )
    return response

@app.route("/panel/create", methods=["POST"])
def panel_create_post():
    if not session.get("user_id"):
        flash("Login First !", "error")
        return redirect("/signup")

    if not session.get("sudah_buka_create"):
        flash("Invalid form access. Retry from dashboard..", "error")
        return redirect("/dashboard")

    session.pop("sudah_buka_create", None)

    user = User.query.get(session["user_id"])
    if not user:
        flash("User not found.", "error")
        return redirect("/signup")

    # Ambil panel_id dari user
    panel_id = str(user.serverid) if user.serverid else None
    if not panel_id or panel_id not in PANELS:
        flash("Panel tidak valid.", "error")
        return redirect("/dashboard")

    # Jika user sudah punya server → redirect ke detail
    if user.server == 1:
        username = user.email.split("@")[0]
        return redirect(f"/panel/detail?email={user.email}&username={username}&panel_id={panel_id}")

    # Cek captcha
    captcha_token = request.form.get("h-captcha-response")
    if not captcha_token or not verify_hcaptcha(captcha_token):
        flash("Captcha verification failed.", "error")
        return redirect("/panel/create")

    # Data dari form
    server_name = request.form.get("server_name")
    egg_id = request.form.get("egg")
    node_id = request.form.get("node")

    if not all([server_name, egg_id, node_id]):
        flash("Incomplete data", "error")
        return redirect("/panel/create")

    # 2️⃣ Ambil spesifikasi server dari db
    server = ServerSpec.query.filter_by(id=panel_id).first()
    if not server:
        flash("Server spec tidak ditemukan!", "error")
        return redirect("/panel/create")

    # 3️⃣ Buat server di Pterodactyl
    username = user.email.split("@")[0]
    p_user = get_ptero_user(user.email, panel_id)
    success = create_server(
        panel_id,
        user_id=p_user["id"],
        name=server_name,
        egg_id=int(egg_id),
        node_id=int(node_id),
        cpu=server.cpu,
        ram=server.ram,
        disk=server.disk
    )

    if not success or "attributes" not in success:
        flash("Failed to create server.", "error")
        return redirect("/panel/create")

    # 🔎 Polling server agar benar-benar siap
    server_id = success["attributes"]["id"]
    server_ready = None
    url_server = f"{PANELS[panel_id]['url']}/api/application/servers/{server_id}"

    for attempt in range(5):  # max 10 detik
        try:
            resp = requests.get(url_server, headers=get_headers(panel_id))
            if resp.status_code == 200:
                server_ready = resp.json()["attributes"]
                logging.info(f"[{panel_id}] Server {server_id} siap setelah {attempt+1}x cek")
                break
        except Exception as e:
            logging.warning(f"[{panel_id}] Cek server gagal attempt {attempt+1}: {e}")
        time.sleep(2)

    if not server_ready:
        flash("Server created but not ready yet. Please wait a moment.", "warning")
        return redirect("/dashboard")

    # 4️⃣ Simpan server ke db
    data = server_ready
    server_entry = Server(
        id=data["id"],
        serverid=panel_id,
        name=server_name,
        uuid=data["uuid"],
        user_id=user.id,
        server=1,
        cpu=server.cpu,
        ram=server.ram,
        disk=server.disk
    )
    db.session.merge(server_entry)

    # Update data user
    user.server = 1
    user.serverid = panel_id
    user.cpu = server.cpu
    user.ram = server.ram
    user.disk = server.disk
    user.iklan = 0
    user.iklan_expiry = None
    
    mark_trial(user)

    # Reward user
    if not user.create_mission_rewarded:
        user.coin += 20
        user.create_mission_rewarded = True

    # Referral
    if user.referred_by:
        log_referral_activity(user, "create_server")

    db.session.commit()

    flash("Server Created Successfully!", "server_created")
    return redirect(f"/panel/detail?email={user.email}&username={username}&panel_id={panel_id}")
    
@app.route("/api/getdata/<email>", methods=["GET"])
def get_data(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    servers = Server.query.filter_by(user_id=user.id).all()
    server_list = [{
        "uuid": s.uuid,
        "name": s.name,
        "cpu": s.cpu,
        "ram": s.ram,
        "disk": s.disk,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else None
    } for s in servers]

    # Ambil data server pertama (jika ada)
    first_server = servers[0] if servers else None

    return jsonify({
        "id": user.id,
        "username": user.nama,
        "is_banned": user.is_banned,
        "email": user.email,
        "coins": user.coin,
        "server": user.server,
        "cpu": user.cpu,
        "ram": user.ram,
        "disk": user.disk,
        "servers": server_list
    }), 200
    
@app.route("/api/create_server", methods=["POST"])
def api_create_server():
    data = request.json
    email = data.get("email")
    server_name = data.get("server_name")
    egg_id = data.get("egg_id")
    node_id = data.get("node_id")

    if not all([email, server_name, egg_id, node_id]):
        return jsonify({"error": "Incomplete data"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Ambil panel_id dari user
    panel_id = str(user.serverid) if user.serverid else None
    if not panel_id or panel_id not in PANELS:
        flash("Panel tidak valid.", "error")
        return redirect("/dashboard")

    # kalau sudah punya server → tolak
    if user.server == 1:
        return jsonify({"error": "User already has a server"}), 400

    # Ambil spesifikasi default dari database
    server_spec = ServerSpec.query.filter_by(id=panel_id).first()
    if not server_spec:
        return jsonify({"error": "Server spec not configured"}), 500
        
    ip_addr = get_client_ip()

    if ip_addr:
           ip_users = User.query.filter(
           User.ip_address == ip_addr,
           User.id != user.id
             ).all()

           total_ip = len(ip_users)
           if total_ip >= 3:
              flash("❌ Pembuatan server diblokir: perangkat/IP ini sudah dipakai 3x oleh user lain yang punya server.", "error")
              return redirect("/dashboard")
        
    # Buat server di Pterodactyl
    username = user.email.split("@")[0]
    p_user = get_ptero_user(user.email, panel_id)
    success = create_server(
        panel_id,
        user_id=p_user["id"],
        name=server_name,
        egg_id=int(egg_id),
        node_id=node_id,
        cpu=server_spec.cpu,
        ram=server_spec.ram,
        disk=server_spec.disk
    )
    if not success or "attributes" not in success:
        return jsonify({"error": "Failed to create server"}), 500

    # Simpan ke database
    data_srv = success["attributes"]
    server_entry = Server(
        id=data_srv["id"],
        serverid=panel_id,
        name=server_name,
        uuid=data_srv["uuid"],
        user_id=user.id,
        server=1,
        cpu=server_spec.cpu,
        ram=server_spec.ram,
        disk=server_spec.disk,
    )
    db.session.merge(server_entry)

    # Update user
    user.server = 1
    user.serverid = panel_id
    user.cpu = server_spec.cpu
    user.ram = server_spec.ram
    user.disk = server_spec.disk
    
    mark_trial(user)

    # Reward user
    if not user.create_mission_rewarded:
        user.coin += 20
        user.create_mission_rewarded = True

    # Referral
    if user.referred_by:
        log_referral_activity(user, "create_server")

    db.session.commit()

    return jsonify({
        "status": "success",
        "uuid": data_srv["uuid"],
        "server_name": server_name,
    })
    
@app.route("/miniapp")
def miniapp():
    email = request.args.get("email")
    if not email:
        return "❌ Email tidak diberikan.", 400
        
    locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )
    if locked and user.email != admin_mail:
            logging.info(f"[DASHBOARD] Locked=True, redirect user {user.email} ke /dashboard/lock")
            return redirect(url_for("dashboard_lock"))

    # cek user berdasarkan email
    user = User.query.filter_by(email=email).first()
    panels = [{"id": k, "name": k.capitalize()} for k in PANELS.keys()]
    if not user:
        return "❌ Email tidak ditemukan. Silakan daftar dulu di website.", 404
        
    resp = check_maintenance()
    if resp:
        return resp
        
    panel_id = str(user.serverid) if user.serverid else "server1"
    if not panel_id or panel_id not in PANELS:
        flash("Panel tidak valid.", "error")
        return redirect("/dashboard")
        
    if user.server == 1:
        username = user.email.split("@")[0]
        return redirect(f"/panel/detail/noads?email={user.email}&username={username}&panel_id={panel_id}")

    return render_template("Panel-Page/pterodactyl_miniapp.html", user=user, panels=panels, panel_id=panel_id)
    
@app.route("/miniapp/paneldetail")
def miniapp_paneldetail():
    email = request.args.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        flash("Email tidak ditemukan.", "error")
        return redirect("/dashboard")

    panel_id = str(user.serverid) if user.serverid else "server1"

    if not panel_id or panel_id not in PANELS:
        flash("Panel tidak valid.", "error")
        return redirect("/dashboard")

    username = user.email.split("@")[0]

    return redirect(f"/panel/detail/noads?email={user.email}&username={username}&panel_id={panel_id}")

@app.route("/main/miniapp")
def miniapp_main():
    email = request.args.get("email")
    if not email:
        return "❌ Email tidak diberikan.", 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return "❌ Email tidak ditemukan. Silakan daftar dulu di website.", 404

    # set session user_id
    session["user_id"] = user.id

    locked, auto_locked, manual_lock, force_unlock, countdown_days, countdown_seconds = (
        calculate_dashboard_lock()
    )
    if locked and user.email != admin_mail:
        logging.info(f"[DASHBOARD] Locked=True, redirect user {user.email} ke /dashboard/lock")
        return redirect(url_for("dashboard_lock"))

    resp = make_response(render_template("Panel-Page/pterodactyl_main_miniapp.html", user=user))

    device_id = get_or_create_device_id(resp)
    ip_addr = get_client_ip()

    user.device_id = device_id
    user.ip_address = ip_addr
    db.session.commit()

    if check_maintenance():
        return check_maintenance()

    return render_template("Panel-Page/pterodactyl_main_miniapp.html", user=user)
    
@app.route("/panel/backup")
def backup_page():
    if "user_id" not in session:
        return redirect("/signup")

    user = User.query.get(session["user_id"])
    if not user:
        return redirect("/signup")
        
    resp = check_maintenance()
    if resp:
        return resp

    panel_id = str(user.serverid) if user.serverid else None
    db.session.refresh(user)

    has_files = False
    no_server = False

    p_user = get_ptero_user(user.email, panel_id)
    if not p_user or "id" not in p_user:
        no_server = True
    else:
        servers = get_servers_by_userid(p_user["id"], panel_id)
        if not servers:
            no_server = True
        else:
            uuid = servers[0]["attributes"]["uuid"]
            files = list_files(panel_id, uuid, "/")
            if files.get("data"):
                has_files = True

    # --- serializable user data untuk template/JS ---
    user_data = {
        "id": user.id,
        "email": user.email,
        # pastikan nama field ini sama dengan yang dipakai di template
        "server": getattr(user, "server", 0),
        "serverid": getattr(user, "serverid", None),
        "auto_backup_enabled": bool(user.auto_backup_enabled)
    }

    return render_template(
        "Panel-Page/backup_server.html",
        user_email=user.email,
        user_data=user_data,
        last_backup=user.last_backup,
        next_backup=user.next_backup,
        has_files=has_files,
        auto_backup_enabled=user.auto_backup_enabled,
        no_server=no_server
    )

@app.route("/list-files")
def list_files_route():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "Email tidak ditemukan"}), 400

    user = User.query.filter_by(email=email).first()
    panel_id = str(user.serverid) if user.serverid else None

    p_user = get_ptero_user(email, panel_id)
    if not p_user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    servers = get_servers_by_userid(p_user["id"], panel_id)
    if not servers:
        return jsonify({"warning": "Server kosong, tidak ada file yang bisa dibackup."}), 200

    uuid = servers[0]["attributes"]["uuid"]
    files = list_files(panel_id, uuid, "/")

    if not files.get("data"):
        return jsonify({"warning": "Server kosong, tidak ada file yang bisa dibackup."}), 200

    file_list = []
    for f in files["data"]:
        file_list.append({
            "name": f["attributes"]["name"],
            "type": "File" if f["attributes"]["is_file"] else "Folder",
            "size": f["attributes"]["size"]
        })

    return jsonify(file_list)

@app.route("/backup", methods=["POST"])
def backup():
    data = request.get_json(silent=True) or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email tidak ditemukan"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    # ✅ RESET STATUS
    user.is_backup_mega = False
    user.mega_link = None
    db.session.commit()

    panel_id = str(user.serverid)

    t = Thread(
        target=trigger_backup_process,
        args=(email, panel_id)
    )
    t.start()

    return jsonify({
        "status": "processing",
        "email": email
    }), 202

@app.route("/upload-mega", methods=["POST"])
def upload_mega_route():
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email wajib"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    panel_id = str(user.serverid) if user.serverid else None

    p_user = get_ptero_user(email, panel_id)
    if not p_user:
        return jsonify({"error": "User panel tidak ditemukan"}), 404

    servers = get_servers_by_userid(p_user["id"], panel_id)
    if not servers:
        return jsonify({"error": "Server tidak ditemukan"}), 404

    uuid = servers[0]["attributes"]["uuid"]
    filename = f"backup_{email}.zip"

    # ================================
    # 1️⃣ REQUEST ZIP KE ZIP API
    # ================================
    try:
        r_zip = requests.post(
            f"{MEGA_API}/build/kocheng/backup",
            json={
                "email": email,
                "panel_id": panel_id,
                "uuid": uuid
            },
            timeout=300
        )
    except Exception as e:
        return jsonify({
            "error": "Gagal menghubungi ZIP API",
            "detail": str(e)
        }), 500

    if r_zip.status_code != 200:
        return jsonify({
            "error": "ZIP API gagal membuat backup",
            "detail": r_zip.text
        }), 500

    zip_buffer = io.BytesIO(r_zip.content)
    zip_buffer.seek(0)

    # ================================
    # 2️⃣ UPLOAD KE MEGA API (RAILWAY)
    # ================================
    files = {
        "file": (filename, zip_buffer, "application/zip")
    }

    try:
        r = requests.post(
            f"{MEGA_API}/mega/kocheng/upload",
            files=files,
            timeout=300
        )
    except Exception as e:
        user.is_backup_mega = False
        db.session.commit()
        return jsonify({
            "error": "Gagal menghubungi MEGA API",
            "detail": str(e)
        }), 500

    if r.status_code != 200:
        user.is_backup_mega = False
        db.session.commit()
        return jsonify({
            "error": "Gagal upload ke Railway",
            "detail": r.text
        }), 500

    # ================================
    # 3️⃣ UPDATE DATABASE
    # ================================
    user.is_backup_mega = True
    user.last_filename = filename
    db.session.commit()

    return jsonify({
        "message": "Upload berhasil",
        "filename": filename
    })

@app.route("/api/backup-finished", methods=["POST"])
def backup_finished():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    filename = data.get("filename")
    mega_link = data.get("mega_link")

    if not email or not mega_link:
        return jsonify({"error": "data tidak lengkap"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404

    user.is_backup_mega = True
    user.last_filename = filename
    user.mega_link = mega_link
    db.session.commit()

    print("✅ Backup selesai diterima di Control Server")
    return jsonify({"status": "ok"}), 200
    
@app.route("/restore-mega", methods=["GET"])
def restore_mega():
    filename = request.args.get("filename")

    if not filename:
        return jsonify({"error": "filename wajib"}), 400

    mega_url = f"{MEGA_API}/mega/kocheng/download?filename={filename}"

    try:
        response = requests.get(mega_url, stream=True)
        if response.status_code != 200:
            return jsonify({"error": "Gagal download dari Mega", "detail": response.text}), 500

        return Response(
            response.iter_content(chunk_size=8192),
            mimetype="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        return jsonify({"error": "Error streaming Mega", "detail": str(e)}), 500

@app.route("/check-mega")
def check_mega():
    email = request.args.get("email")
    if not email:
        return jsonify({"has_backup": False, "error": "Email wajib diisi"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"has_backup": False, "error": "User tidak ditemukan"}), 404

    filename = f"backup_{email}.zip"

    # Panggil API Mega internal
    try:
        api_url = f"{MEGA_API}/mega/kocheng/check?filename={filename}"
        response = requests.get(api_url)
    except Exception as e:
        return jsonify({
            "has_backup": False,
            "error": f"Gagal menghubungi API Mega: {str(e)}"
        }), 500

    # Parse response API
    if response.status_code != 200:
        return jsonify({
            "has_backup": False,
            "error": f"API Mega error: {response.text}"
        }), 500

    data = response.json()

    # Jika Mega bilang ada
    if data.get("has_backup"):
        user.is_backup_mega = True
        user.last_filename = filename
        db.session.commit()
        return jsonify({"has_backup": True, "filename": filename})

    # Jika tidak ada
    user.is_backup_mega = False
    db.session.commit()
    return jsonify({"has_backup": False})

@app.route("/toggle-auto-backup", methods=["POST"])
def toggle_auto_backup():
    if "user_id" not in session:
        return "Unauthorized", 401

    user = User.query.get(session["user_id"])
    enabled = request.json.get("enabled", False)
    user.auto_backup_enabled = enabled
    db.session.commit()

    if enabled:
        backup_and_upload(user)

    return jsonify({"status": "ok", "enabled": enabled})
    
@app.route("/api/panels", methods=["GET"])
def get_panels():
    secret = request.headers.get("X-CONTROL-KEY")

    if secret != "KUNCI_WEB_A":
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify(PANELS)
    
@app.route("/api/ram-status")
def ram_status():
    user = User.query.get(session["user_id"])

    allowed, remaining = can_use_special_ram(user)

    return jsonify({
        "special_allowed": allowed,
        "remaining_seconds": int(remaining.total_seconds()) if remaining else 0
    })
    
@app.route("/internal/reset-boost", methods=["POST"])
def internal_reset_boost():
    from web1.scheduler_tasks import run_reset_ram_boost
    run_reset_ram_boost()
    return {"status": "ok", "job": "reset_boost"}, 200

@app.route("/internal/reset-upgrade", methods=["POST"])
def internal_reset_upgrade():
    from web1.scheduler_tasks import run_reset_ram_upgrade
    run_reset_ram_upgrade()
    return {"status": "ok", "job": "reset_upgrade"}, 200

@app.route("/internal/weekly-backup", methods=["POST"])
def internal_weekly_backup():
    from web1.scheduler_tasks import weekly_backup
    weekly_backup()
    return {"status": "ok", "job": "weekly_backup"}, 200

@app.route("/internal/shutdown-inactive", methods=["POST"])
def internal_shutdown_inactive():
    from web1.scheduler_tasks import run_shutdown_inactive_servers
    run_shutdown_inactive_servers()
    return {"status": "ok", "job": "shutdown_inactive"}, 200

@app.route("/internal/daily-broadcast", methods=["POST"])
def internal_daily_broadcast():
    from web1.scheduler_tasks import run_daily_broadcast
    run_daily_broadcast()
    return {"status": "ok", "job": "daily_broadcast"}, 200
    
@app.route("/internal/sync-coin-github", methods=["POST"])
def sync_coin_github():
    try:
        from web1.scheduler_tasks import sync_coin_to_github
        sync_coin_to_github()
        return jsonify({
            "status": "success",
            "message": "Coin berhasil disinkronkan ke GitHub"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
if __name__ == "__main__":
    app.run()