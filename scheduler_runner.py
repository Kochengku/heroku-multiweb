import sys
from datetime import datetime
from zoneinfo import ZoneInfo

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
# ✅ SAFE IMPORT DENGAN FALLBACK WEB1 -> WEB3
# =========================

def safe_import_multi(paths, func_name):
    """
    Coba import fungsi dari beberapa module secara berurutan.
    Kalau gagal semua, return None (TAPI ERROR DITAMPILKAN).
    """
    for path in paths:
        try:
            module = __import__(path, fromlist=[func_name])
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

# ✅ WEEKLY BACKUP (WEB1 & WEB3)
weekly_backup = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "weekly_backup"
)

# ✅ DAILY BROADCAST (KHUSUS WEB1)
run_daily_broadcast = safe_import_multi(
    ["web1.scheduler_tasks"],
    "run_daily_broadcast"
)

# ✅ SHUTDOWN INACTIVE (WEB1 & WEB3)
run_shutdown_inactive_servers = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_shutdown_inactive_servers"
)

# ✅ RESET BOOST (WEB1 & WEB3)
run_reset_ram_boost = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_reset_ram_boost"
)

# ✅ RESET UPGRADE (WEB1 & WEB3)
run_reset_ram_upgrade = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_reset_ram_upgrade"
)

# ✅ UPDATE QUEUE (WEB1 & WEB3)
run_process_update_queue = safe_import_multi(
    ["web1.scheduler_tasks", "web3.scheduler_tasks"],
    "run_process_update_queue"
)

# =========================
# ✅ DEBUG STATUS FUNGSI
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
    # ✅ 1 MINGGU 1X → MINGGU JAM 03:00 WIB
    if job == "weekly_backup":
        if not weekly_backup:
            raise Exception("Fungsi weekly_backup tidak tersedia")

        if now.weekday() == 6 and now.hour == 3:
            print("✅ EKSEKUSI weekly_backup")
            weekly_backup()
        else:
            print("⏭️ Skip weekly_backup (belum waktunya)")

    # ✅ TIAP HARI JAM 07:00 WIB
    elif job == "daily_broadcast":
        if not run_daily_broadcast:
            raise Exception("Fungsi daily_broadcast tidak tersedia di web ini")

        if now.hour == 7:
            print("✅ EKSEKUSI daily_broadcast")
            run_daily_broadcast()
        else:
            print("⏭️ Skip daily_broadcast (belum jam 7 pagi WIB)")

    # ✅ TIAP HARI JAM 02:00 WIB
    elif job == "shutdown_inactive":
        if not run_shutdown_inactive_servers:
            raise Exception("Fungsi shutdown_inactive tidak tersedia")

        if now.hour == 2:
            print("✅ EKSEKUSI shutdown_inactive")
            run_shutdown_inactive_servers()
        else:
            print("⏭️ Skip shutdown_inactive (belum jam 2 pagi WIB)")

    # ✅ BEBAS (SETIAP 1–10 MENIT)
    elif job == "update_queue":
        if not run_process_update_queue:
            raise Exception("Fungsi update_queue tidak tersedia")

        print("✅ EKSEKUSI update_queue")
        run_process_update_queue()

    # ✅ RESET BOOST
    elif job == "reset_boost":
        if not run_reset_ram_boost:
            raise Exception("Fungsi reset_boost tidak tersedia")

        print("✅ EKSEKUSI reset_boost")
        run_reset_ram_boost()

    # ✅ RESET UPGRADE
    elif job == "reset_upgrade":
        if not run_reset_ram_upgrade:
            raise Exception("Fungsi reset_upgrade tidak tersedia")

        print("✅ EKSEKUSI reset_upgrade")
        run_reset_ram_upgrade()

    else:
        print("❌ JOB TIDAK DIKENAL:", job)

except Exception as e:
    print("🔥 FATAL ERROR SAAT EKSEKUSI JOB:", e)

print("========== SCHEDULER RUNNER SELESAI ==========")