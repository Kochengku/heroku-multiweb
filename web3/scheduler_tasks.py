from datetime import datetime, timedelta
import time
import requests
import os
import base64
import json

# =========================
# ✅ SAFE IMPORT DARI FLASK APP
# =========================
try:
    from web3.app import (
    app,
    db,
    User,
    Server,
    ServerSpec,
    PANELS,

    update_server_build,
    get_allocation_from_api,
    revert_ram,
    get_ptero_user,
    get_servers_by_userid,
    list_files,
    backup_and_upload,
    add_log
)
    print("✅ Import web3.app berhasil")
except Exception as e:
    print("❌ Gagal import web3.app:", e)
    app = db = User = Server = ServerSpec = PANELS = None
    update_server_build = None
    get_allocation_from_api = None
    revert_ram = None
    get_ptero_user = None
    get_servers_by_userid = None
    list_files = None
    backup_and_upload = None
    add_log = None

GITHUB_API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO_SKYFORGIA")
FILE_PATH = os.getenv("GITHUB_FILE_PATH")
BRANCH = os.getenv("GITHUB_BRANCH", "main")

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# =========================
# ✅ PROCESS UPDATE QUEUE
# =========================
update_queue = []
update_status = "idle"

def run_process_update_queue():
    global update_queue, update_status

    # proses ini tidak butuh app context DB kalau semua helper siap
    if not update_queue:
        if update_status == "running":
            update_status = "done"
            if 'add_log' in globals() and add_log:
                add_log("🎉 Semua server selesai diproses")
        return

    update_status = "running"
    batch = update_queue[:10]
    update_queue = update_queue[10:]

    if 'add_log' in globals() and add_log:
        add_log(f"🔄 Proses {len(batch)} server (sisa {len(update_queue)} di queue)")

    for srv in batch:
        try:
            ok = None
            if 'update_server_build' in globals() and update_server_build:
                ok = update_server_build(
                    srv.get("id"),
                    srv.get("allocation"),
                    srv.get("ram"),
                    srv.get("disk"),
                    srv.get("cpu")
                )
            else:
                print("⚠️ update_server_build helper tidak tersedia")
                ok = False

            if ok and 'add_log' in globals() and add_log:
                add_log(f"✅ Berhasil update server {srv.get('uuid')} (panel {srv.get('panel_id')})")
            elif not ok and 'add_log' in globals() and add_log:
                add_log(f"❌ Gagal update server {srv.get('uuid')} (panel {srv.get('panel_id')})")

        except Exception as e:
            if 'add_log' in globals() and add_log:
                add_log(f"❌ Error server {srv.get('uuid')}: {e}")
            else:
                print("❌ Error server:", srv.get('uuid'), e)


