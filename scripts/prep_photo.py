#!/usr/bin/env python3
"""
Prep a photo for ASCII conversion. Run once per photo (locally):

    python scripts/prep_photo.py source-photo.jpg

A flatly-lit face converts to a dark, unreadable blob. Three steps fix that:
  1. Remove the background with rembg so the subject is isolated.
  2. Boost local contrast with OpenCV CLAHE (contrast-limited adaptive
     histogram equalization) -- gives a flat face real highlights/shadows.
  3. Composite onto pure white so the background maps to the blank end of the
     ASCII ramp (white -> spaces).

Output: source-prepped.png (grayscale). Then run make_ascii_svg.py.

Requires: pillow numpy opencv-python rembg
    pip install pillow numpy opencv-python rembg
"""
import os
import sys

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "source-prepped.png")


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/prep_photo.py <photo.jpg>")
        sys.exit(1)
    src = sys.argv[1]
    if not os.path.exists(src):
        print(f"not found: {src}")
        sys.exit(1)

    try:
        import cv2
        import numpy as np
        from PIL import Image
        from rembg import remove
    except ImportError as e:
        print(f"missing dependency: {e}\n"
              "pip install pillow numpy opencv-python rembg")
        sys.exit(1)

    # 1. isolate subject (RGBA with transparent background)
    with open(src, "rb") as f:
        cut = remove(f.read())
    tmp = os.path.join(HERE, "..", "_cut.png")
    with open(tmp, "wb") as f:
        f.write(cut)
    rgba = Image.open(tmp).convert("RGBA")

    # 2. composite onto pure white
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white, rgba).convert("L")

    # 3. CLAHE local contrast boost
    arr = np.array(comp)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # keep the isolated background pure white so it maps to spaces
    alpha = np.array(rgba.split()[-1])
    arr[alpha < 10] = 255

    Image.fromarray(arr).save(OUT)
    try:
        os.remove(tmp)
    except OSError:
        pass
    print(f"[prep] wrote {OUT}  ({comp.size[0]}x{comp.size[1]})")


if __name__ == "__main__":
    main()
