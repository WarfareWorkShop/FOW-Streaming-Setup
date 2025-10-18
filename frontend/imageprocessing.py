"""Utility helpers for basic image processing tasks."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import cv2


class ImageProcessingError(RuntimeError):
    """Raised when the provided image cannot be processed."""


def _resolve_path(image_path: str | os.PathLike[str]) -> Path:
    if not image_path:
        raise ImageProcessingError("No image path was provided.")
    return Path(image_path)


def analyze_image(image_path: str | os.PathLike[str]) -> str:
    """Analyse the given image and save a processed copy.

    The function validates that the image can be loaded before attempting any
    processing and writes the result to a unique temporary file to avoid
    collisions.
    """

    source_path = _resolve_path(image_path)
    image = cv2.imread(str(source_path))
    if image is None:
        raise ImageProcessingError(f"Could not read image at {source_path}.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]
    result = cv2.drawContours(image.copy(), valid_contours, -1, (0, 255, 0), 2)

    fd, result_path = tempfile.mkstemp(prefix="processed_", suffix=".jpg")
    os.close(fd)
    cv2.imwrite(result_path, result)

    return result_path
