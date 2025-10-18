"""Image processing helpers exposed through the API."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency guarded during import
    import numpy as np
except Exception as exc:  # pragma: no cover - handled at runtime
    np = None  # type: ignore[assignment]
    NUMPY_ERROR = exc
else:
    NUMPY_ERROR = None

try:  # pragma: no cover - optional dependency guarded during import
    import cv2
except Exception as exc:  # pragma: no cover - handled at runtime
    cv2 = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@dataclass
class DiceProcessingError(RuntimeError):
    """Raised when the uploaded image cannot be processed."""

    message: str


def _ensure_cv2() -> None:
    if cv2 is None or IMPORT_ERROR is not None or np is None or NUMPY_ERROR is not None:
        raise DiceProcessingError("OpenCV no está disponible en el servidor.")


def analyse_dice_image(file_bytes: bytes) -> Dict[str, Any]:
    """Analyse the uploaded dice image and return statistics."""

    _ensure_cv2()

    if not file_bytes:
        raise DiceProcessingError("La imagen recibida está vacía.")

    np_buffer = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise DiceProcessingError("No se pudo decodificar la imagen proporcionada.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    pip_contours: List[Any] = []
    bounding_boxes: List[Dict[str, int]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if 20 <= area <= 2000:
            pip_contours.append(contour)
            x, y, w, h = cv2.boundingRect(contour)
            bounding_boxes.append({"x": int(x), "y": int(y), "width": int(w), "height": int(h)})

    annotated = image.copy()
    if pip_contours:
        cv2.drawContours(annotated, pip_contours, -1, (0, 255, 0), 2)

    success, buffer = cv2.imencode(".jpg", annotated)
    if not success:
        raise DiceProcessingError("No se pudo generar la vista previa procesada.")

    encoded_preview = base64.b64encode(buffer.tobytes()).decode("ascii")

    return {
        "pip_count": len(pip_contours),
        "bounding_boxes": bounding_boxes,
        "preview_image": encoded_preview,
    }
