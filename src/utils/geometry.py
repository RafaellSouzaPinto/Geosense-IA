"""Utilitários de geometria para cálculos de bounding boxes e posições"""

import numpy as np
from typing import Tuple


def compute_centers(xyxy: np.ndarray) -> np.ndarray:
    """Calcula os centros das bounding boxes em formato [x1,y1,x2,y2]"""
    x1 = xyxy[:, 0]
    y1 = xyxy[:, 1]
    x2 = xyxy[:, 2]
    y2 = xyxy[:, 3]
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return np.stack([cx, cy], axis=1)


def bbox_iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula IoU entre duas caixas em formato [x1,y1,x2,y2]."""
    try:
        ax1, ay1, ax2, ay2 = float(a[0]), float(a[1]), float(a[2]), float(a[3])
        bx1, by1, bx2, by2 = float(b[0]), float(b[1]), float(b[2]), float(b[3])
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0.0, inter_x2 - inter_x1)
        inter_h = max(0.0, inter_y2 - inter_y1)
        inter = inter_w * inter_h
        area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        denom = area_a + area_b - inter
        if denom <= 0.0:
            return 0.0
        return float(inter / denom)
    except Exception:
        return 0.0


def center_distance_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    """Calcula a distância entre os centros de duas bounding boxes"""
    try:
        acx = (float(a[0]) + float(a[2])) / 2.0
        acy = (float(a[1]) + float(a[3])) / 2.0
        bcx = (float(b[0]) + float(b[2])) / 2.0
        bcy = (float(b[1]) + float(b[3])) / 2.0
        return float(np.hypot(acx - bcx, acy - bcy))
    except Exception:
        return 1e9
