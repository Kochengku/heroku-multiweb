# scheduler_runner.py
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

if len(sys.argv) < 2:
    print("Gunakan format:")
    print("python scheduler_runner.py nama_job")
    sys.exit(1)

job = sys.argv[1]

# ✅ PAKAI WAKTU INDONESIA (WIB)
now = datetime.now(ZoneInfo("Asia/Jakarta"))

# ✅ AMBIL SEMUA YANG ADA, JANGAN PAKSA
try:
    from web1.app import weekly_backup
except:
    weekly_backup = None

try:
    from web1.app import run_daily_broadcast
except:
    run_daily_broadcast = None

try:
    from web3.app import run_process_update_queue
except:
    run_process_update_queue = None

try:
    from web1.app import run_reset_ram_boost
except:
    run_reset_ram_boost = None

try:
    from web1.app import run_reset_ram_upgrade
except:
    run_reset_ram_upgrade = None

try:
    from web1.app import run_shutdown_inactive_servers
except:
    run_shutdown_inactive_servers = None


print(f"[SCHEDULER] Job: {job} | Waktu WIB: {now}")

# =========================
# ✅ ROUTING + FILTER WAKTU WIB
# =========================

# ✅ 1 MINGGU 1X → MINGGU JAM 03:00 WIB
if job == "weekly_backup" and weekly_backup:
    if now.weekday() == 6 and now.hour == 3:
        print("✅ EKSEKUSI weekly_backup")
        weekly_backup()
    else:
        print("⏭️ Skip weekly_backup (belum waktunya)")

# ✅ TIAP HARI JAM 07:00 PAGI WIB
elif job == "daily_broadcast" and run_daily_broadcast:
    if now.hour == 7:
        print("✅ EKSEKUSI daily_broadcast")
        run_daily_broadcast()
    else:
        print("⏭️ Skip daily_broadcast (belum jam 7 pagi WIB)")

# ✅ 24 JAM 1X → JAM 02:00 WIB
elif job == "shutdown_inactive" and run_shutdown_inactive_servers:
    if now.hour == 2:
        print("✅ EKSEKUSI shutdown_inactive")
        run_shutdown_inactive_servers()
    else:
        print("⏭️ Skip shutdown_inactive (belum jam 2 pagi WIB)")

# ✅ BEBAS SETIAP 10 MENIT
elif job == "update_queue" and run_process_update_queue:
    print("✅ EKSEKUSI update_queue")
    run_process_update_queue()

elif job == "reset_boost" and run_reset_ram_boost:
    print("✅ EKSEKUSI reset_boost")
    run_reset_ram_boost()

elif job == "reset_upgrade" and run_reset_ram_upgrade:
    print("✅ EKSEKUSI reset_upgrade")
    run_reset_ram_upgrade()

else:
    print("[ERROR] Job tidak ada atau fungsi tidak ditemukan:", job)