import cv2
import numpy as np

def analyze_image(image_path):
    # Cargar la imagen
    image = cv2.imread(image_path)

    # Convertir a escala de grises
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detección de bordes
    edges = cv2.Canny(gray, 50, 150)

    # Encontrar contornos
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Procesar los contornos (Ejemplo: filtrar por tamaño)
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]

    # Dibujar contornos válidos
    result = cv2.drawContours(image.copy(), valid_contours, -1, (0, 255, 0), 2)

    # Guardar la imagen resultante
    result_path = "processed_image.jpg"
    cv2.imwrite(result_path, result)

    return result_path

