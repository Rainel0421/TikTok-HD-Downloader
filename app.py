from __future__ import annotations

import hmac
import os
import re
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="TikTok Enterprise HD Downloader",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para un diseño altamente profesional y moderno
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    .custom-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #1a1c24;
        border: 1px solid #2d3139;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

ALLOWED_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}
MAX_LINKS = 25
MAX_ZIP_BYTES = 1_500_000_000  # 1.5 GB


def valid_tiktok_url(candidate: str) -> bool:
    try:
        parsed = urlparse(candidate)
        return (parsed.scheme == "https" and 
                (parsed.hostname or "").lower() in ALLOWED_HOSTS and 
                bool(parsed.path.strip("/")) and 
                not parsed.username and 
                not parsed.password)
    except ValueError:
        return False


def parse_links(raw: str) -> tuple[list[str], list[str]]:
    found = re.findall(r"https?://[^\s<>\"']+", raw)
    valid, invalid, seen = [], [], set()
    for item in found:
        item = item.rstrip(".,;)]}")
        if valid_tiktok_url(item):
            if item not in seen:
                valid.append(item)
                seen.add(item)
        else:
            invalid.append(item)
    return valid, invalid


def password_gate() -> None:
    password = os.getenv("APP_PASSWORD", "")
    if not password or password == "CAMBIAME_POR_UNA_CLAVE_LARGA":
        st.error("⚠️ Configura la variable `APP_PASSWORD` en tu archivo `.env` antes de iniciar la aplicación.")
        st.stop()
    if st.session_state.get("authenticated", False):
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### 🔒 Acceso Privado Requerido")
        st.caption("Introduce la contraseña maestra para acceder a la plataforma.")
        with st.form("login_form"):
            value = st.text_input("Contraseña de Acceso", type="password")
            submit = st.form_submit_button("Desbloquear Sistema", type="primary", use_container_width=True)
        if submit:
            if hmac.compare_digest(value.encode(), password.encode()):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
    st.stop()


def download_one(url: str, dest: Path, number: int, quality: str) -> list[Path]:
    base = f"{number:03d}_%(uploader|autor)s_%(id)s.%(ext)s"
    opts = {
        "format": "bv*+ba/b",
        "outtmpl": str(dest / base),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "retries": 5,
        "fragment_retries": 5,
        "socket_timeout": 30,
        "max_filesize": 400 * 1024 * 1024,
        "ignoreerrors": False,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.tiktok.com/",
        },
        "extractor_args": {
            "tiktok": {
                "api_hostname": ["api16-normal-c-useast1a.tiktokv.com"],
                "app_version": ["30.3.2"],
                "app_name": ["trill"],
                "device_id": ["7318518857994389254"],
            }
        },
    }
    if quality == "1080":
        opts["format_sort"] = ["res:1080", "fps"]
    elif quality == "720":
        opts["format_sort"] = ["res:720", "fps"]
        
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return [f for f in dest.iterdir() if f.is_file() and f.name.startswith(f"{number:03d}_") and not f.name.endswith((".part", ".ytdl"))]


def build_zip(folder: Path, report: list[str], target: Path) -> tuple[int, int]:
    files = sorted(f for f in folder.iterdir() if f.is_file())
    total = sum(f.stat().st_size for f in files)
    if total > MAX_ZIP_BYTES:
        raise ValueError("Los videos superan el límite de 1.5 GB. Divide la lista en lotes más pequeños.")
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for file in files:
            zf.write(file, arcname=file.name)
        zf.writestr("informe_lote.txt", "\n".join(report))
    return len(files), total


# Ejecutar control de acceso
password_gate()

# ── Header Principal ─────────────────────────────────────────────────────────
st.title("🎬 TikTok Enterprise HD Downloader")
st.caption("Plataforma profesional para la extracción masiva, privada y optimizada de contenido multimedia en alta calidad.")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/tiktok.png", width=100)
    st.subheader("Panel de Control")
    st.success("🟢 Sesión Segura Activa")
    
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()
        
    st.divider()
    st.markdown("### 📌 Pautas de Uso")
    st.info("Utiliza únicamente URLs de contenido propio o autorizado bajo los términos de servicio de la plataforma de origen.")
    st.markdown("---")
    

# ── Paso 1: Ingreso de Enlaces ────────────────────────────────────────────────
st.subheader("1. Ingesta de Enlaces")
col_input1, col_input2 = st.columns([2, 1])

with col_input1:
    raw = st.text_area(
        "Pegue los enlaces (uno por línea)",
        height=160,
        placeholder="https://www.tiktok.com/@usuario/video/123456789..."
    )

with col_input2:
    st.markdown("<br>", unsafe_allow_html=True)
    upload = st.file_uploader("O cargue un archivo TXT", type=["txt"])
    if upload is not None:
        raw += "\n" + upload.getvalue().decode("utf-8-sig", errors="replace")

links, invalid = parse_links(raw)

# Métricas rápidas de validación
m1, m2, m3 = st.columns(3)
m1.metric("Enlaces Válidos", len(links), delta=f"Máx. {MAX_LINKS}")
m2.metric("No Válidos / Filtrados", len(invalid))
m3.metric("Límite de Lote", f"{max(0, MAX_LINKS - len(links))} disponibles")

if invalid:
    st.warning(f"⚠️ Se omitieron {len(invalid)} elementos por no coincidir con el formato HTTPS válido de TikTok.")

