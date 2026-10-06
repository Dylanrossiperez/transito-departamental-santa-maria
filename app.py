from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
import os
from functools import wraps

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
DB_PATH = DATA_DIR / "site.db"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cambiar-esta-clave-secreta")

DEFAULTS = {
    "institution": "POLICÍA DE LA PROVINCIA DE CÓRDOBA",
    "department": "DEPARTAMENTAL SANTA MARÍA",
    "title": "TRÁNSITO",
    "subtitle": "Información y orientación para la comunidad",
    "hero_text": "Espacio informativo del área de Tránsito de la Departamental Santa María.",
    "phone": "A completar",
    "emergency": "911",
    "location": "Departamental Santa María — Córdoba",
    "hours": "A completar",
    "notice": "La información publicada debe mantenerse actualizada por el personal responsable.",
    "about": "Este sitio puede utilizarse para publicar información institucional, recomendaciones de seguridad vial, operativos preventivos, documentación y vías de contacto.",
}

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    for key, value in DEFAULTS.items():
        conn.execute("INSERT OR IGNORE INTO content(key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_content():
    conn = db()
    rows = conn.execute("SELECT key, value FROM content").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    return render_template("index.html", c=get_content())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Demo/local password. Change it before deployment.
        if request.form.get("password") == "transito2026":
            session["admin"] = True
            return redirect(request.args.get("next") or url_for("admin"))
        flash("Contraseña incorrecta.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
@admin_required
def admin():
    if request.method == "POST":
        conn = db()
        for key in DEFAULTS:
            value = request.form.get(key, "").strip()
            conn.execute("UPDATE content SET value = ? WHERE key = ?", (value, key))
        conn.commit()
        conn.close()
        flash("Cambios guardados correctamente.", "success")
        return redirect(url_for("admin"))
    return render_template("admin.html", c=get_content())

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
