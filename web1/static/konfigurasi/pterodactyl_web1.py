# pterodactyl.py
import requests
import logging
import urllib3
from dateutil.parser import parse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from config_web1 import admin_mail, moderator_mail

# Header API
PANELS = {
    "server1": {
        "url": "https://console.kocheng.tech",
        "api_key": "ptla_gW4dCCjvKzeZAN54jYEMs8Gghsf1YzPqsB4SOebuZQS",
        "client_api_key": "ptlc_0QyWefmgfx9FfFJff7fhSx07FmY4pCy5lCqNUJIhlGx"
    },
    "server2": {
        "url": "https://console.kocheng.biz.id",
        "api_key": "ptla_9ycm6JAufB53NsSeoWNSdpukhk69YQBulExWwSIeQg4",
        "client_api_key": "ptlc_4BZRqnOFcDuRMNiV5neWjO0CuInlqXkaB0wfHuic7nt"
    }
    # Bisa ditambah server3, dst...
}

def get_headers(panel_id):
    return {
        "Authorization": f"Bearer {PANELS[panel_id]['api_key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
def get_client_headers(panel_id):
    return {
        "Authorization": f"Bearer {PANELS[panel_id]['client_api_key']}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_egg_startup(panel_id, nest_id, egg_id):
    """Ambil startup command dari egg tertentu di panel."""
    url = f"{PANELS[panel_id]['url']}/api/application/nests/{nest_id}/eggs/{egg_id}"
    try:
        response = requests.get(url, headers=get_headers(panel_id))
        response.raise_for_status()
        data = response.json()
        if 'attributes' in data:
            return data['attributes'].get('startup', "")
        else:
            logging.error(f"[{panel_id}] Response JSON tidak mengandung 'attributes': {data}")
            return ""
    except requests.exceptions.RequestException as e:
        logging.error(f"[{panel_id}] Gagal ambil egg startup: {e}")
        return ""

def get_available_allocation(panel_id, node_id):
    page = 1
    while True:
        url = f"{PANELS[panel_id]['url']}/api/application/nodes/{node_id}/allocations?page={page}"
        response = requests.get(url, headers=get_headers(panel_id))
        response.raise_for_status()
        data = response.json()

        for alloc in data['data']:
            if not alloc['attributes']['assigned']:
                return alloc['attributes']['id']

        if not data['meta']['pagination']['links']['next']:
            break
        page += 1
    return None

# Fungsi buat user (jika belum ada)
def create_user(panel_id, email, username):
    try:
        url = f"{PANELS[panel_id]['url']}/api/application/users"

        # 🔎 Cek apakah user dengan email ini sudah ada
        check = requests.get(f"{url}?filter[email]={email}", headers=get_headers(panel_id))
        check.raise_for_status()
        data = check.json()

        if data.get("data"):
            user_id = data["data"][0]["attributes"]["id"]
            logging.info(f"[{panel_id}] User sudah ada di Pterodactyl dengan ID {user_id}")
            return {"id": user_id}

        # 📤 Data untuk user baru
        user_data = {
            "email": email,
            "username": username,
            "first_name": username,
            "last_name": "User",
            "password": username,
        }

        resp = requests.post(url, json=user_data, headers=get_headers(panel_id))

        if resp.status_code == 201:
            logging.info(f"[{panel_id}] User baru berhasil dibuat di Pterodactyl: {email}")
            return resp.json()

        # ❌ Kalau gagal, log detail error
        logging.error(f"[{panel_id}] Gagal membuat user (status {resp.status_code})")
        try:
            logging.error(f"[{panel_id}] Response: {resp.json()}")
        except Exception:
            logging.error(f"[{panel_id}] Response text: {resp.text}")
        return None

    except requests.exceptions.RequestException as e:
        logging.error(f"[{panel_id}] Exception saat membuat user: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logging.error(f"[{panel_id}] Response status: {e.response.status_code}")
            logging.error(f"[{panel_id}] Response text: {e.response.text}")
        return None

# Fungsi buat server
def create_server(panel_id, user_id, name, egg_id, node_id, cpu, ram, disk):
    try:
        allocation_id = get_available_allocation(panel_id, node_id)
        if allocation_id is None:
            logging.error(f"[{panel_id}] Tidak ada allocation ID tersedia")
            return None

        # Konfigurasi Egg
        egg_configs = {
            16: {  # Python Generic
                "docker_image": "ghcr.io/parkervcp/yolks:python_3.10",
                "startup": "pip install -r requirements.txt && python /home/container/{{STARTUP_FILE}} {{EXTRA_ARGS}}",
                "environment": {
                    "STARTUP_FILE": "main.py",
                    "EXTRA_ARGS": ""
                },
                "nest_id": 6
            },
            15: {  # NodeJS
                "docker_image": "ghcr.io/parkervcp/yolks:nodejs_20",
                "startup": get_egg_startup(panel_id, 5, 15),
                "environment": {
                    "NODE_VERSION": "18",
                    "CMD_RUN": "npm start"
                },
                "nest_id": 5
            }
        }

        if egg_id not in egg_configs:
            logging.error(f"[{panel_id}] Egg {egg_id} tidak dikenali")
            return None

        config = egg_configs[egg_id]

        # Ambil startup dari API kalau belum diisi
        if not config["startup"]:
            config["startup"] = get_egg_startup(panel_id, config["nest_id"], egg_id)

        server_data = {
            "name": name,
            "user": user_id,
            "egg": egg_id,
            "docker_image": config["docker_image"],
            "startup": config["startup"],
            "environment": config["environment"],
            "limits": {
                "memory": ram,
                "swap": 0,
                "disk": disk,
                "io": 500,
                "cpu": cpu
            },
            "feature_limits": {"databases": 5, "backups": 1},
            "allocation": {"default": allocation_id},
            "description": "Free"
        }

        resp = requests.post(
            f"{PANELS[panel_id]['url']}/api/application/servers",
            json=server_data,
            headers=get_headers(panel_id)
        )
        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.RequestException as e:
        logging.error(f"[{panel_id}] Error creating server: {str(e)}")
        if e.response is not None:
            logging.error(e.response.text)
        return None
        
##CLEAR SERVER & USER
def get_all_nodes(panel_id):
    url = f"{PANELS[panel_id]['url']}/api/application/nodes"
    nodes = {}
    page = 1

    while True:
        resp = requests.get(url, headers=get_headers(panel_id), params={"page": page})
        if resp.status_code != 200:
            break

        data = resp.json()
        for node in data['data']:
            nodes[str(node['attributes']['id'])] = node['attributes']['name']

        if not data.get("meta", {}).get("pagination", {}).get("links", {}).get("next"):
            break
        page += 1

    return nodes
    
def delete_server(panel_id, server_id):
    """Hapus server dari panel menggunakan Application API key."""
    url = f"{PANELS[panel_id]['url']}/api/application/servers/{server_id}"
    resp = requests.delete(url, headers=get_headers(panel_id))

    # Tambahkan log agar tahu jika gagal
    if resp.status_code != 204:
        print(f"[DELETE ERROR][{panel_id}] Server {server_id} gagal dihapus. "
              f"Status: {resp.status_code}, Response: {resp.text}")

    return resp.status_code == 204
    
def get_all_users(panel_id):
    url = f"{PANELS[panel_id]['url']}/api/application/users"
    users = []
    page = 1
    while True:
        resp = requests.get(url, headers=get_headers(panel_id), params={"page": page})
        if resp.status_code != 200:
            break
        data = resp.json()
        users.extend(data['data'])
        if not data.get("meta", {}).get("pagination", {}).get("links", {}).get("next"):
            break
        page += 1
    return users

def get_all_servers(panel_id):
    servers = []
    page = 1
    while True:
        url = f"{PANELS[panel_id]['url']}/api/application/servers?page={page}"
        resp = requests.get(url, headers=get_headers(panel_id))
        if resp.status_code != 200:
            break

        data = resp.json()
        servers.extend(data['data'])

        if not data.get("meta", {}).get("pagination", {}).get("links", {}).get("next"):
            break
        page += 1
    return servers
    
def get_user_server_counts(panel_id):
    """Hitung jumlah server per user di panel tertentu."""
    all_servers = get_all_servers(panel_id)
    user_server_map = defaultdict(int)

    for server in all_servers:
        attr = server['attributes']
        user_id = attr['user']
        user_server_map[user_id] += 1

    return user_server_map

def delete_user(panel_id, user_id):
    url = f"{PANELS[panel_id]['url']}/api/application/users/{user_id}"
    resp = requests.delete(url, headers=get_headers(panel_id))
    return resp.status_code == 204
    
def hapus_user_tanpa_server(panel_id, dry_run=False):
    """Hapus user yang tidak punya server di panel tertentu (kecuali admin)."""
    output = []
    user_server_counts = get_user_server_counts(panel_id)
    users = get_all_users(panel_id)

    total_dihapus = 0
    total_dilewatkan = 0

    for user in users:
        attr = user['attributes']
        user_id = attr['id']
        username = attr['username']
        email = attr.get('email', '')  # ambil email user
        server_count = user_server_counts.get(user_id, 0)

        # Skip user admin
        if email in admin_mail:
            output.append(f"[{panel_id}] User '{username}' dilewatkan karena merupakan admin.")
            total_dilewatkan += 1
            continue
            
        if email in moderator_mail:
            output.append(f"[{panel_id}] User '{username}' dilewatkan karena merupakan moderator.")
            total_dilewatkan += 1
            continue

        if server_count == 0:
            output.append(f"[{panel_id}] User '{username}' tidak punya server, siap dihapus.")
            if dry_run:
                output.append("  [DRY RUN] User tidak dihapus.")
            else:
                if delete_user(panel_id, user_id):
                    output.append(f"  User '{username}' berhasil dihapus.")
                    total_dihapus += 1
                else:
                    output.append(f"  Gagal menghapus user '{username}'.")
        else:
            output.append(f"[{panel_id}] User '{username}' masih punya {server_count} server, dilewatkan.")
            total_dilewatkan += 1

    if total_dihapus == 0 and dry_run:
        output.append("Tidak ada user tanpa server ditemukan (DRY RUN).")
    elif total_dihapus == 0:
        output.append("Tidak ada user tanpa server yang berhasil dihapus.")
    
    total_user = total_dihapus + total_dilewatkan
    output.append(f"\nRingkasan untuk panel {panel_id}:")
    output.append(f"  Total user diproses: {total_user}")
    output.append(f"  Total user dihapus: {total_dihapus}")
    output.append(f"  Total user tersisa: {total_user - total_dihapus}")

    return output

def fetch_node_server_counts(panel_id):
    try:
        # Ambil semua node
        nodes_res = requests.get(
            f"{PANELS[panel_id]['url']}/api/application/nodes",
            headers=get_headers(panel_id)
        )
        nodes_res.raise_for_status()
        nodes = nodes_res.json().get("data", [])

        # Ambil semua server (sudah ada fungsi multi-panel)
        servers = get_all_servers(panel_id)

        # Hitung server per node
        server_counts = {node["attributes"]["id"]: 0 for node in nodes}
        for server in servers:
            node_id = server["attributes"].get("node")
            if node_id in server_counts:
                server_counts[node_id] += 1

        # Gabungkan info node dan jumlah server
        result = {}
        for node in nodes:
            node_id = node["attributes"]["id"]
            result[node_id] = {
                "name": node["attributes"]["name"],
                "count": server_counts[node_id]
            }

        return result

    except Exception as e:
        logging.exception(f"[{panel_id}] Gagal mengambil data node/server")
        return None

def fetch_egg_list(panel_id):
    """Ambil semua daftar egg dari panel tertentu."""
    try:
        nests_res = requests.get(
            f"{PANELS[panel_id]['url']}/api/application/nests",
            headers=get_headers(panel_id)
        )
        nests_res.raise_for_status()
        nests = nests_res.json()['data']

        all_eggs = []
        for nest in nests:
            nest_id = nest['attributes']['id']
            eggs_res = requests.get(
                f"{PANELS[panel_id]['url']}/api/application/nests/{nest_id}/eggs",
                headers=get_headers(panel_id)
            )
            eggs_res.raise_for_status()
            eggs = eggs_res.json()['data']

            for egg in eggs:
                egg_info = {
                    'id': egg['attributes']['id'],
                    'name': egg['attributes']['name'],
                    'nest': nest['attributes']['name']
                }
                all_eggs.append(egg_info)

        return all_eggs

    except Exception as e:
        logging.error(f"[{panel_id}] Gagal mengambil data eggs: {e}")
        return None
