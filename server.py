from flask import request
from werkzeug.wrappers import Response
from mega import Mega

# ============== MEGA LOGIN LAZY ==============
MEGA_EMAIL = "kentukimeme@gmail.com"
MEGA_PASSWORD = "Bintang123**"

mega_client = None
def get_mega():
    global mega_client
    if mega_client is None:
        mega = Mega()
        mega_client = mega.login(MEGA_EMAIL, MEGA_PASSWORD)
        print("[INFO] Login Mega Sukses!")
    return mega_client

# ============== IMPORT APPS ==============
from web1.app import app as web1
from web2.app import app as web2
from web3.app import app as web3
from web4.app import app as web4

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

app = HostDispatcher()  # Gunicorn akan memanggil ini