# =========================
# ✅ RESET BOOST RAM
# =========================
def run_reset_ram_boost():
    print("🔥 MASUK run_reset_ram_boost()")
    try:
        with app.app_context():
            users = User.query.filter(User.last_boost != None).all()
            print("✅ User dengan last_boost:", len(users))
            now = datetime.utcnow()

            for user in users:
                try:
                    if not user.last_boost:
                        continue

                    if (now - user.last_boost) < timedelta(hours=1):
                        # belum waktunya revert karena boost belum 1 jam
                        continue

                    panel_id = str(user.serverid) if user.serverid else None
                    server_data = Server.query.filter_by(user_id=user.id).first()
                    if not server_data:
                        print(f"⚠️ Tidak ada server_data untuk user {user.id}, skip")
                        continue

                    # pastikan allocation_id
                    if not server_data.allocation_id:
                        allocation_id = get_allocation_from_api(panel_id, server_data.id)
                        if allocation_id:
                            server_data.allocation_id = allocation_id
                            db.session.commit()
                        else:
                            print(f"⚠️ Allocation tidak ditemukan untuk server {server_data.id}, skip")
                            continue

                    # reset flags di DB
                    user.boostserver = 0
                    db.session.commit()
                    print(f"✅ DB: boostserver=0 untuk {user.email}")

                    # ambil serverspec aman
                    serverspec = ServerSpec.query.filter_by(id=panel_id).first()
                    target_ram = serverspec.ram if serverspec else 512

                    # panggil revert_ram (eksekusi ke panel)
                    try:
                        revert_ok = revert_ram(panel_id, user, server_data, 512)
                        print(f"🔁 revert_ram untuk {user.email} -> result: {revert_ok}")
                    except Exception as e:
                        print(f"❌ Error revert_ram untuk {user.email}:", e)

                    # clear last_boost
                    user.last_boost = None
                    db.session.commit()
                    print(f"✅ BOOST DIRESET: {user.email}")

                except Exception as e:
                    print("[ERROR reset_boost] loop user:", e)

    except Exception as e:
        print("❌ ERROR run_reset_ram_boost:", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB session dilepas (reset_boost)")
        except Exception:
            pass


# =========================
# ✅ RESET UPGRADE RAM
# =========================
def run_reset_ram_upgrade():
    print("🔥 MASUK run_reset_ram_upgrade()")
    try:
        with app.app_context():
            now = datetime.utcnow()
            users = User.query.filter(User.ram_upgrade_end != None).all()
            print("✅ User dengan ram_upgrade_end:", len(users))

            for user in users:
                try:
                    if now < user.ram_upgrade_end:
                        continue

                    panel_id = str(user.serverid) if user.serverid else None
                    if not panel_id or panel_id not in PANELS:
                        print(f"⚠️ panel_id invalid untuk user {user.email}, skip")
                        continue

                    server = Server.query.filter_by(user_id=user.id).first()
                    if not server:
                        print(f"⚠️ Tidak ada server untuk user {user.email}, skip")
                        continue

                    if not server.allocation_id:
                        allocation_id = get_allocation_from_api(panel_id, server.id)
                        if allocation_id:
                            server.allocation_id = allocation_id
                            db.session.commit()
                        else:
                            print(f"⚠️ Allocation tidak ditemukan untuk server {server.id}, skip")
                            continue

                    serverspec = ServerSpec.query.filter_by(id=panel_id).first()
                    target_ram = serverspec.ram if serverspec else 512

                    try:
                        revert_ok = revert_ram(panel_id, user, server, 512)
                        print(f"🔁 revert_ram (upgrade) untuk {user.email} -> result: {revert_ok}")
                    except Exception as e:
                        print(f"❌ Error revert_ram (upgrade) untuk {user.email}:", e)

                    if revert_ok:
                        user.ram = 512
                        user.ram_upgrade_start = None
                        user.ram_upgrade_end = None
                        db.session.commit()
                        print(f"✅ UPGRADE DIRESET: {user.email}")

                except Exception as e:
                    print("[ERROR reset_upgrade] loop user:", e)

    except Exception as e:
        print("❌ ERROR run_reset_ram_upgrade:", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB session dilepas (reset_upgrade)")
        except Exception:
            pass


# =========================
# ✅ SHUTDOWN USER TIDAK AKTIF
# =========================
def run_shutdown_inactive_servers():
    print("🔥 MASUK run_shutdown_inactive_servers()")
    try:
        with app.app_context():
            batas = datetime.utcnow() - timedelta(days=5)
            users = User.query.filter(User.last_login != None, User.last_login < batas).all()
            print("✅ User inactive:", len(users))

            for user in users:
                try:
                    panel_id = str(user.serverid) if user.serverid else None
                    if not panel_id or panel_id not in PANELS:
                        continue

                    servers = Server.query.filter_by(user_id=user.id).all()
                    for server in servers:
                        try:
                            url = f"{PANELS[panel_id]['url']}/api/application/servers/{server.id}/power"
                            headers = {
                                "Authorization": f"Bearer {PANELS[panel_id]['api_key']}",
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                            }

                            r = requests.post(url, headers=headers, json={"signal": "stop"})
                            if r.status_code == 204:
                                print(f"[✓] Server {server.id} dimatikan")
                            else:
                                print(f"⚠️ Gagal matikan server {server.id}, status: {r.status_code}")
                        except Exception as e:
                            print("❌ Error saat memanggil panel power:", e)

                except Exception as e:
                    print("[ERROR shutdown] loop user:", e)

    except Exception as e:
        print("❌ ERROR run_shutdown_inactive_servers:", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB session dilepas (shutdown)")
        except Exception:
            pass


# =========================
# ✅ WEEKLY BACKUP
# =========================
def weekly_backup():
    print("🔥 MASUK weekly_backup()")
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
                    print(f"✅ Backup dijalankan: {user.email}")

                except Exception as e:
                    print(f"[ERROR weekly_backup] {user.email}:", e)
                    user.auto_backup_enabled = False
                    db.session.commit()

                time.sleep(60)

    except Exception as e:
        print("❌ ERROR weekly_backup:", e)

    finally:
        try:
            db.session.remove()
            print("✅ DB session dilepas (weekly_backup)")
        except Exception:
            pass
            
def get_existing_file():
    url = f"{GITHUB_API}/repos/{REPO}/contents/{FILE_PATH}?ref={BRANCH}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode()
        return json.loads(content), data["sha"]

    return {}, None


def sync_coin_to_github():
    users = User.query.filter(User.coin > 0).all()

    coin_data = {}
    for user in users:
        coin_data[user.email] = {
            "coin": user.coin
        }

    existing_data, sha = get_existing_file()

    if coin_data == existing_data:
        print("[INFO] Coin JSON tidak berubah")
        return

    content_encoded = base64.b64encode(
        json.dumps(coin_data, indent=2).encode()
    ).decode()

    url = f"{GITHUB_API}/repos/{REPO}/contents/{FILE_PATH}"

    payload = {
        "message": "Sync user coin data",
        "content": content_encoded,
        "branch": BRANCH
    }

    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=HEADERS, json=payload)

    if r.status_code in (200, 201):
        print("[SUCCESS] Coin berhasil di-sync ke GitHub")
    else:
        print("[ERROR] Gagal sync:", r.text)