import os
import subprocess
from datetime import datetime

from flask import request
from werkzeug.wrappers import Response

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

REPO_PATH = os.getcwd()

# folder yang mau di-backup
TARGETS = [
    "web1/instance",
    "web3/instance",
]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # set via Heroku
GITHUB_USER = "Kochengku"
REPO_NAME = "heroku-multiweb"


# ==========================
# BACKUP FUNCTION
# ==========================

def backup_job():
    print("=== BACKUP START ===")

    os.chdir(REPO_PATH)

    # Set remote pakai token biar push tidak minta password
    remote_url = (
        f"https://{GITHUB_TOKEN}:x-oauth-basic@github.com/"
        f"{GITHUB_USER}/{REPO_NAME}.git"
    )
    subprocess.run(["git", "remote", "set-url", "origin", remote_url])

    # Loop untuk setiap folder target
    for target_path in TARGETS:
        print(f"Backup folder: {target_path}")

        # git add hanya folder tersebut
        subprocess.run(["git", "add", target_path])

    # Commit
    msg = f"Auto-backup web1+web3 instance {datetime.now().isoformat()}"
    subprocess.run(["git", "commit", "-m", msg])

    # Push
    subprocess.run(["git", "push"])

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
# SCHEDULER (SETIAP 1 MENIT)
# ==========================

scheduler = BackgroundScheduler()

scheduler.add_job(
    backup_job,
    CronTrigger(minute="*/1"),  # <--- BACKUP SETIAP 1 MENIT
    id="backup_job",
    replace_existing=True
)

scheduler.start()

print("Scheduler aktif: backup setiap 1 menit untuk web1/instance & web3/instance")