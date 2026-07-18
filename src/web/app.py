"""Servidor web local para administrar la configuracion de MultiScreenPi
sin tener que editar config.yaml a mano por SSH.

Corre en un hilo dentro del proceso principal (ver core/app.py), asi que
los cambios (feeds, camaras, atajos, luces, imagenes) se reflejan de
inmediato la proxima vez que entres a esa pantalla en el panel, sin
reiniciar el servicio.
"""

from pathlib import Path

from flask import Flask, redirect, request, send_from_directory
from werkzeug.utils import secure_filename

from core import config

SLIDESHOW_DIR = Path(__file__).resolve().parents[2] / "assets" / "slideshow"
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

app = Flask(__name__)


def _password():
    return config.get("web", "password", default="")


@app.before_request
def _check_auth():
    auth = request.authorization
    if not auth or auth.username != "admin" or auth.password != _password():
        return (
            "Autenticacion requerida",
            401,
            {"WWW-Authenticate": 'Basic realm="MultiScreenPi"'},
        )


def _page(title, body):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - MultiScreenPi</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 760px; margin: 24px auto; padding: 0 16px; background:#fff; color:#1c1c20; }}
  h1 {{ font-size: 1.4rem; }}
  nav a {{ margin-right: 12px; text-decoration: none; color: #3f51b5; font-weight: 600; }}
  .card {{ background:#eef0fd; border-radius:12px; padding:16px; margin-bottom:12px; }}
  form.inline {{ display:inline; margin:0; }}
  input, select {{ padding:10px; margin:6px 0; width:100%; box-sizing:border-box; border:1px solid #ccc; border-radius:8px; }}
  button {{ background:#3f51b5; color:#fff; border:none; padding:10px 18px; border-radius:8px; cursor:pointer; font-size:1rem; }}
  button.danger {{ background:#d32f2f; }}
  button.muted {{ background:#8887a3; }}
  .row {{ display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap: wrap; }}
  .actions {{ display:flex; gap:8px; }}
  img.thumb {{ max-width:140px; max-height:100px; border-radius:8px; display:block; margin-bottom:8px; }}
  .gallery {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap:14px; }}
  .gallery .card {{ text-align:center; }}
  .gallery img.thumb {{ max-width:100%; max-height:140px; width:100%; object-fit:cover; margin:0 0 8px; }}
</style>
</head>
<body>
<h1>MultiScreenPi</h1>
<nav>
  <a href="/">Inicio</a>
  <a href="/news">Noticias</a>
  <a href="/cameras">Camaras</a>
  <a href="/shortcuts">Atajos PC</a>
  <a href="/home-assistant">Home Assistant</a>
  <a href="/images">Imagenes</a>
</nav>
<hr>
{body}
</body>
</html>"""


@app.route("/")
def index():
    body = """
    <p>Bienvenido, este proyecto es desarrollado por Cristian Jimenez, Loja, Ecuador.</p>
    <p>Elige que administrar en el menu de arriba.</p>
    """
    return _page("Inicio", body)


# --- Noticias ---


@app.route("/news", methods=["GET", "POST"])
def news():
    feeds = config.get("news", "feeds", default=[]) or []

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        if name and url:
            feeds = feeds + [{"name": name, "url": url}]
            config.set_value("news", "feeds", value=feeds)
        return redirect("/news")

    rows = ""
    for i, feed in enumerate(feeds):
        rows += f"""<div class="card row">
          <div><strong>{feed.get('name', '?')}</strong><br><small>{feed.get('url', '')}</small></div>
          <div class="actions">
            <a href="/news/edit/{i}"><button type="button">Editar</button></a>
            <form class="inline" method="post" action="/news/delete/{i}">
              <button class="danger" type="submit">Eliminar</button>
            </form>
          </div>
        </div>"""

    body = (
        rows
        + """
    <h2>Agregar feed</h2>
    <form method="post">
      <input name="name" placeholder="Nombre (ej. El Comercio)" required>
      <input name="url" placeholder="URL del feed RSS" required>
      <button type="submit">Agregar</button>
    </form>
    """
    )
    return _page("Noticias", body)


@app.route("/news/edit/<int:index>", methods=["GET", "POST"])
def news_edit(index):
    feeds = config.get("news", "feeds", default=[]) or []
    if not (0 <= index < len(feeds)):
        return redirect("/news")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        if name and url:
            feeds[index] = {"name": name, "url": url}
            config.set_value("news", "feeds", value=feeds)
        return redirect("/news")

    feed = feeds[index]
    body = f"""<form method="post">
      <input name="name" value="{feed.get('name', '')}" placeholder="Nombre" required>
      <input name="url" value="{feed.get('url', '')}" placeholder="URL del feed RSS" required>
      <button type="submit">Guardar</button>
    </form>"""
    return _page("Editar feed", body)


@app.route("/news/delete/<int:index>", methods=["POST"])
def news_delete(index):
    feeds = config.get("news", "feeds", default=[]) or []
    if 0 <= index < len(feeds):
        feeds.pop(index)
        config.set_value("news", "feeds", value=feeds)
    return redirect("/news")


# --- Camaras ---


@app.route("/cameras", methods=["GET", "POST"])
def cameras():
    cams = config.get("cameras", default=[]) or []

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        cam_type = request.form.get("type", "mjpeg")
        target = request.form.get("target", "").strip()
        if name and target:
            entry = {"name": name, "type": cam_type}
            if cam_type == "mjpeg":
                entry["url"] = target
            else:
                entry["entity_id"] = target
            cams = cams + [entry]
            config.set_value("cameras", value=cams)
        return redirect("/cameras")

    rows = ""
    for i, cam in enumerate(cams):
        target = cam.get("url") or cam.get("entity_id", "")
        rows += f"""<div class="card row">
          <div><strong>{cam.get('name', '?')}</strong><br><small>{cam.get('type')}: {target}</small></div>
          <div class="actions">
            <a href="/cameras/edit/{i}"><button type="button">Editar</button></a>
            <form class="inline" method="post" action="/cameras/delete/{i}">
              <button class="danger" type="submit">Eliminar</button>
            </form>
          </div>
        </div>"""

    body = (
        rows
        + """
    <h2>Agregar camara</h2>
    <form method="post">
      <input name="name" placeholder="Nombre" required>
      <select name="type">
        <option value="mjpeg">MJPEG (URL de stream)</option>
        <option value="ha_snapshot">Home Assistant (entity_id)</option>
      </select>
      <input name="target" placeholder="URL del stream o entity_id" required>
      <button type="submit">Agregar</button>
    </form>
    """
    )
    return _page("Camaras", body)


@app.route("/cameras/edit/<int:index>", methods=["GET", "POST"])
def cameras_edit(index):
    cams = config.get("cameras", default=[]) or []
    if not (0 <= index < len(cams)):
        return redirect("/cameras")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        cam_type = request.form.get("type", "mjpeg")
        target = request.form.get("target", "").strip()
        if name and target:
            entry = {"name": name, "type": cam_type}
            if cam_type == "mjpeg":
                entry["url"] = target
            else:
                entry["entity_id"] = target
            cams[index] = entry
            config.set_value("cameras", value=cams)
        return redirect("/cameras")

    cam = cams[index]
    target = cam.get("url") or cam.get("entity_id", "")
    mjpeg_selected = "selected" if cam.get("type") == "mjpeg" else ""
    ha_selected = "selected" if cam.get("type") == "ha_snapshot" else ""
    body = f"""<form method="post">
      <input name="name" value="{cam.get('name', '')}" placeholder="Nombre" required>
      <select name="type">
        <option value="mjpeg" {mjpeg_selected}>MJPEG (URL de stream)</option>
        <option value="ha_snapshot" {ha_selected}>Home Assistant (entity_id)</option>
      </select>
      <input name="target" value="{target}" placeholder="URL del stream o entity_id" required>
      <button type="submit">Guardar</button>
    </form>"""
    return _page("Editar camara", body)


@app.route("/cameras/delete/<int:index>", methods=["POST"])
def cameras_delete(index):
    cams = config.get("cameras", default=[]) or []
    if 0 <= index < len(cams):
        cams.pop(index)
        config.set_value("cameras", value=cams)
    return redirect("/cameras")


# --- Atajos de PC ---


@app.route("/shortcuts", methods=["GET", "POST"])
def shortcuts():
    items = config.get("pc_control", "shortcuts", default=[]) or []

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        kind = request.form.get("type", "url")
        target = request.form.get("target", "").strip()
        if name and target:
            items = items + [{"name": name, "type": kind, "target": target}]
            config.set_value("pc_control", "shortcuts", value=items)
        return redirect("/shortcuts")

    rows = ""
    for i, item in enumerate(items):
        rows += f"""<div class="card row">
          <div><strong>{item.get('name', '?')}</strong><br><small>{item.get('type')}: {item.get('target', '')}</small></div>
          <div class="actions">
            <a href="/shortcuts/edit/{i}"><button type="button">Editar</button></a>
            <form class="inline" method="post" action="/shortcuts/delete/{i}">
              <button class="danger" type="submit">Eliminar</button>
            </form>
          </div>
        </div>"""

    body = (
        rows
        + """
    <h2>Agregar atajo</h2>
    <form method="post">
      <input name="name" placeholder="Nombre" required>
      <select name="type">
        <option value="url">Sitio web</option>
        <option value="app">App (nombre configurado en el agente)</option>
      </select>
      <input name="target" placeholder="URL o nombre de la app" required>
      <button type="submit">Agregar</button>
    </form>
    """
    )
    return _page("Atajos de PC", body)


@app.route("/shortcuts/edit/<int:index>", methods=["GET", "POST"])
def shortcuts_edit(index):
    items = config.get("pc_control", "shortcuts", default=[]) or []
    if not (0 <= index < len(items)):
        return redirect("/shortcuts")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        kind = request.form.get("type", "url")
        target = request.form.get("target", "").strip()
        if name and target:
            items[index] = {"name": name, "type": kind, "target": target}
            config.set_value("pc_control", "shortcuts", value=items)
        return redirect("/shortcuts")

    item = items[index]
    url_selected = "selected" if item.get("type") == "url" else ""
    app_selected = "selected" if item.get("type") == "app" else ""
    body = f"""<form method="post">
      <input name="name" value="{item.get('name', '')}" placeholder="Nombre" required>
      <select name="type">
        <option value="url" {url_selected}>Sitio web</option>
        <option value="app" {app_selected}>App</option>
      </select>
      <input name="target" value="{item.get('target', '')}" placeholder="URL o nombre de la app" required>
      <button type="submit">Guardar</button>
    </form>"""
    return _page("Editar atajo", body)


@app.route("/shortcuts/delete/<int:index>", methods=["POST"])
def shortcuts_delete(index):
    items = config.get("pc_control", "shortcuts", default=[]) or []
    if 0 <= index < len(items):
        items.pop(index)
        config.set_value("pc_control", "shortcuts", value=items)
    return redirect("/shortcuts")


# --- Home Assistant: agregar luces a mano y activar/desactivar ---


@app.route("/home-assistant", methods=["GET", "POST"])
def home_assistant():
    entities = config.get("home_assistant", "entities", default=[]) or []

    if request.method == "POST":
        entity_id = request.form.get("entity_id", "").strip()
        if entity_id:
            entities = entities + [{"entity_id": entity_id, "enabled": True}]
            config.set_value("home_assistant", "entities", value=entities)
        return redirect("/home-assistant")

    rows = ""
    for i, entity in enumerate(entities):
        enabled = entity.get("enabled", True)
        toggle_label = "Desactivar" if enabled else "Activar"
        status = "Activa" if enabled else "Inactiva"
        rows += f"""<div class="card row">
          <div><strong>{entity.get('entity_id', '?')}</strong><br><small>{status}</small></div>
          <div class="actions">
            <a href="/home-assistant/edit/{i}"><button type="button">Editar</button></a>
            <form class="inline" method="post" action="/home-assistant/toggle/{i}">
              <button class="muted" type="submit">{toggle_label}</button>
            </form>
            <form class="inline" method="post" action="/home-assistant/delete/{i}">
              <button class="danger" type="submit">Eliminar</button>
            </form>
          </div>
        </div>"""

    if not rows:
        rows = "<p>No has agregado ninguna luz todavia. Sin ninguna agregada, el panel muestra todas las light.* automaticamente.</p>"

    body = (
        rows
        + """
    <h2>Agregar luz</h2>
    <form method="post">
      <input name="entity_id" placeholder="entity_id (ej. light.sala)" required>
      <button type="submit">Agregar</button>
    </form>
    """
    )
    return _page("Home Assistant", body)


@app.route("/home-assistant/edit/<int:index>", methods=["GET", "POST"])
def home_assistant_edit(index):
    entities = config.get("home_assistant", "entities", default=[]) or []
    if not (0 <= index < len(entities)):
        return redirect("/home-assistant")

    if request.method == "POST":
        entity_id = request.form.get("entity_id", "").strip()
        if entity_id:
            entities[index]["entity_id"] = entity_id
            config.set_value("home_assistant", "entities", value=entities)
        return redirect("/home-assistant")

    entity = entities[index]
    body = f"""<form method="post">
      <input name="entity_id" value="{entity.get('entity_id', '')}" placeholder="entity_id" required>
      <button type="submit">Guardar</button>
    </form>"""
    return _page("Editar luz", body)


@app.route("/home-assistant/toggle/<int:index>", methods=["POST"])
def home_assistant_toggle(index):
    entities = config.get("home_assistant", "entities", default=[]) or []
    if 0 <= index < len(entities):
        entities[index]["enabled"] = not entities[index].get("enabled", True)
        config.set_value("home_assistant", "entities", value=entities)
    return redirect("/home-assistant")


@app.route("/home-assistant/delete/<int:index>", methods=["POST"])
def home_assistant_delete(index):
    entities = config.get("home_assistant", "entities", default=[]) or []
    if 0 <= index < len(entities):
        entities.pop(index)
        config.set_value("home_assistant", "entities", value=entities)
    return redirect("/home-assistant")


# --- Imagenes del slideshow ---


@app.route("/images", methods=["GET", "POST"])
def images():
    SLIDESHOW_DIR.mkdir(parents=True, exist_ok=True)

    if request.method == "POST":
        file = request.files.get("photo")
        if file and file.filename:
            filename = secure_filename(file.filename)
            if Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTS:
                file.save(SLIDESHOW_DIR / filename)
        return redirect("/images")

    files = sorted(p.name for p in SLIDESHOW_DIR.iterdir() if p.suffix.lower() in ALLOWED_IMAGE_EXTS)
    cells = ""
    for name in files:
        cells += f"""<div class="card">
          <img class="thumb" src="/slideshow-image/{name}">
          <div>{name}</div>
          <form method="post" action="/images/delete/{name}">
            <button class="danger" type="submit">Eliminar</button>
          </form>
        </div>"""

    gallery = f'<div class="gallery">{cells}</div>' if cells else "<p>Todavia no hay fotos.</p>"

    body = (
        gallery
        + """
    <h2>Subir foto</h2>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="photo" accept="image/*" required>
      <button type="submit">Subir</button>
    </form>
    """
    )
    return _page("Imagenes", body)


@app.route("/slideshow-image/<path:filename>")
def slideshow_image(filename):
    return send_from_directory(SLIDESHOW_DIR, filename)


@app.route("/images/delete/<path:filename>", methods=["POST"])
def images_delete(filename):
    path = SLIDESHOW_DIR / secure_filename(filename)
    if path.exists() and path.parent == SLIDESHOW_DIR:
        path.unlink()
    return redirect("/images")


def run_server():
    port = config.get("web", "port", default=8080)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
