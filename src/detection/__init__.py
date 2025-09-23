"""Módulo de detecção e rastreamento para o GeoSense"""

from .yolo_detector import YoloDetector
from .tracker import MotorcycleTracker

__all__ = ["YoloDetector", "MotorcycleTracker"]
