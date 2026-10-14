"""
Helper script (not part of the graded template).

Reproduces the exact loops of task3.py / task4.py and reports, for every
(image, attack-strength) pair, the smallest alpha in ALPHAS whose recovered
QR code can actually be decoded. Used to fill in the tables in
subjective_answers_task3.md and subjective_answers_task4.md.
"""
import os
import cv2
import glob
import numpy as np
from dotenv import load_dotenv

from task1 import load_image_as_rgb, add_watermark_rgb, recover_watermark_rgb
from task3 import add_gaussian_noise, STDDEV, ALPHAS
from task4 import jpg_compression, QUALITY

load_dotenv()

ROLL_NO = "26210053"
_detector = cv2.QRCodeDetector()


def decodes(recovered: np.ndarray) -> bool:
    """True if a QR reader can pull the roll number out of the recovered mark."""
    img8 = (np.clip(recovered, 0, 1) * 255).astype(np.uint8)
    gray = cv2.cvtColor(img8, cv2.COLOR_RGB2GRAY)
    candidates = [
        img8,
        cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB),
        cv2.cvtColor(
            cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            cv2.COLOR_GRAY2RGB,
        ),
    ]
    for cand in candidates:
        try:
            value, _, _ = _detector.detectAndDecode(cand)
        except cv2.error:
            continue
        if value == ROLL_NO:
            return True
    return False


if __name__ == "__main__":
    image_paths = sorted(glob.glob("imgs/*.jpg"))
    images_rgb = [load_image_as_rgb(p) for p in image_paths]
    watermark_rgb = cv2.resize(load_image_as_rgb(os.getenv("watermark_path")), (321, 321))

    # ---- Task 3: Gaussian noise -------------------------------------
    np.random.seed(0)  # same seed and same loop order as task3.py
    t3 = {}
    for stddev in STDDEV:
        for alpha in ALPHAS:
            for img_idx, image in enumerate(images_rgb):
                w = add_watermark_rgb(image, watermark_rgb, alpha=alpha)
                n = add_gaussian_noise(w, stddev=stddev)
                r = recover_watermark_rgb(image, n, watermark_rgb, alpha=alpha)
                t3[(stddev, alpha, img_idx)] = decodes(r)

    print("=== TASK 3: Gaussian noise ===")
    print("stddev | " + " | ".join(f"Image {i+1}" for i in range(3)))
    for stddev in STDDEV:
        cells = []
        for img_idx in range(3):
            ok = [a for a in ALPHAS if t3[(stddev, a, img_idx)]]
            cells.append(str(min(ok)) if ok else "FAILED")
        print(f"{stddev:6} | " + " | ".join(f"{c:>7}" for c in cells))

    print("\nFull decode grid (task 3), rows=alpha, cols=(stddev, image):")
    print("alpha | " + " | ".join(f"s{s}-i{i+1}" for s in STDDEV for i in range(3)))
    for a in ALPHAS:
        print(f"{a:5} | " + " | ".join(
            ("Y" if t3[(s, a, i)] else ".").rjust(7) for s in STDDEV for i in range(3)))

    # ---- Task 4: JPEG compression -----------------------------------
    t4 = {}
    for quality in QUALITY:
        for alpha in ALPHAS:
            for img_idx, image in enumerate(images_rgb):
                w = add_watermark_rgb(image, watermark_rgb, alpha=alpha)
                c = jpg_compression(w, quality=quality)
                r = recover_watermark_rgb(image, c, watermark_rgb, alpha=alpha)
                t4[(quality, alpha, img_idx)] = decodes(r)

    print("\n=== TASK 4: JPEG compression ===")
    print("quality | " + " | ".join(f"Image {i+1}" for i in range(3)))
    for quality in QUALITY:
        cells = []
        for img_idx in range(3):
            ok = [a for a in ALPHAS if t4[(quality, a, img_idx)]]
            cells.append(str(min(ok)) if ok else "FAILED")
        print(f"{quality:7} | " + " | ".join(f"{c:>7}" for c in cells))

    print("\nFull decode grid (task 4), rows=alpha, cols=(quality, image):")
    print("alpha | " + " | ".join(f"q{q}-i{i+1}" for q in QUALITY for i in range(3)))
    for a in ALPHAS:
        print(f"{a:5} | " + " | ".join(
            ("Y" if t4[(q, a, i)] else ".").rjust(6) for q in QUALITY for i in range(3)))
