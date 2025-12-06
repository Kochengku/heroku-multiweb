from datetime import datetime, timedelta
import time
import requests

# =========================
# ✅ SAFE IMPORT DARI FLASK APP
# =========================
try:
    from web1.app import app, db, User, Server, ServerSpec, PANELS
    from web1.utils import (
        broadcast_lock_notification,
        update_server_build,
        get_allocation_from_api,
        revert_ram,
        get_ptero_user,
        get_servers_by_userid,
        list_files,
        backup_and_upload,
        add_log
    )
    print("✅ Import web1.app berhasil")
except Exception as e:
    print("❌ Gagal import web1.app:", e)
    app = db = User = Server = ServerSpec = PANELS = None
    broadcast_lock_notification = None
    update_server_build = None
    get_allocation_from_api = None
    revert_ram = None
    get_ptero_user = None
    get_servers_by_userid = None
    list_files = None
    backup_and_upload = None
    add_log = None


# =========================
# ✅ DAILY BROADCAST
# =========================
def run_daily_broadcast():
    if not app:
        print("❌ App tidak siap - daily_broadcast dilewati")
        return

    with app.app_context():
        print(f"[SCHEDULER] Cek broadcast {datetime.now()}")
        if broadcast_lock_notification:
            broadcast_lock_notification()


# =========================
# ✅ PROCESS UPDATE QUEUE
# =========================
update_queue = []
update_status = "idle"

def run_process_update_queue():
    global update_queue, update_status

    if not update_queue:
        if update_status == "running":
            update_status = "done"
            if add_log:
                add_log("🎉 Semua server selesai diproses")
        return

    update_status = "running"
    batch = update_queue[:10]
    update_queue = update_queue[10:]

    if add_log:
        add_log(f"🔄 Proses {len(batch)} server (sisa {len(update_queue)} di queue)")

    for srv in batch:
        try:
            ok = update_server_build(
                srv["id"],
                srv["allocation"],
                srv["ram"],
                srv["disk"],
                srv["cpu"]
            )

            if ok and add_log:
                add_log(f"✅ Berhasil update server {srv['uuid']} (panel {srv['panel_id']})")

        except Exception as e:
            if add_log:
                add_log(f"❌ Error server {srv.get('uuid')}: {e}")


