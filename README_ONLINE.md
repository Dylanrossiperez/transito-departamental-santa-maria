# Publicación online

La configuración `render.yaml` deja el sitio listo para Render.

**Importante:** la configuración usa un disco persistente de Render para que los cambios realizados desde `/admin` no se pierdan al reiniciar o redeployar. Los discos persistentes requieren un servicio pago en Render.

1. Subir este proyecto a un repositorio de GitHub.
2. En Render: New > Blueprint.
3. Conectar el repositorio y usar `render.yaml`.
4. Esperar el deploy.
5. Abrir la URL `https://...onrender.com`.
6. Administrar desde `/admin`.

La contraseña de administración sigue siendo la definida en `app.py` (`transito2026`) hasta que se cambie en el código. Para un sitio público real conviene reemplazarla por un sistema de usuarios/contraseñas seguro antes de publicarlo.
