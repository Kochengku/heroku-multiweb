import sys
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import importlib

print("========== SCHEDULER RUNNER START ==========")

# =========================
# ✅ VALIDASI ARGUMEN
# =========================
if len(sys.argv) < 2:
    print("❌ Gunakan format:")
    print("python scheduler_runner.py <nama_job>")
    sys.exit(1)

job = sys.argv[1]

# =========================
# ✅ WAKTU WIB
# =========================
now = datetime.now(ZoneInfo("Asia/Jakarta"))
print(f"[SCHEDULER] Job: {job} | Waktu WIB: {now}")

def safe_import_multi(paths, func_name):
    for path in paths:
        try:
            module = importlib.import_module(path)
            func = getattr(module, func_name)
            print(f"✅ IMPORT BERHASIL: {func_name} dari {path}")
            return func
        except Exception as e:
            print(f"⚠️ GAGAL import {func_name} dari {path}: {e}")
    print(f"❌ TOTAL GAGAL IMPORT: {func_name}")
    return None
    
run_process_update_queue = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_process_update_queue"
)

# =========================
# ✅ DOMAIN
# =========================
WEB1_URL = "https://control.kocheng.biz.id"
WEB3_URL = "https://control.skyforgia.web.id"

# =========================
# ✅ ROUTING + JAM (FULL HTTP)
# =========================

try:
    # =========================
    # ✅ WEEKLY BACKUP (MINGGU 03:00 WIB)
    # =========================
    if job == "weekly_backup_web1":
        if now.weekday() == 6 and now.hour == 3:
            print("✅ EKSEKUSI weekly_backup WEB1")
            r = requests.post(f"{WEB1_URL}/internal/weekly-backup", timeout=600)
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip weekly_backup_web1 (belum waktunya)")

    elif job == "weekly_backup_web3":
        if now.weekday() == 6 and now.hour == 3:
            print("✅ EKSEKUSI weekly_backup WEB3")
            r = requests.post(f"{WEB3_URL}/internal/weekly-backup", timeout=600)
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip weekly_backup_web3 (belum waktunya)")

    # =========================
    # ✅ DAILY BROADCAST (WEB1 ONLY - 07:00)
    # =========================
    elif job == "daily_broadcast_web1":
        if now.hour == 7:
            print("✅ EKSEKUSI daily_broadcast WEB1")
            r = requests.post(f"{WEB1_URL}/internal/daily-broadcast", timeout=120)
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip daily_broadcast_web1")

    # =========================
    # ✅ SHUTDOWN INACTIVE (02:00 WIB)
    # =========================
    elif job == "shutdown_inactive_web1":
        if now.hour == 2:
            print("✅ EKSEKUSI shutdown_inactive WEB1")
            r = requests.post(f"{WEB1_URL}/internal/shutdown-inactive", timeout=300)
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip shutdown_inactive_web1")

    elif job == "shutdown_inactive_web3":
        if now.hour == 2:
            print("✅ EKSEKUSI shutdown_inactive WEB3")
            r = requests.post(f"{WEB3_URL}/internal/shutdown-inactive", timeout=300)
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip shutdown_inactive_web3")

    # =========================
    # ✅ RESET BOOST (BEBAS)
    # =========================
    elif job == "reset_boost_web1":
        print("✅ EKSEKUSI reset_boost WEB1")
        r = requests.post(f"{WEB1_URL}/internal/reset-boost", timeout=120)
        print("✅ RESPONSE:", r.text)

    elif job == "reset_boost_web3":
        print("✅ EKSEKUSI reset_boost WEB3")
        r = requests.post(f"{WEB3_URL}/internal/reset-boost", timeout=120)
        print("✅ RESPONSE:", r.text)
        
    # =========================
    # ✅ UPLOAD JSON TO GITHUB
    # =========================
    elif job == "sync_coin_github_web1":
        if now.minute == 0:
            print("✅ EKSEKUSI sync_coin_github (1 JAM)")
            r = requests.post(
                f"{WEB1_URL}/internal/sync-coin-github",
                timeout=300
            )
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip sync_coin_github (bukan jam penuh)")
            
    elif job == "sync_coin_github_web3":
        if now.minute == 0:
            print("✅ EKSEKUSI sync_coin_github (1 JAM)")
            r = requests.post(
                f"{WEB3_URL}/internal/sync-coin-github",
                timeout=300
            )
            print("✅ RESPONSE:", r.text)
        else:
            print("⏭️ Skip sync_coin_github (bukan jam penuh)")

    # =========================
    # ✅ RESET UPGRADE (BEBAS)
    # =========================
    elif job == "reset_upgrade_web1":
        print("✅ EKSEKUSI reset_upgrade WEB1")
        r = requests.post(f"{WEB1_URL}/internal/reset-upgrade", timeout=120)
        print("✅ RESPONSE:", r.text)

    elif job == "reset_upgrade_web3":
        print("✅ EKSEKUSI reset_upgrade WEB3")
        r = requests.post(f"{WEB3_URL}/internal/reset-upgrade", timeout=120)
        print("✅ RESPONSE:", r.text)
        
    elif job == "update_queue":
        if not run_process_update_queue:
            raise Exception("Fungsi update_queue tidak tersedia")

        print("✅ EKSEKUSI update_queue")
        run_process_update_queue()

    else:
        print("❌ JOB TIDAK DIKENAL:", job)

except Exception as e:
    print("🔥 FATAL ERROR SAAT EKSEKUSI JOB:", e)

finally:
    print("✅ Scheduler selesai, exit...")
    sys.exit(0)