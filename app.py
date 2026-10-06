from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory
)

import sqlite3
from pathlib import Path
import os
from functools import wraps
from werkzeug.utils import secure_filename


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        str(BASE_DIR / "data")
    )
)

DB_PATH = DATA_DIR / "site.db"


app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)


app.secret_key = os.getenv(
    "SECRET_KEY",
    "cambiar-esta-clave-secreta"
)


# ============================================================
# CONFIGURACIÓN DE IMÁGENES
# ============================================================

UPLOAD_DIR = DATA_DIR / "uploads"

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

MAX_IMAGE_SIZE = 8 * 1024 * 1024  # 8 MB


# ============================================================
# CONTENIDO PREDETERMINADO
# ============================================================

DEFAULTS = {

    "institution":
        "POLICÍA DE LA PROVINCIA DE CÓRDOBA",

    "department":
        "DEPARTAMENTAL SANTA MARÍA",

    "title":
        "TRÁNSITO",

    "subtitle":
        "Información y orientación para la comunidad",

    "hero_text":
        "Espacio informativo del área de Tránsito de la Departamental Santa María.",

    "phone":
        "A completar",

    "emergency":
        "911",

    "location":
        "Departamental Santa María — Córdoba",

    "hours":
        "A completar",

    "notice":
        "La información publicada debe mantenerse actualizada por el personal responsable.",

    "about":
        "Este sitio puede utilizarse para publicar información institucional, recomendaciones de seguridad vial, operativos preventivos, documentación y vías de contacto.",
}


# ============================================================
# BASE DE DATOS
# ============================================================

def db():

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS content (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    for key, value in DEFAULTS.items():

        conn.execute(
            """
            INSERT OR IGNORE INTO content(key, value)
            VALUES (?, ?)
            """,
            (key, value)
        )

    conn.commit()

    conn.close()


def get_content():

    conn = db()

    rows = conn.execute(
        "SELECT key, value FROM content"
    ).fetchall()

    conn.close()

    return {
        row["key"]: row["value"]
        for row in rows
    }


# ============================================================
# AUTENTICACIÓN
# ============================================================

def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("admin"):

            return redirect(
                url_for(
                    "login",
                    next=request.path
                )
            )

        return view(*args, **kwargs)

    return wrapped


# ============================================================
# FUNCIONES PARA IMÁGENES
# ============================================================

def allowed_image(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_image(
    file,
    filename
):

    if not file:

        return False, "No se recibió ninguna imagen."

    if not file.filename:

        return False, "No seleccionaste ningún archivo."

    if not allowed_image(file.filename):

        return (
            False,
            "Formato no permitido. "
            "Usá PNG, JPG, JPEG o WEBP."
        )

    # Comprobamos tamaño
    file.stream.seek(0, os.SEEK_END)

    size = file.stream.tell()

    file.stream.seek(0)

    if size > MAX_IMAGE_SIZE:

        return (
            False,
            "La imagen supera el límite de 8 MB."
        )

    extension = Path(
        secure_filename(file.filename)
    ).suffix.lower()

    if not extension:

        return (
            False,
            "No se pudo determinar el formato."
        )

    final_path = UPLOAD_DIR / f"{filename}{extension}"

    # Eliminamos versiones anteriores
    for old_file in UPLOAD_DIR.glob(
        f"{filename}.*"
    ):

        try:

            if old_file != final_path:
                old_file.unlink()

        except OSError:
            pass

    try:

        file.save(final_path)

    except Exception as error:

        app.logger.exception(
            "Error guardando imagen"
        )

        return (
            False,
            f"No se pudo guardar la imagen: {error}"
        )

    return True, final_path.name


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html",
        c=get_content()
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        # IMPORTANTE:
        # Para producción conviene mover la contraseña
        # a una variable de entorno en Render.

        if request.form.get(
            "password"
        ) == "transito2026":

            session["admin"] = True

            return redirect(
                request.args.get(
                    "next"
                )
                or url_for("admin")
            )

        flash(
            "Contraseña incorrecta.",
            "error"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# ============================================================
# ADMINISTRACIÓN
# ============================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
@admin_required
def admin():

    if request.method == "POST":

        conn = db()

        try:

            # -----------------------------------------------
            # GUARDAR CAMPOS DE TEXTO
            # -----------------------------------------------

            for key in DEFAULTS:

                value = request.form.get(
                    key,
                    ""
                ).strip()

                conn.execute(
                    """
                    UPDATE content
                    SET value = ?
                    WHERE key = ?
                    """,
                    (
                        value,
                        key
                    )
                )

            conn.commit()

            flash(
                "Cambios guardados correctamente.",
                "success"
            )

        except Exception as error:

            conn.rollback()

            app.logger.exception(
                "Error guardando contenido"
            )

            flash(
                f"Error al guardar los cambios: {error}",
                "error"
            )

        finally:

            conn.close()

        return redirect(
            url_for("admin")
        )

    return render_template(
        "admin.html",
        c=get_content()
    )


# ============================================================
# SUBIR ESCUDO
# ============================================================

@app.route(
    "/admin/upload-logo",
    methods=["POST"]
)
@admin_required
def upload_logo():

    file = request.files.get(
        "logo"
    )

    success, message = save_uploaded_image(
        file,
        "logo"
    )

    if success:

        flash(
            "Escudo actualizado correctamente.",
            "success"
        )

    else:

        flash(
            f"No se pudo actualizar el escudo: {message}",
            "error"
        )

    return redirect(
        url_for("admin")
    )


# ============================================================
# SUBIR FONDO
# ============================================================

@app.route(
    "/admin/upload-background",
    methods=["POST"]
)
@admin_required
def upload_background():

    file = request.files.get(
        "background"
    )

    success, message = save_uploaded_image(
        file,
        "background"
    )

    if success:

        flash(
            "Imagen de fondo actualizada correctamente.",
            "success"
        )

    else:

        flash(
            f"No se pudo actualizar el fondo: {message}",
            "error"
        )

    return redirect(
        url_for("admin")
    )


# ============================================================
# SERVIR IMÁGENES SUBIDAS
# ============================================================

@app.route(
    "/uploads/<path:filename>"
)
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# ============================================================
# INICIALIZACIÓN
# ============================================================

init_db()


# ============================================================
# EJECUCIÓN LOCAL
# ============================================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "5000"
            )
        ),
        debug=False
    )
