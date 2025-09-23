"""Detector YOLO para motocicletas"""

import numpy as np
from typing import Dict, List, Set
from ultralytics import YOLO
import supervision as sv


class YoloDetector:
    """Detector YOLO especializado para motocicletas"""
    
    def __init__(self, model_path: str, device: str = "cpu"):
        self.model = YOLO(model_path)
        self.device = device
        self.motorcycle_synonyms = {"motorcycle", "motorbike", "moto"}
        
        # Cache dos nomes das classes do modelo
        try:
            self.model_names: Dict[int, str] = (
                self.model.names if hasattr(self.model, "names") 
                else self.model.model.names  # type: ignore[attr-defined]
            )
        except Exception:
            self.model_names = {}
        
        # IDs das classes de motocicleta
        self.motorcycle_class_ids = self._resolve_motorcycle_class_ids()
    
    def _resolve_motorcycle_class_ids(self) -> List[int]:
        """Encontra os IDs das classes que representam motocicletas"""
        ids: List[int] = []
        try:
            for cid, name in self.model_names.items():
                if str(name).lower() in self.motorcycle_synonyms:
                    try:
                        ids.append(int(cid))
                    except Exception:
                        continue
        except Exception:
            return []
        return sorted(list(set(ids)))
    
    def detect(
        self, 
        image: np.ndarray,
        conf: float = 0.35,
        iou: float = 0.60,
        imgsz: int = 960,
        half: bool = False,
        augment: bool = False
    ) -> sv.Detections:
        """Detecta motocicletas na imagem"""
        results = self.model.predict(
            source=image,
            conf=conf,
            iou=iou,
            imgsz=imgsz,
            device=self.device,
            half=half,
            augment=augment,
            classes=self.motorcycle_class_ids if self.motorcycle_class_ids else None,
            verbose=False,
        )
        
        result = results[0]
        detections = sv.Detections.from_ultralytics(result)
        
        # Filtra apenas motocicletas se temos nomes de classes
        if len(detections) > 0 and self.model_names:
            class_names = np.array(
                [str(self.model_names.get(int(c), "")).lower() for c in detections.class_id],
                dtype=object,
            )
            mask_moto = np.isin(class_names, list(self.motorcycle_synonyms))
            detections = detections[mask_moto]
        
        return detections
    
    def get_class_name(self, class_id: int) -> str:
        """Retorna o nome da classe para um ID"""
        return str(self.model_names.get(class_id, "obj")) if self.model_names else "obj"