st.divider()

# ── Paso 2: Configuración del Lote ───────────────────────────────────────────
st.subheader("2. Parámetros de Procesamiento")
col1, col2, col3 = st.columns(3)

with col1:
    quality = st.selectbox(
        "Calidad Objetivo", 
        ["Mejor disponible", "Hasta 1080p (preferida)", "Hasta 720p (preferida)"]
    )
with col2:
    output_mode = st.selectbox(
        "Modo de Entrega",
        ["ZIP (Archivo comprimido único)", "Videos individuales (Acceso directo)"],
        help="Elija si prefiere un archivo ZIP consolidado o botones separados por video."
    )
with col3:
    st.text_input("Restricciones del Servidor", value="Máx. 200 URLs · 1.5 GB", disabled=True)

permission = st.checkbox("✔️ Confirmo que poseo los derechos de autor, autorizaciones o permisos necesarios para descargar y procesar este contenido.")

st.divider()

# ── Paso 3: Ejecución ────────────────────────────────────────────────────────
st.subheader("3. Ejecución y Descarga")
process_btn = st.button("🚀 Iniciar Procesamiento por Lotes", type="primary", disabled=not (0 < len(links) <= MAX_LINKS and permission), use_container_width=True)

if process_btn:
    jobdir = Path(tempfile.mkdtemp(prefix="tiktok_hd_"))
    video_dir = jobdir / "videos"
    video_dir.mkdir()
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    reports = ["TikTok HD Downloader - Informe de Lote", f"Fecha de ejecución: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    success_count = 0
    quality_key = "1080" if quality.startswith("Hasta 1080") else "720" if quality.startswith("Hasta 720") else "best"
    downloaded_videos: list[tuple[str, Path]] = []

    for index, link in enumerate(links, 1):
        status_text.text(f"⏳ Procesando elemento {index} de {len(links)}...")
        try:
            created = download_one(link, video_dir, index, quality_key)
            if not created:
                raise RuntimeError("No se generó ningún archivo multimedia válido.")
            success_count += 1
            reports.append(f"EX ÉXITO | {link} | {', '.join(p.name for p in created)}")
            for p in created:
                downloaded_videos.append((p.name, p))
        except Exception as exc:
            err_msg = str(exc).replace("\n", " ")[:250]
            reports.append(f"ERROR | {link} | {err_msg}")
        progress_bar.progress(index / len(links))

    progress_bar.empty()
    status_text.empty()

    if success_count > 0:
        if "ZIP" in output_mode:
            zip_path = jobdir / "tiktok_enterprise_bundle.zip"
            try:
                count, bytes_size = build_zip(video_dir, reports, zip_path)
                st.session_state["zip_path"] = str(zip_path)
                st.session_state["individual_videos"] = []
                st.session_state["summary"] = (success_count, len(links), count, round(bytes_size / (1024 ** 2), 1))
                st.success(f"🎉 Lote finalizado con éxito: {success_count} de {len(links)} videos procesados correctamente.")
            except Exception as exc:
                st.session_state.pop("zip_path", None)
                st.error(f"❌ Error al empaquetar: {exc}")
        else:
            st.session_state.pop("zip_path", None)
            st.session_state["individual_videos"] = [(name, str(path)) for name, path in downloaded_videos]
            st.session_state["summary"] = (success_count, len(links), len(downloaded_videos), 0)
            st.success(f"🎉 Lote finalizado con éxito: {success_count} de {len(links)} videos listos para descarga individual.")
    else:
        st.session_state.pop("zip_path", None)
        st.session_state["individual_videos"] = []
        st.error("❌ Ningún video pudo ser descargado. Verifique los enlaces ingresados o restricciones de la plataforma origen.")
        with st.expander("Ver informe detallado de errores"):
            st.text_area("Logs de Errores", "\n".join(reports), height=150)

# ── Área de Resultados y Descargas ───────────────────────────────────────────
zip_path_str = st.session_state.get("zip_path", "")
path_zip = Path(zip_path_str) if zip_path_str else None

if path_zip and path_zip.is_file():
    ok, total, files_count, size_mb = st.session_state.get("summary", (0, 0, 0, 0))
    st.markdown("### 📦 Archivo Consolidado Listo")
    st.info(f"📊 **Estadísticas:** {ok}/{total} exitosos · {files_count} archivos multimedia · {size_mb} MB (sin comprimir)")
    
    with path_zip.open("rb") as f_zip:
        st.download_button(
            label="⬇️ Descargar Paquete ZIP Completo",
            data=f_zip,
            file_name="tiktok_enterprise_bundle.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

individual_items = st.session_state.get("individual_videos", [])
if individual_items:
    ok, total, files_count, _ = st.session_state.get("summary", (0, 0, 0, 0))
    st.markdown("### 📂 Enlaces de Descarga Individual")
    st.success(f"📊 **Estadísticas:** {ok}/{total} exitosos · {files_count} archivos listos")
    
    for name, path_str in individual_items:
        p_item = Path(path_str)
        if p_item.is_file():
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                st.code(name, language=None)
            with col_d2:
                with p_item.open("rb") as f_ind:
                    st.download_button(
                        label="⬇️ Descargar",
                        data=f_ind,
                        file_name=name,
                        mime="video/mp4",
                        key=f"dl_{name}",
                        use_container_width=True
                    )