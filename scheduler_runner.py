import sys
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

# =========================
# ✅ SAFE IMPORT (VERSI AMAN)
# =========================
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


# =========================
# ✅ IMPORT SEMUA JOB
# =========================

weekly_backup = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "weekly_backup"
)

run_daily_broadcast = safe_import_multi(
    ["web1.scheduler_tasks"],
    "run_daily_broadcast"
)

run_shutdown_inactive_servers = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_shutdown_inactive_servers"
)

run_reset_ram_boost = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_reset_ram_boost"
)

run_reset_ram_upgrade = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_reset_ram_upgrade"
)

run_process_update_queue = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_process_update_queue"
)

# =========================
# ✅ DEBUG STATUS
# =========================
print("========== DEBUG STATUS FUNGSI ==========")
print("weekly_backup:", weekly_backup)
print("daily_broadcast:", run_daily_broadcast)
print("shutdown_inactive:", run_shutdown_inactive_servers)
print("update_queue:", run_process_update_queue)
print("reset_boost:", run_reset_ram_boost)
print("reset_upgrade:", run_reset_ram_upgrade)
print("========================================")

# =========================
# ✅ ROUTING + EKSEKUSI JOB
# =========================

try:
    # ✅ MINGGU JAM 03:00 WIB
    if job == "weekly_backup":
        if not weekly_backup:
            raise Exception("Fungsi weekly_backup tidak tersedia")

        if now.weekday() == 6 and now.hour == 3:
            print("✅ EKSEKUSI weekly_backup")
            weekly_backup()
        else:
            print("⏭️ Skip weekly_backup (belum waktunya)")

    # ✅ HARIAN JAM 07:00 WIB
    elif job == "daily_broadcast":
        if not run_daily_broadcast:
            raise Exception("Fungsi daily_broadcast tidak tersedia")

        if now.hour == 7:
            print("✅ EKSEKUSI daily_broadcast")
            run_daily_broadcast()
        else:
            print("⏭️ Skip daily_broadcast")

    # ✅ HARIAN JAM 02:00 WIB
    elif job == "shutdown_inactive":
        if not run_shutdown_inactive_servers:
            raise Exception("Fungsi shutdown_inactive tidak tersedia")

        if now.hour == 2:
            print("✅ EKSEKUSI shutdown_inactive")
            run_shutdown_inactive_servers()
        else:
            print("⏭️ Skip shutdown_inactive")

    # ✅ TIAP 1–10 MENIT
    elif job == "update_queue":
        if not run_process_update_queue:
            raise Exception("Fungsi update_queue tidak tersedia")

        print("✅ EKSEKUSI update_queue")
        run_process_update_queue()

    # ✅ RESET BOOST → JAM 01:00 WIB
    elif job == "reset_boost":
        if not run_reset_ram_boost:
            raise Exception("Fungsi reset_boost tidak tersedia")

        if now.hour == 1:
            print("✅ EKSEKUSI reset_boost")
            run_reset_ram_boost()
        else:
            print("⏭️ Skip reset_boost (belum jam 1 pagi WIB)")

    # ✅ RESET UPGRADE → JAM 01:30 WIB
    elif job == "reset_upgrade":
        if not run_reset_ram_upgrade:
            raise Exception("Fungsi reset_upgrade tidak tersedia")

        if now.hour == 1 and now.minute >= 30:
            print("✅ EKSEKUSI reset_upgrade")
            run_reset_ram_upgrade()
        else:
            print("⏭️ Skip reset_upgrade (belum jam 01:30 WIB)")

    else:
        print("❌ JOB TIDAK DIKENAL:", job)

except Exception as e:
    print("🔥 FATAL ERROR SAAT EKSEKUSI JOB:", e)

finally:
    print("✅ Scheduler selesai, exit...")
    sys.exit(0)