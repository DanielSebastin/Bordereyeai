from __future__ import annotations
# ANPR text validation + character rectification.
#
# Ported from the tutorial pipeline:
#   https://github.com/computervisioneng/automatic-number-plate-recognition-python-yolov8
# (util.py, MIT-licensed tutorial code) and adapted to our OCR engine.
#
# Purpose: OCR gives ambiguous glyphs (O/0, I/1, S/5, G/6, J/3, A/4, B/8).
# For plates that match the common LL-DD-LLL layout these are corrected per
# position; anything else is returned as-is (never destroyed).
#
# FIX 5  — complies_format() now uses all() instead of any() per zone.
# FIX 6  — _enhance_plate() centralised here so anpr_ocr.py / camera_runner.py
#           / main.py all import from one place instead of duplicating it.

import cv2

# ---------------------------------------------------------------------------
# Character substitution maps
# ---------------------------------------------------------------------------
# Letters that look like digits (in the letter zones of a plate):
#   O→0, I→1, J→3, A→4, G→6, S→5
LETTER_TO_DIGIT = {"O": "0", "I": "1", "J": "3", "A": "4", "G": "6", "S": "5"}
# Digits that look like letters (in the digit zones of a plate):
#   0→O, 1→I, 3→J, 4→A, 6→G, 5→S
DIGIT_TO_LETTER = {"0": "O", "1": "I", "3": "J", "4": "A", "6": "G", "5": "S"}

# Pre-built sets for O(1) membership tests.
_VALID_LETTERS: frozenset[str] = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_DIGIT_OR_DIGIT_LIKE: frozenset[str] = frozenset("0123456789") | frozenset(LETTER_TO_DIGIT)
_LETTER_OR_LETTER_LIKE: frozenset[str] = _VALID_LETTERS | frozenset(DIGIT_TO_LETTER)


def _clean(text: str) -> str:
    """Strip non-alphanumeric characters and upper-case."""
    return "".join(ch for ch in text.upper() if ch.isalnum())


def complies_format(text: str) -> bool:
    """Return True if *text* (already cleaned, length 7) fits the LL-DD-LLL
    licence-plate layout, accounting for common OCR glyph confusions.

    FIX 5 — Previously used any() which allowed a single correct character to
    mask garbage in the same zone.  Now uses all() so **every** character in
    each zone must be valid for its expected type:

      pos 0,1   → letter zone  (A-Z, or a digit easily confused with a letter)
      pos 2,3   → digit zone   (0-9, or a letter easily confused with a digit)
      pos 4,5,6 → letter zone  (A-Z, or a digit easily confused with a letter)
    """
    if len(text) != 7:
        return False

    # All characters in the first letter zone must be letter-like.
    letter_zone_1_ok = all(c in _LETTER_OR_LETTER_LIKE for c in (text[0], text[1]))

    # All characters in the digit zone must be digit-like.
    digit_zone_ok = all(c in _DIGIT_OR_DIGIT_LIKE for c in (text[2], text[3]))

    # All characters in the second letter zone must be letter-like.
    letter_zone_2_ok = all(c in _LETTER_OR_LETTER_LIKE for c in (text[4], text[5], text[6]))

    return letter_zone_1_ok and digit_zone_ok and letter_zone_2_ok


def format_license(text: str) -> str:
    """Rectify a 7-char LL-DD-LLL plate in place using the per-position maps."""
    mapping = {
        0: DIGIT_TO_LETTER,
        1: DIGIT_TO_LETTER,
        4: DIGIT_TO_LETTER,
        5: DIGIT_TO_LETTER,
        6: DIGIT_TO_LETTER,
        2: LETTER_TO_DIGIT,
        3: LETTER_TO_DIGIT,
    }
    out = []
    for i, ch in enumerate(text):
        out.append(mapping[i].get(ch, ch))
    return "".join(out)


def refine_plate(raw_text: str) -> str | None:
    """Validate+rectify an OCR plate candidate.  Returns None for garbage."""
    t = _clean(raw_text)
    if len(t) < 4 or len(t) > 12:
        return None
    if len(t) == 7 and complies_format(t):
        return format_license(t)
    return t


# ---------------------------------------------------------------------------
# FIX 6 — Shared image-enhancement helper (single source of truth).
#
# Previously duplicated verbatim in:
#   backend/app/vision/anpr_ocr.py        (_enhance_plate)
#   backend/app/vision/camera_runner.py   (_enhance_plate)
#   backend/app/vision/main.py            (_enhance_plate)
#
# All three files now import this function instead.
# ---------------------------------------------------------------------------
def enhance_plate(crop_bgr) -> "cv2.Mat":
    """Grayscale + CLAHE + upscale to make small plates OCR-readable.

    Scales 2× for wide crops (≥ 360 px wide) to save CPU, 3× for smaller
    crops where plate text is tiny.  Followed by median blur to kill salt-
    and-pepper noise introduced by resizing.
    """
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    fx = 2.0 if gray.shape[1] >= 360 else 3.0
    gray = cv2.resize(gray, None, fx=fx, fy=fx, interpolation=cv2.INTER_CUBIC)
    gray = cv2.createCLAHE(3.0, (8, 8)).apply(gray)
    return cv2.medianBlur(gray, 3)