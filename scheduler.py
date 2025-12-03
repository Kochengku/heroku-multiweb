import os
import base64
import requests
from datetime import datetime

TARGETS = [
    "web1/instance",
    "web3/instance",
]

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = "Kochengku"
GITHUB_REPO = "heroku-multiweb"

def github_upload(local_path, github_path):
    with open(local_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{github_path}"

    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = r.json().get("sha") if r.status_code == 200 else None

    data = {
        "message": f"Backup {github_path}",
        "content": encoded,
        "branch": "main",
    }

    if sha:
        data["sha"] = sha

    r = requests.put(
        url,
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json=data
    )
    print("UPLOAD", github_path, "=>", r.status_code)


def backup_job():
    print("=== BACKUP START ===")

    for folder in TARGETS:
        if not os.path.isdir(folder):
            print("Folder tidak ditemukan:", folder)
            continue

        for root, dirs, files in os.walk(folder):
            for file in files:
                local = os.path.join(root, file)
                github = local
                github_upload(local, github)

    print("=== BACKUP DONE ===")


# RUN SCHEDULER
from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()
sched.add_job(backup_job, "cron", minute="*/1")
sched.start()