# =========================
# ✅ RESET BOOST RAM
# =========================
def run_reset_ram_boost():
    if not app:
        print("❌ App tidak siap - reset_boost dilewati")
        return

    print("[INFO] Running reset_ram_task")

    try:
        with app.app_context():
            users = User.query.filter(User.last_boost != None).all()
            now = datetime.utcnow()

            for user in users:
                try:
                    if not user.last_boost:
                        continue

                    if (now - user.last_boost) < timedelta(hours=1):
                        continue

                    panel_id = str(user.serverid) if user.serverid else None
                    server_data = Server.query.filter_by(user_id=user.id).first()
                    if not server_data:
                        continue

                    if not server_data.allocation_id:
                        allocation_id = get_allocation_from_api(panel_id, server_data.id)
                        if allocation_id:
                            server_data.allocation_id = allocation_id
                            db.session.commit()
                        else:
                            continue

                    user.boostserver = 0
                    db.session.commit()

                    serverspec = ServerSpec.query.filter_by(id=panel_id).first()
                    revert_ram(panel_id, user, server_data, serverspec.ram if serverspec else 1024)

                    user.last_boost = None
                    db.session.commit()

                except Exception as e:
                    print("[ERROR reset_boost]", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB ditutup (reset_boost)")
        except:
            pass


# =========================
# ✅ RESET UPGRADE RAM
# =========================
def run_reset_ram_upgrade():
    if not app:
        print("❌ App tidak siap - reset_upgrade dilewati")
        return

    print("[INFO] Menjalankan reset_ram_task_upgrade_ram...")

    try:
        with app.app_context():
            now = datetime.utcnow()
            users = User.query.filter(User.ram_upgrade_end != None).all()

            for user in users:
                try:
                    if now < user.ram_upgrade_end:
                        continue

                    panel_id = str(user.serverid) if user.serverid else None
                    if not panel_id or panel_id not in PANELS:
                        continue

                    server = Server.query.filter_by(user_id=user.id).first()
                    if not server:
                        continue

                    if not server.allocation_id:
                        allocation_id = get_allocation_from_api(panel_id, server.id)
                        if allocation_id:
                            server.allocation_id = allocation_id
                            db.session.commit()
                        else:
                            continue

                    serverspec = ServerSpec.query.filter_by(id=panel_id).first()

                    if revert_ram(panel_id, user, server, serverspec.ram):
                        user.ram = serverspec.ram
                        user.ram_upgrade_start = None
                        user.ram_upgrade_end = None
                        db.session.commit()

                except Exception as e:
                    print("[ERROR reset_upgrade]", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB ditutup (reset_upgrade)")
        except:
            pass


# =========================
# ✅ SHUTDOWN USER TIDAK AKTIF
# =========================
def run_shutdown_inactive_servers():
    if not app:
        print("❌ App tidak siap - shutdown dilewati")
        return

    print("[INFO] Menjalankan shutdown_inactive_servers...")

    try:
        with app.app_context():
            batas = datetime.utcnow() - timedelta(days=5)
            users = User.query.filter(User.last_login != None, User.last_login < batas).all()

            for user in users:
                try:
                    panel_id = str(user.serverid) if user.serverid else None
                    if not panel_id or panel_id not in PANELS:
                        continue

                    servers = Server.query.filter_by(user_id=user.id).all()
                    for server in servers:
                        url = f"{PANELS[panel_id]['url']}/api/application/servers/{server.id}/power"
                        headers = {
                            "Authorization": f"Bearer {PANELS[panel_id]['api_key']}",
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }

                        r = requests.post(url, headers=headers, json={"signal": "stop"})
                        if r.status_code == 204:
                            print(f"[✓] Server {server.id} dimatikan")

                except Exception as e:
                    print("[ERROR shutdown]", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB ditutup (shutdown)")
        except:
            pass


# =========================
# ✅ WEEKLY BACKUP
# =========================
def weekly_backup():
    if not app:
        print("❌ App tidak siap - weekly_backup dilewati")
        return

    try:
        with app.app_context():
            users = User.query.filter_by(auto_backup_enabled=True).all()
            print(f"[INFO] Weekly backup: {len(users)} user")

            for user in users:
                try:
                    panel_id = str(user.serverid) if user.serverid else None
                    if not panel_id:
                        user.auto_backup_enabled = False
                        db.session.commit()
                        continue

                    p_user = get_ptero_user(user.email, panel_id)
                    if not p_user:
                        user.auto_backup_enabled = False
                        db.session.commit()
                        continue

                    servers = get_servers_by_userid(p_user["id"], panel_id)
                    if not servers:
                        user.auto_backup_enabled = False
                        db.session.commit()
                        continue

                    has_files = False
                    for srv in servers:
                        uuid = srv["attributes"]["uuid"]
                        files = list_files(panel_id, uuid, "/")
                        if files and files.get("data"):
                            has_files = True
                            break

                    if not has_files:
                        user.auto_backup_enabled = False
                        db.session.commit()
                        continue

                    backup_and_upload(user)

                    user.last_backup = datetime.utcnow()
                    user.next_backup = user.last_backup + timedelta(weeks=1)
                    db.session.commit()

                except Exception as e:
                    print(f"[ERROR weekly_backup] {user.email}:", e)
                    user.auto_backup_enabled = False
                    db.session.commit()

                time.sleep(60)

    finally:
        try:
            db.session.remove()
            print("✅ DB ditutup (weekly_backup)")
        except:
            pass