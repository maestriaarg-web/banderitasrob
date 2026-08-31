"""Descarga los videos listados en videos.csv usando una sesion autenticada
exportada como cookies.txt (formato Netscape, ej. extension "Get cookies.txt
LOCALLY"). Reanuda automaticamente si un archivo ya existe con el tamano final.

Uso:
    .venv/Scripts/python.exe download_videos.py --cookies cookies.txt
"""

import argparse
import http.cookiejar
import sys
from pathlib import Path

import truststore

truststore.inject_into_ssl()

import requests

from common import VIDEOS_DIR, load_videos


def build_session(cookies_path: Path) -> requests.Session:
    jar = http.cookiejar.MozillaCookieJar(str(cookies_path))
    jar.load(ignore_discard=True, ignore_expires=True)
    for cookie in jar:
        # expires=0 in the Netscape file means "session cookie, no expiry",
        # but Cookie.is_expired() reads it as "expired in 1970" and would
        # silently drop it from every outgoing request.
        if cookie.expires == 0:
            cookie.expires = None
    session = requests.Session()
    session.cookies = jar
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session


def download_one(session: requests.Session, url: str, dest: Path) -> None:
    with session.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        content_type = r.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise RuntimeError(
                "La respuesta es HTML, no un video: la sesion probablemente "
                "no esta autenticada (cookies.txt vencido o incorrecto)."
            )
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
        tmp.rename(dest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookies", required=True, help="Ruta al cookies.txt exportado del navegador")
    args = parser.parse_args()

    cookies_path = Path(args.cookies)
    if not cookies_path.is_file():
        print(f"No encuentro el archivo de cookies: {cookies_path}", file=sys.stderr)
        sys.exit(1)

    session = build_session(cookies_path)
    videos = load_videos()
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    failed = []
    for v in videos:
        dest = VIDEOS_DIR / f"{v['basename']}.mp4"
        if dest.exists():
            print(f"[{v['index']:02d}/{len(videos)}] ya existe, salteo: {dest.name}")
            continue
        print(f"[{v['index']:02d}/{len(videos)}] descargando: {v['titulo']}")
        try:
            download_one(session, v["url_video"], dest)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            failed.append(v)

    if failed:
        print(f"\n{len(failed)} video(s) fallaron:")
        for v in failed:
            print(f"  - [{v['index']:02d}] {v['titulo']}")
        sys.exit(1)

    print(f"\nListo: {len(videos)} videos descargados en {VIDEOS_DIR}")


if __name__ == "__main__":
    main()
