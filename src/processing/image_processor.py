"""Processador de imagens para detecção de motocicletas"""

import argparse
import cv2
import os
import uuid
from datetime import datetime
from typing import List, Optional

import supervision as sv
import numpy as np

try:
    from ..detection import YoloDetector
    from ..logging import JsonLogger, OracleLogger
    from ..utils.geometry import compute_centers
    from ..utils.io_utils import safe_read_line
except ImportError:
    # Fallback para imports absolutos
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.detection import YoloDetector
    from src.logging import JsonLogger, OracleLogger
    from src.utils.geometry import compute_centers
    from src.utils.io_utils import safe_read_line


class ImageProcessor:
    """Processador para detecção de motocicletas em imagens estáticas"""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.detector = YoloDetector(args.model, args.device)
        
        # Configurar anotadores
        self.box_annotator = sv.BoxAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
        self.label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.5)
    
    def process(self, source_path: str, db_logger: Optional[OracleLogger] = None) -> None:
        """Processa uma imagem para detecção de motocicletas"""
        # Carrega a imagem
        image = cv2.imread(source_path)
        if image is None:
            raise RuntimeError(f"Não foi possível abrir a imagem: {source_path}")
        
        frame_h, frame_w = image.shape[:2]
        
        # Executa detecção
        detections = self.detector.detect(
            image=image,
            conf=self.args.conf,
            iou=self.args.iou,
            imgsz=self.args.imgsz,
            half=self.args.half,
            augment=self.args.tta
        )
        
        # Cria labels para as detecções
        labels = self._create_labels(detections)
        
        # Anota a imagem
        annotated = self._annotate_image(image, detections, labels)
        
        # Configura logger JSON
        json_logger = self._setup_json_logger(source_path)
        
        # Registra detecções se não estiver no modo show
        if db_logger is not None and len(detections) > 0 and not self.args.show:
            self._log_detections(detections, db_logger, json_logger)
        
        # Exibe ou salva resultado
        if self.args.show:
            self._display_image(annotated, detections, db_logger, json_logger)
        
        if self.args.save:
            self._save_image(annotated, source_path)
    
    def _create_labels(self, detections: sv.Detections) -> List[str]:
        """Cria labels para as detecções"""
        labels: List[str] = []
        for i in range(len(detections)):
            cls_id = int(detections.class_id[i]) if detections.class_id is not None else -1
            conf = float(detections.confidence[i]) if detections.confidence is not None else 0.0
            name = self.detector.get_class_name(cls_id)
            labels.append(f"{name} {conf:.2f}")
        return labels
    
    def _annotate_image(self, image: np.ndarray, detections: sv.Detections, labels: List[str]) -> np.ndarray:
        """Anota a imagem com detecções e contagem"""
        annotated = image.copy()
        
        # Adiciona bounding boxes e labels
        if len(detections) > 0:
            annotated = self.box_annotator.annotate(scene=annotated, detections=detections)
            annotated = self.label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
        
        # Adiciona contador de motos
        total = len(detections)
        cv2.putText(
            annotated,
            f"Motos detectadas: {total}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        
        return annotated
    
    def _setup_json_logger(self, source_path: str) -> Optional[JsonLogger]:
        """Configura o logger JSON"""
        try:
            if self.args.json_out:
                run_id = self.args.run_id or str(uuid.uuid4())
                return JsonLogger(self.args.json_out, source_desc=os.path.basename(source_path), run_id=run_id)
        except Exception:
            return None
        return None
    
    def _log_detections(self, detections: sv.Detections, db_logger: OracleLogger, json_logger: Optional[JsonLogger]) -> None:
        """Registra detecções nos loggers"""
        try:
            centers = compute_centers(detections.xyxy)
            now = datetime.now()
            for idx, (cx, cy) in enumerate(centers, start=1):
                db_id = None
                if db_logger is not None:
                    db_id = db_logger.insert_moto(int(idx), float(cx), float(cy), now)
                if json_logger is not None:
                    json_logger.insert_moto(int(idx), float(cx), float(cy), now, db_id=db_id)
        except Exception as e:
            print(f"Aviso: falha ao registrar detecções no Oracle (imagem): {e}")
    
    def _display_image(self, annotated: np.ndarray, detections: sv.Detections, 
                      db_logger: Optional[OracleLogger], json_logger: Optional[JsonLogger]) -> None:
        """Exibe a imagem em uma janela"""
        window_name = "GeoSense - Imagem"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, annotated)
        print("Pressione 'q' na janela para sair.")
        
        while True:
            key = cv2.waitKey(30) & 0xFF
            quit_pressed = False
            
            if key == ord("q"):
                quit_pressed = True
            
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    quit_pressed = True
            except Exception:
                pass
            
            # Verifica tecla no Windows
            if not quit_pressed and os.name == "nt":
                try:
                    import msvcrt  
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch.lower() == "q":
                            quit_pressed = True
                except Exception:
                    pass
            
            if quit_pressed:
                # Salva snapshot se necessário
                if (db_logger is not None or json_logger is not None) and len(detections) > 0:
                    try:
                        centers = compute_centers(detections.xyxy)
                        now = datetime.now()
                        for idx, (cx, cy) in enumerate(centers, start=1):
                            db_id = None
                            if db_logger is not None:
                                db_id = db_logger.insert_moto(int(idx), float(cx), float(cy), now)
                            if json_logger is not None:
                                json_logger.insert_moto(int(idx), float(cx), float(cy), now, db_id=db_id)
                        print(f"Snapshot (imagem) salvo: {len(centers)} registros")
                    except Exception as e:
                        print(f"Aviso: falha ao salvar snapshot (imagem): {e}")
                break
        
        try:
            cv2.destroyWindow(window_name)
        except Exception:
            cv2.destroyAllWindows()
    
    def _save_image(self, annotated: np.ndarray, source_path: str) -> None:
        """Salva a imagem anotada"""
        os.makedirs(os.path.dirname(self.args.output) or "output/runs", exist_ok=True)
        out_path = self.args.output
        root, ext = os.path.splitext(out_path)
        
        # Se é vídeo ou não especificado, usa nome baseado na fonte
        if ext.lower() in {"", ".mp4", ".mov", ".avi"}:
            base = os.path.splitext(os.path.basename(source_path))[0]
            out_path = os.path.join("output/runs", f"{base}_annotated.jpg")
        
        cv2.imwrite(out_path, annotated)
        print(f"Imagem salva em: {out_path}")
