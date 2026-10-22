#!/usr/bin/env python3
"""Bundle the tested web application and pinned math dependencies into the APK.

Downloads are required only when building, never when running the Android app.
The website itself keeps its existing CDN configuration.
"""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "android/build/assets/www"
CACHE = ROOT / "android/build/downloads"
PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.29.5/full/"
KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/"


def download(url, destination, checksum=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            data = response.read()
        temporary = destination.with_suffix(destination.suffix + ".part")
        temporary.write_bytes(data)
        temporary.replace(destination)
    data = destination.read_bytes()
    if checksum and hashlib.sha256(data).hexdigest() != checksum:
        raise ValueError(f"Checksum mismatch: {destination.name}")
    return data


def prepare():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name in ["index.html", "styles.css", "app.js", "worker.js", "solver.py", "icon.svg", "manifest.webmanifest", "LICENSE"]:
        shutil.copyfile(ROOT / name, ASSETS / name)
    lock = json.loads(download(PYODIDE + "pyodide-lock.json", CACHE / "pyodide/pyodide-lock.json"))
    tasks = []
    for name in ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]:
        tasks.append((PYODIDE + name, CACHE / "pyodide" / name, None))
    for package in ["sympy", "mpmath"]:
        entry = lock["packages"][package]
        tasks.append((PYODIDE + entry["file_name"], CACHE / "pyodide" / entry["file_name"], entry["sha256"]))
    css = download(KATEX + "katex.min.css", CACHE / "katex/katex.min.css").decode()
    for name in ["katex.min.js"] + re.findall(r"url\((fonts/[^)]+)\)", css):
        tasks.append((KATEX + name, CACHE / "katex" / name, None))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda args: download(*args), tasks))
    for vendor in ["pyodide", "katex"]:
        shutil.copytree(CACHE / vendor, ASSETS / "vendor" / vendor, dirs_exist_ok=True)
    page = (ASSETS / "index.html").read_text()
    page = page.replace(KATEX, "./vendor/katex/")
    (ASSETS / "index.html").write_text(page)
    worker = (ASSETS / "worker.js").read_text().replace(PYODIDE, "./vendor/pyodide/")
    worker = worker.replace("Téléchargement du moteur…", "Initialisation du moteur local…")
    (ASSETS / "worker.js").write_text(worker)
    app = (ASSETS / "app.js").read_text()
    app = app.replace("if('serviceWorker' in navigator && location.protocol==='https:')", "if(false)")
    app = app.replace("Chargement du moteur impossible. Vérifiez votre connexion.", "Chargement du moteur impossible. Fermez puis rouvrez l’application.")
    app = app.replace("Le moteur ne répond pas. Vérifiez la connexion ou simplifiez le calcul.", "Le calcul prend trop de temps. Essayez une expression plus simple.")
    app = app.replace("dans ce navigateur", "sur cet appareil").replace("dans ce navigateur", "sur cet appareil")
    (ASSETS / "app.js").write_text(app)
    page = (ASSETS / "index.html").read_text().replace("dans ce navigateur", "sur cet appareil")
    (ASSETS / "index.html").write_text(page)
    licenses = {
        "Pyodide-LICENSE.txt": "https://raw.githubusercontent.com/pyodide/pyodide/0.29.5/LICENSE",
        "KaTeX-LICENSE.txt": "https://cdn.jsdelivr.net/npm/katex@0.16.22/LICENSE",
    }
    for name, url in licenses.items():
        download(url, ASSETS / "licenses" / name)
    (ASSETS / "THIRD_PARTY.txt").write_text(
        "Pyodide 0.29.5 (Mozilla Public License 2.0), including CPython (PSF license).\n"
        "SymPy 1.13.3 (BSD), mpmath 1.3.0 (BSD); licenses are included in their wheels.\n"
        "KaTeX 0.16.22 (MIT). See licenses/ and https://pyodide.org/.\n")
    files = list(ASSETS.rglob("*"))
    print(f"Bundled {sum(p.is_file() for p in files)} files, "
          f"{sum(p.stat().st_size for p in files if p.is_file()) / 1024**2:.1f} MiB")
    return ASSETS


if __name__ == "__main__":
    prepare()
