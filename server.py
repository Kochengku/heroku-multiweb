import os
import base64
import requests
from datetime import datetime

from flask import request
from werkzeug.wrappers import Response
os.environ["WERKZEUG_RUN_MAIN"] = "true"
# ============== IMPORT APPS ==============
from web1.app import app as web1
from web2.app import app as web2
from web3.app import app as web3
from web4.app import app as web4

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# ==========================
# CONFIG
# ==========================

TARGETS = [
    "web1/instance",
    "web3/instance",
]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = "Kochengku"
GITHUB_REPO = "heroku-multiweb"


# ==========================
# GITHUB UPLOAD FUNCTION
# ==========================

def github_upload(local_path, github_path):

    with open(local_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_path}"

    # cek apakah file sudah ada
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": f"Backup {github_path}",
        "content": encoded,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    r = requests.put(
        url,
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json=data
    )

    print("UPLOAD", github_path, "=>", r.status_code)
    return r.status_code in (200, 201)


# ==========================
# BACKUP JOB
# ==========================

def backup_job():
    print("=== BACKUP START ===")

    for folder in TARGETS:
        print("Backup folder:", folder)

        if not os.path.isdir(folder):
            print("Folder tidak ditemukan:", folder)
            continue

        for root, dirs, files in os.walk(folder):
            for file in files:
                local_file = os.path.join(root, file)

                # path di GitHub 100% sama seperti lokal
                github_file = local_file  # <- TERPENTING!

                github_upload(local_file, github_file)

    print("=== BACKUP DONE ===")


# ==========================
# DOMAIN DISPATCHER
# ==========================

DOMAIN_MAP = {
    "control.kocheng.biz.id": web1,
    "kocheng.biz.id": web2,
    "control.skyforgia.web.id": web3,
    "skyforgia.web.id": web4,
}

class HostDispatcher:
    def __call__(self, environ, start_response):
        host = environ.get("HTTP_HOST", "").split(":")[0].lower()

        for domain, app in DOMAIN_MAP.items():
            if domain in host:
                return app(environ, start_response)

        return Response("Domain tidak ditemukan", status=404)(environ, start_response)


app = HostDispatcher()


# ==========================
# SCHEDULER SETIAP 1 MENIT
# ==========================

scheduler = BackgroundScheduler()

scheduler.add_job(
    backup_job,
    CronTrigger(minute="*/1"),
    id="backup_job",
    replace_existing=True
)
if os.getenv("DISABLE_SCHEDULER") != "1":
    scheduler.start()

print("Scheduler aktif: backup setiap 1 menit untuk web1/instance & web3/instance")