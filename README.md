# TikTok HD Downloader — web privado

Aplicación sin anuncios para procesar lotes de enlaces públicos de TikTok que tienes autorización para descargar. Interfaz en español, opción de calidad, resultado ZIP e informe de éxitos y errores. No borra marcas de agua ni garantiza que una fuente entregue 1080p.

## Ejecutar en Mac / Windows / Linux

Necesitas **Python 3.11 o superior** y **FFmpeg** instalado.

1. Descomprime el ZIP y abre una terminal en esta carpeta.
2. Crea un entorno virtual y actívalo:
   - Mac/Linux: `python3 -m venv .venv && source .venv/bin/activate`
   - Windows PowerShell: `py -m venv .venv; .venv\Scripts\Activate.ps1`
3. Instala dependencias: `pip install -r requirements.txt`
4. Copia `.env.example` a `.env` y reemplaza `APP_PASSWORD` por una contraseña larga (no uses la de ejemplo).
5. Arranca con `streamlit run app.py` y abre `http://localhost:8501`.

En Mac: `brew install ffmpeg` (si utilizas Homebrew). En Windows: instala FFmpeg y asegúrate de que `ffmpeg` esté disponible en PATH.

## Usar con Docker

1. Copia `.env.example` a `.env` y cambia la contraseña.
2. Ejecuta: `docker build -t tiktok-hd-privado .`
3. Ejecuta: `docker run --rm --env-file .env -p 127.0.0.1:8501:8501 tiktok-hd-privado`
4. Abre `http://localhost:8501`.

**Privacidad:** por defecto se recomienda acceso únicamente local. Para uso remoto, ponlo detrás de HTTPS y autenticación adicional (por ejemplo, Cloudflare Access, Tailscale o proxy privado); **no publiques el puerto 8501 directamente en Internet**. La contraseña de la app es una barrera básica, no una solución de seguridad completa.

## Uso

1. Entra con la contraseña.
2. Pega hasta 200 enlaces o sube un TXT.
3. Escoge la calidad (mejor disponible, preferir 1080p o 720p).
4. Marca la confirmación de autorización.
5. Pulsa «Procesar lote» y descarga el ZIP.

## Límites

- El selector de calidad prioriza la resolución elegida, pero no escala ni mejora artificialmente videos.
- La descarga depende de la disponibilidad y restricciones de TikTok; enlaces privados, eliminados o protegidos pueden fallar.
- Un enlace no garantiza video sin marca de agua. La aplicación no quita marcas de agua.
- Los lotes se procesan de forma secuencial para mayor estabilidad; el máximo es 200 enlaces, tamaño de ZIP 1.5 GB.
- Los archivos permanecen temporalmente en el disco del servidor. Evita un servidor sin cuota de disco y limpia regularmente sus archivos temporales.
- Úsalo respetando derechos de autor, permisos de creadores y las condiciones de TikTok.
