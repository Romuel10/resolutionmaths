#!/usr/bin/env python3
"""Generate the native and web √x brand from one set of vector coordinates.

Requires Pillow only when editing the artwork. Generated resources are committed,
so APK builds do not need Pillow. The foreground fits the adaptive icon safe zone.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "android/app/src/main/res"
NAVY = "#14233f"
WHITE = "#f4fbff"
MINT = "#7fe0c3"
RADICAL = [(27, 53), (35, 49), (42, 65), (55, 30), (76, 30),
           (76, 39), (61, 39), (47, 78), (38, 78), (31, 58), (27, 60)]
LETTER_X = [(58, 48), (64, 48), (67, 53), (70, 48), (76, 48), (70, 58),
            (76, 68), (70, 68), (67, 63), (64, 68), (58, 68), (64, 58)]
REGULAR = "resolutionmaths_launcher"
ROUND = "resolutionmaths_launcher_round"


def path(points):
    return "M" + " L".join(f"{x},{y}" for x, y in points) + " Z"


def vector(monochrome=False):
    return ('''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
'''
        + f'    <path android:fillColor="{WHITE}" android:pathData="{path(RADICAL)}" />\n'
        + f'    <path android:fillColor="{WHITE if monochrome else MINT}" android:pathData="{path(LETTER_X)}" />\n'
        + '</vector>\n')


def adaptive(themed=False):
    return ('''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/resolutionmaths_icon_background" />
    <foreground android:drawable="@drawable/resolutionmaths_logo_foreground" />
'''
        + ('    <monochrome android:drawable="@drawable/resolutionmaths_logo_monochrome" />\n' if themed else '')
        + '</adaptive-icon>\n')


def bitmap(size, round_icon=False):
    # Render above the target resolution, then downsample for clean small icons.
    factor = 6
    canvas = Image.new("RGBA", (size * factor, size * factor))
    draw = ImageDraw.Draw(canvas)
    bounds = (0, 0, size * factor - 1, size * factor - 1)
    if round_icon:
        draw.ellipse(bounds, fill=NAVY)
    else:
        draw.rounded_rectangle(bounds, radius=16 / 72 * size * factor, fill=NAVY)
    scale = size * factor / 72
    for points, color in [(RADICAL, WHITE), (LETTER_X, MINT)]:
        draw.polygon([((x - 18) * scale, (y - 18) * scale) for x, y in points], fill=color)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def main():
    for points in [RADICAL, LETTER_X]:
        if any((x - 54) ** 2 + (y - 54) ** 2 > 33 ** 2 for x, y in points):
            raise ValueError("The logo would extend outside the adaptive icon safe circle")
    drawables = RES / "drawable"
    drawables.mkdir(parents=True, exist_ok=True)
    (drawables / "resolutionmaths_logo_foreground.xml").write_text(vector())
    (drawables / "resolutionmaths_logo_monochrome.xml").write_text(vector(True))
    for api in [26, 33]:
        directory = RES / f"mipmap-anydpi-v{api}"
        directory.mkdir(parents=True, exist_ok=True)
        for name in [REGULAR, ROUND]:
            (directory / f"{name}.xml").write_text(adaptive(api >= 33))
    for density, size in [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)]:
        directory = RES / f"mipmap-{density}"
        directory.mkdir(parents=True, exist_ok=True)
        bitmap(size).save(directory / f"{REGULAR}.png", optimize=True)
        bitmap(size, True).save(directory / f"{ROUND}.png", optimize=True)
    artwork = ROOT / "android/branding"
    artwork.mkdir(parents=True, exist_ok=True)
    bitmap(512).save(artwork / "resolution-maths-icon.png", optimize=True)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 72 72">'
           f'<rect x="18" y="18" width="72" height="72" rx="16" fill="{NAVY}"/>'
           f'<path d="{path(RADICAL)}" fill="{WHITE}"/>'
           f'<path d="{path(LETTER_X)}" fill="{MINT}"/></svg>\n')
    (ROOT / "icon.svg").write_text(svg)
    print("Generated √x icons: 10 density PNGs, 4 adaptive resources, themed layer and 512px artwork.")


if __name__ == "__main__":
    main()
