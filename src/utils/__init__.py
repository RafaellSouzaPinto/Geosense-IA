"""Módulo de utilitários para o GeoSense"""

from .geometry import compute_centers, bbox_iou_xyxy, center_distance_xyxy
from .zones import read_zones_config
from .io_utils import (
    is_webcam_source, 
    is_image_file, 
    gather_media_files,
    safe_read_line
)

__all__ = [
    "compute_centers",
    "bbox_iou_xyxy", 
    "center_distance_xyxy",
    "read_zones_config",
    "is_webcam_source",
    "is_image_file",
    "gather_media_files", 
    "safe_read_line"
]
