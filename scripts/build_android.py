#!/usr/bin/env python3
"""Small native Android build using the official SDK (no Gradle dependency).

Set ANDROID_SDK_ROOT, or pass --platform and --build-tools. A release keystore
must be supplied to sign the result. Never commit the keystore or its passwords.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
from prepare_android_assets import prepare, ROOT


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def main():
    sdk = Path(os.environ.get("ANDROID_SDK_ROOT", os.environ.get("ANDROID_HOME", "/opt/android-sdk")))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", type=Path, default=sdk / "platforms/android-35/android.jar")
    parser.add_argument("--build-tools", type=Path, default=sdk / "build-tools/35.0.0")
    parser.add_argument("--ecj", type=Path, help="Optional Eclipse compiler jar when javac is unavailable")
    parser.add_argument("--keystore", type=Path, required=True)
    parser.add_argument("--alias", default="resolutionmaths")
    parser.add_argument("--preview", action="store_true", help="Separate testing application; never replaces a release")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/Resolution-Maths-1.1.0.apk")
    args = parser.parse_args()
    for name in ["ANDROID_KEYSTORE_PASSWORD", "ANDROID_KEY_PASSWORD"]:
        if not os.environ.get(name): parser.error(f"Missing {name}")
    if not args.platform.is_file(): parser.error(f"Missing Android 35 platform: {args.platform}")
    if not args.keystore.is_file(): parser.error("The signing keystore does not exist")
    prepare()
    build = ROOT / "android/build"
    src = ROOT / "android/app/src/main"
    for directory in ["gen", "classes", "dex"]:
        shutil.rmtree(build / directory, ignore_errors=True)
        (build / directory).mkdir()
    tools = args.build_tools
    manifest = src / "AndroidManifest.xml"
    if args.preview:
        text = manifest.read_text().replace('package="mg.resolutionmaths.app"', 'package="mg.resolutionmaths.preview"')
        text = text.replace('android:label="Résolution Maths"', 'android:label="Résolution Maths Test"')
        text = text.replace('android:versionName="1.1.0"', 'android:versionName="1.1.0-test"')
        manifest = build / "preview-AndroidManifest.xml"
        manifest.write_text(text)
    run(tools / "aapt", "package", "-f", "-M", manifest, "-S", src / "res",
        "-A", build / "assets", "-I", args.platform, "-J", build / "gen", "-F", build / "resources.apk")
    sources = list((src / "java").rglob("*.java")) + list((build / "gen").rglob("*.java"))
    compiler = ["java", "-jar", args.ecj, "-1.8", "-proc:none"] if args.ecj else ["javac", "-source", "8", "-target", "8"]
    bootclasspath = os.pathsep.join([str(args.platform), str(tools / "core-lambda-stubs.jar")])
    run(*compiler, "-encoding", "UTF-8", "-bootclasspath", bootclasspath, "-d", build / "classes", *sources)
    class_archive = build / "classes.jar"
    with zipfile.ZipFile(class_archive, "w") as archive:
        for file in (build / "classes").rglob("*.class"):
            archive.write(file, file.relative_to(build / "classes"))
    run("java", "-cp", tools / "lib/d8.jar", "com.android.tools.r8.D8", "--release", "--min-api", "26",
        "--lib", args.platform, "--lib", tools / "core-lambda-stubs.jar", "--output", build / "dex", class_archive)
    with zipfile.ZipFile(build / "resources.apk", "a", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in (build / "dex").glob("*.dex"):
            archive.write(file, file.name)
    run(tools / "zipalign", "-f", "-p", "4", build / "resources.apk", build / "aligned.apk")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    run("java", "-jar", tools / "lib/apksigner.jar", "sign", "--ks", args.keystore,
        "--ks-key-alias", args.alias, "--ks-pass", "env:ANDROID_KEYSTORE_PASSWORD",
        "--key-pass", "env:ANDROID_KEY_PASSWORD", "--out", args.output, build / "aligned.apk")
    run("java", "-jar", tools / "lib/apksigner.jar", "verify", "--verbose", args.output)
    run(tools / "aapt", "dump", "badging", args.output)
    print(f"APK: {args.output} ({args.output.stat().st_size / 1024**2:.1f} MiB)")


if __name__ == "__main__":
    main()
