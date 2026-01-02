from flask import request
from werkzeug.wrappers import Response

# =====================================
# IMPORT APP SETIAP DOMAIN
# =====================================
from web1.app import app as web1
from web2.app import app as web2
from web3.app import app as web3
from web4.app import app as web4


# =====================================
# ROUTER DOMAIN KE FLASK APP
# =====================================

DOMAIN_MAP = {
    "control.kocheng.biz.id": web1,
    "kocheng.biz.id": web2,
    "control.skyforgia.web.id": web3,
    "skyforgia.web.id": web4
}

class HostDispatcher:
    def __call__(self, environ, start_response):
        host = environ.get("HTTP_HOST", "").split(":")[0].lower()

        for domain, flask_app in DOMAIN_MAP.items():
            if domain == host:
                with flask_app.app_context():
                    return flask_app(environ, start_response)

        return Response("Domain tidak ditemukan", status=404)(environ, start_response)

app = HostDispatcher()