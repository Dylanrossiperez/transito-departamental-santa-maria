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
UPLOAD_DIR = DATA_DIR / "uploads"

ALLOWED_IMAGE_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

MAX_IMAGE_SIZE = 8 * 1024 * 1024


# ============================================================
# FLASK
# ============================================================

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
        "Este sitio puede utilizarse para publicar información institucional, recomendaciones de seguridad vial, operativos preventivos, documentación y vías de contacto."
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
            (
                key,
                value
            )
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

    extension = (
        filename
        .rsplit(".", 1)[1]
        .lower()
    )

    return extension in ALLOWED_IMAGE_EXTENSIONS


def get_image_path(name):

    """
    Busca una imagen por nombre lógico.

    Ejemplos:

        get_image_path("logo")
        get_image_path("background")

    Busca automáticamente:

        logo.png
        logo.jpg
        logo.jpeg
        logo.webp

    y lo mismo para background.
    """

    for extension in ALLOWED_IMAGE_EXTENSIONS:

        candidate = (
            UPLOAD_DIR /
            f"{name}.{extension}"
        )

        if candidate.is_file():
            return candidate

    return None


def save_uploaded_image(file, filename):

    if not file:
        return (
            False,
            "No se recibió ninguna imagen."
        )

    if not file.filename:
        return (
            False,
            "No seleccionaste ningún archivo."
        )

    if not allowed_image(file.filename):

        return (
            False,
            "Formato no permitido. "
            "Usá PNG, JPG, JPEG o WEBP."
        )

    # --------------------------------------------------------
    # COMPROBAR TAMAÑO
    # --------------------------------------------------------

    try:

        file.stream.seek(
            0,
            os.SEEK_END
        )

        size = file.stream.tell()

        file.stream.seek(0)

    except Exception:

        return (
            False,
            "No se pudo comprobar el tamaño de la imagen."
        )

    if size > MAX_IMAGE_SIZE:

        return (
            False,
            "La imagen supera el límite de 8 MB."
        )

    # --------------------------------------------------------
    # OBTENER EXTENSIÓN
    # --------------------------------------------------------

    safe_name = secure_filename(
        file.filename
    )

    extension = (
        Path(safe_name)
        .suffix
        .lower()
    )

    if extension not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    }:

        return (
            False,
            "Formato de imagen no válido."
        )

    # --------------------------------------------------------
    # NOMBRE FINAL
    # --------------------------------------------------------

    final_path = (
        UPLOAD_DIR /
        f"{filename}{extension}"
    )

    # --------------------------------------------------------
    # ELIMINAR VERSIONES ANTERIORES
    # --------------------------------------------------------

    for old_file in UPLOAD_DIR.glob(
        f"{filename}.*"
    ):

        try:

            if old_file != final_path:
                old_file.unlink()

        except OSError:

            pass

    # --------------------------------------------------------
    # GUARDAR
    # --------------------------------------------------------

    try:

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        file.save(final_path)

    except Exception as error:

        app.logger.exception(
            "Error guardando imagen"
        )

        return (
            False,
            f"No se pudo guardar la imagen: {error}"
        )

    return (
        True,
        final_path.name
    )


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

        password = request.form.get(
            "password",
            ""
        )

        expected_password = os.getenv(
            "ADMIN_PASSWORD",
            "transito2026"
        )

        if password == expected_password:

            session["admin"] = True

            return redirect(
                request.args.get("next")
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

@app.route("/uploads/logo")
def uploaded_logo():
    # 1. Buscar primero un logo subido
    for extension in ALLOWED_IMAGE_EXTENSIONS:
        candidate = UPLOAD_DIR / f"logo.{extension}"

        if candidate.is_file():
            return send_from_directory(
                UPLOAD_DIR,
                candidate.name
            )

    # 2. Si no existe un logo subido,
    # usar el escudo incluido en /app/static/
    static_logo = BASE_DIR / "app" / "static" / "escudo-policia-cordoba.jpeg"

    if static_logo.is_file():
        return send_from_directory(
            static_logo.parent,
            static_logo.name
        )

    return "Logo no encontrado", 404

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

    requested = (
        UPLOAD_DIR /
        filename
    )

    # --------------------------------------------------------
    # ARCHIVO EXACTO
    # --------------------------------------------------------

    if requested.is_file():

        return send_from_directory(
            UPLOAD_DIR,
            filename
        )

    # --------------------------------------------------------
    # BUSCAR POR NOMBRE SIN IMPORTAR EXTENSIÓN
    # --------------------------------------------------------

    stem = Path(
        filename
    ).stem

    if stem:

        image_path = get_image_path(
            stem
        )

        if image_path:

            return send_from_directory(
                UPLOAD_DIR,
                image_path.name
            )

    return (
        "Imagen no encontrada",
        404
    )


# ============================================================
# RUTA DIRECTA DEL LOGO
# ============================================================




# ============================================================
# RUTA DIRECTA DEL FONDO
# ============================================================

@app.route("/uploads/background")
def uploaded_background():

    image_path = get_image_path(
        "background"
    )

    if not image_path:

        return (
            "Fondo no encontrado",
            404
        )

    response = send_from_directory(
        UPLOAD_DIR,
        image_path.name
    )

    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    return response


# ============================================================
# ESTADO DE IMÁGENES
# ============================================================

@app.route("/uploads/status")
@admin_required
def uploads_status():

    logo = get_image_path(
        "logo"
    )

    background = get_image_path(
        "background"
    )

    return {
        "upload_directory": str(
            UPLOAD_DIR
        ),

        "logo": (
            logo.name
            if logo
            else None
        ),

        "background": (
            background.name
            if background
            else None
        )
    }


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
