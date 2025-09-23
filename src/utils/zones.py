"""Utilitários para configuração e manipulação de zonas de detecção"""

import json
import numpy as np
from typing import Any, Dict, List, Optional, Sequence, Tuple


def read_zones_config(
    zones_path: str, frame_width: int, frame_height: int
) -> List[Dict[str, Any]]:
    """Lê configuração de zonas de um arquivo JSON e ajusta para o tamanho do frame"""
    with open(zones_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    normalized = bool(data.get("normalized", False))
    ref_w, ref_h = None, None
    if "frame_reference" in data and isinstance(data["frame_reference"], (list, tuple)):
        ref_w, ref_h = int(data["frame_reference"][0]), int(data["frame_reference"][1])

    zones_out: List[Dict[str, Any]] = []
    for zone in data.get("zones", []):
        display_id = str(
            zone.get("name")
            or zone.get("label")
            or zone.get("id", f"Setor {len(zones_out)+1}")
        )
        pts: Sequence[Sequence[float]] = zone.get("points", [])
        pts_np = np.array(pts, dtype=float)

        if normalized:
            if ref_w and ref_h:
                scale_x = frame_width
                scale_y = frame_height
            else:
                scale_x = frame_width
                scale_y = frame_height
            pts_px = np.column_stack((pts_np[:, 0] * scale_x, pts_np[:, 1] * scale_y))
        else:
            pts_px = pts_np

        color_value: Optional[Tuple[int, int, int]] = None
        col = zone.get("color")
        if isinstance(col, list) and len(col) == 3:
            try:
                color_value = (int(col[0]), int(col[1]), int(col[2]))
            except Exception:
                color_value = None
        elif isinstance(col, str) and col.startswith("#") and len(col) == 7:
            try:
                r = int(col[1:3], 16)
                g = int(col[3:5], 16)
                b = int(col[5:7], 16)
                color_value = (r, g, b)
            except Exception:
                color_value = None

        zones_out.append(
            {
                "id": display_id,
                "points": pts_px.astype(int),
                "purpose": zone.get("purpose"),
                "capacity": zone.get("capacity"),
                "color": color_value,
            }
        )

    return zones_out
