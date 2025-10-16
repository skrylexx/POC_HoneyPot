from flask import Flask, request, render_template_string, send_from_directory, abort
import pathlib
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix
import os

# Flask app
app = Flask(__name__, static_folder=None)

# Nous faisons confiance à 1 proxy (nginx sur l'hôte) qui ajoute X-Forwarded-For
NUM_PROXIES = 1
if NUM_PROXIES > 0:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=NUM_PROXIES, x_proto=NUM_PROXIES,
                            x_host=NUM_PROXIES, x_port=NUM_PROXIES, x_prefix=NUM_PROXIES)

# Directories
SITE_DIR = pathlib.Path("/app")         # fichiers servis
SHARED_DIR = pathlib.Path("/shared")    # monté depuis D:\HoneyPot
CONN_FILE = SHARED_DIR / "connections.txt"

# Ensure structure exists
SITE_DIR.mkdir(parents=True, exist_ok=True)
(SITE_DIR / "test.py").touch(exist_ok=True)
(SITE_DIR / "generation.py").touch(exist_ok=True)
(SITE_DIR / "result.json").touch(exist_ok=True)
(SITE_DIR / "tests").mkdir(parents=True, exist_ok=True)
SHARED_DIR.mkdir(parents=True, exist_ok=True)

INDEX_TEMPLATE = """
<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>Arborescence</title>
<style>body{font-family:system-ui,Segoe UI,Roboto,Arial;padding:20px}ul{list-style:none;padding-left:1rem}</style>
</head><body>
<h1>Arborescence</h1>
{{ tree_html|safe }}
</body></html>
"""

def render_tree(path: pathlib.Path) -> str:
    parts = []
    for entry in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        if entry.is_dir():
            parts.append(f'<li class="folder">📁 {entry.name}<ul>')
            for sub in sorted(entry.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                if sub.is_file():
                    parts.append(f'<li class="file">- <a href="/files/{entry.name}/{sub.name}">{sub.name}</a></li>')
            parts.append('</ul></li>')
        else:
            parts.append(f'<li class="file">- <a href="/files/{entry.name}">{entry.name}</a></li>')
    return "<ul>" + "\n".join(parts) + "</ul>"

def get_candidate_headers():
    return {
        "remote_addr": request.remote_addr or "",
        "x_forwarded_for": request.headers.get("X-Forwarded-For", ""),
        "x_real_ip": request.headers.get("X-Real-IP", ""),
        "via": request.headers.get("Via", ""),
        "forwarded": request.headers.get("Forwarded", ""),
        "user_agent": request.headers.get("User-Agent", ""),
    }

def choose_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    xr = request.headers.get("X-Real-IP", "")
    if xr:
        return xr.strip()
    return request.remote_addr or "unknown"

def log_connection(selected_ip: str, path: str):
    data = get_candidate_headers()
    try:
        SHARED_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONN_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()}Z\tselected_ip={selected_ip}\tpath={path}\n")
            f.write("\t".join([f"{k}={v}" for k, v in data.items()]) + "\n")
    except Exception as e:
        app.logger.warning(f"Could not write connection log: {e}")

@app.route("/", methods=["GET"])
def index():
    ip = choose_client_ip()
    log_connection(ip, "/")
    tree_html = render_tree(SITE_DIR)
    return render_template_string(INDEX_TEMPLATE, tree_html=tree_html)

@app.route("/files/<path:filename>", methods=["GET"])
def files(filename):
    full = (SITE_DIR / filename).resolve()
    if not str(full).startswith(str(SITE_DIR.resolve())):
        abort(403)
    if not full.exists() or not full.is_file():
        abort(404)
    ip = choose_client_ip()
    log_connection(ip, f"/files/{filename}")
    parent = str(full.parent)
    return send_from_directory(parent, full.name, as_attachment=True)

if __name__ == "__main__":
    # écoute sur 0.0.0.0:8081
    app.run(host="0.0.0.0", port=8081)
