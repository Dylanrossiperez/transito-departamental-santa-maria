# Sitio web — Tránsito / Departamental Santa María

Proyecto web en Python + Flask con temática institucional policial y el escudo proporcionado.

## Funciones

- Página pública responsive.
- Secciones: inicio, información, seguridad vial, contacto y aviso institucional.
- Panel de administración en `/admin`.
- Los textos principales se editan desde el navegador.
- La información se guarda en SQLite.
- El escudo está incluido en `app/static/escudo-policia-cordoba.jpeg`.

## Ejecutar

### Windows
1. Instalar Python 3.11 o superior.
2. Abrir una terminal en esta carpeta.
3. Ejecutar:
   `python -m venv .venv`
4. Activar:
   `.venv\Scripts\activate`
5. Instalar:
   `pip install -r requirements.txt`
6. Ejecutar:
   `python app.py`
7. Abrir:
   `http://127.0.0.1:5000`

También se puede ejecutar `run_windows.bat`.

### Linux/macOS
Ejecutar:
`chmod +x run_linux_mac.sh`
`./run_linux_mac.sh`

## Acceso al panel

URL: `http://127.0.0.1:5000/login`

Contraseña inicial de demostración: `transito2026`

**Importante:** cambiar la contraseña y `app.secret_key` antes de publicar el sitio en Internet.

## Nota institucional

Los teléfonos, horarios y otros datos que aparecen como "A completar" son marcadores editables y no deben interpretarse como información oficial. Antes de usar el sitio públicamente, cargar los datos oficiales y verificar las autorizaciones correspondientes.
