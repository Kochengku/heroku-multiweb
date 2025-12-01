from flask import request
from werkzeug.wrappers import Response
from mega import Mega
from web1.app import upload_to_mega, download_from_mega
from web3.app import upload_to_mega, download_from_mega

# ============================
# LOGIN KE MEGA (SEKALI SAAT DYNO START)
# ============================

MEGA_EMAIL = "kentukimeme@gmail.com"
MEGA_PASSWORD = "Bintang123**"

mega = Mega()
mega_client = mega.login(MEGA_EMAIL, MEGA_PASSWORD)

print("[INFO] Login Mega Sukses!")

# ============================
# IMPORT WEBSITE APPS
# ============================

from web1.app import app as web1
from web2.app import app as web2
from web3.app import app as web3
from web4.app import app as web4

# ============================
# ROUTER BERDASARKAN DOMAIN
# ============================

DOMAIN_MAP = {
    "WEB1_DOMAIN": web1,
    "WEB2_DOMAIN": web2,
    "WEB3_DOMAIN": web3,
    "WEB4_DOMAIN": web4,
}

class HostDispatcher:
    def __call__(self, environ, start_response):
        host = environ.get("HTTP_HOST", "").split(":")[0].lower()

        # pilih website sesuai domain
        for domain, app in DOMAIN_MAP.items():
            if domain in host:
                return app(environ, start_response)

        return Response("Domain tidak ditemukan", status=404)(environ, start_response)

application = HostDispatcher()