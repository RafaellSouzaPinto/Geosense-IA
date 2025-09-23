"""Processador de vídeo para detecção e rastreamento de motocicletas"""

import argparse
import cv2
import os
import time
import uuid
from datetime import datetime
from typing import List, Optional, Union

import supervision as sv
import numpy as np

try:
    from ..detection import YoloDetector, MotorcycleTracker
    from ..logging import JsonLogger, OracleLogger
    from ..utils.geometry import compute_centers
    from ..utils.io_utils import safe_read_line
except ImportError:
    # Fallback para imports absolutos
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.detection import YoloDetector, MotorcycleTracker
    from src.logging import JsonLogger, OracleLogger
    from src.utils.geometry import compute_centers
    from src.utils.io_utils import safe_read_line


class VideoProcessor:
    """Processador para detecção e rastreamento de motocicletas em vídeo"""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.detector = YoloDetector(args.model, args.device)
        
        # Configurar anotadores
        self.box_annotator = sv.BoxAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
        self.label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.5)
        
        # Tracker será inicializado quando soubermos o tamanho do frame
        self.tracker: Optional[MotorcycleTracker] = None
        
    def process(self, source: Union[str, int], db_logger: Optional[OracleLogger] = None) -> None:
        """Processa um fluxo de vídeo (arquivo ou webcam) com detecção e rastreamento"""
        # Abre a fonte de vídeo
        cap = self._open_video_capture(source)
        
        # Lê primeiro frame para obter dimensões
        ret, first_frame = cap.read()
        if not ret:
            raise RuntimeError("Não foi possível ler o primeiro frame do vídeo.")
        
        frame_h, frame_w = first_frame.shape[:2]
        
        # Inicializa tracker com dimensões do frame
        self.tracker = MotorcycleTracker(
            track_thresh=self.args.track_thresh,
            match_thresh=self.args.match_thresh,
            track_buffer=self.args.track_buffer,
            min_track_frames=self.args.min_track_frames,
            reassoc_window=self.args.reassoc_window,
            reassoc_iou=self.args.reassoc_iou,
            reassoc_dist_frac=self.args.reassoc_dist_frac,
            frame_width=frame_w,
            frame_height=frame_h
        )
        
        # Configura writer e logger
        writer = self._setup_video_writer(cap, frame_w, frame_h)
        json_logger = self._setup_json_logger(source)
        
        # Configura janela se necessário
        window_name = "GeoSense - Mottu x FIAP"
        if self.args.show:
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(window_name, min(1280, frame_w), min(720, frame_h))
        
        # Controle de IDs já logados no banco
        canonical_logged_db = set()
        
        try:
            frame = first_frame
            while True:
                if frame is None:
                    break
                
                start = time.time()
                
                # Detecta motocicletas
                detections = self.detector.detect(
                    image=frame,
                    conf=self.args.conf,
                    iou=self.args.iou,
                    imgsz=self.args.imgsz,
                    half=self.args.half,
                    augment=self.args.tta
                )
                
                # Atualiza tracker
                detections, det_canonical_ids = self.tracker.update(detections)
                
                # Registra motos recém-confirmadas
                if (db_logger is not None or json_logger is not None) and len(detections) > 0:
                    self._log_newly_confirmed_motorcycles(
                        detections, det_canonical_ids, db_logger, json_logger, canonical_logged_db
                    )
                
                # Cria labels e anota frame
                labels = self._create_labels(detections, det_canonical_ids)
                annotated = self._annotate_frame(frame, detections, labels)
                
                # Adiciona HUD
                elapsed = time.time() - start
                annotated = self._add_hud(annotated, det_canonical_ids, elapsed)
                
                # Exibe frame
                if self.args.show:
                    cv2.imshow(window_name, annotated)
                    if self._check_quit_key():
                        # Salva snapshot final
                        self._save_final_snapshot(
                            detections, det_canonical_ids, db_logger, json_logger, canonical_logged_db
                        )
                        break
                
                # Salva frame
                if writer is not None:
                    writer.write(annotated)
                
                # Verifica limite de frames
                if self.args.max_frames and self.tracker.frame_count >= self.args.max_frames:
                    break
                
                # Lê próximo frame
                ret, frame = cap.read()
                if not ret:
                    break
                    
        finally:
            self._cleanup_resources(cap, writer, window_name)
            
        # Mostra estatísticas finais
        final_total = self.tracker.get_unique_count() if self.tracker else 0
        print(f"Total de motos únicas vistas no vídeo: {final_total}")
        
        # Mostra popup no Windows
        if os.name == "nt" and self.args.show:
            self._show_final_popup(final_total)
    
    def _open_video_capture(self, source: Union[str, int]) -> cv2.VideoCapture:
        """Abre a captura de vídeo com fallbacks para webcam"""
        backend_map = {
            "any": getattr(cv2, "CAP_ANY", 0),
            "dshow": getattr(cv2, "CAP_DSHOW", 700),
            "msmf": getattr(cv2, "CAP_MSMF", 1400),
        }
        
        if isinstance(source, int):
            # Webcam
            if self.args.backend != "auto":
                cap = cv2.VideoCapture(source, backend_map[self.args.backend])
            else:
                cap = cv2.VideoCapture(source)
                
            # Fallback para outros backends no Windows
            if not cap.isOpened() and os.name == "nt":
                for flag in [backend_map["dshow"], backend_map["msmf"], backend_map["any"]]:
                    try:
                        cap.release()
                    except Exception:
                        pass
                    cap = cv2.VideoCapture(source, flag)
                    if cap.isOpened():
                        break
        else:
            # Arquivo
            cap = cv2.VideoCapture(source)
        
        if not cap or not cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a fonte: {source}")
        
        return cap
    
    def _setup_video_writer(self, cap: cv2.VideoCapture, frame_w: int, frame_h: int) -> Optional[cv2.VideoWriter]:
        """Configura o writer de vídeo se necessário"""
        if not self.args.save:
            return None
            
        os.makedirs(os.path.dirname(self.args.output), exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        return cv2.VideoWriter(self.args.output, fourcc, float(fps), (frame_w, frame_h))
    
    def _setup_json_logger(self, source: Union[str, int]) -> Optional[JsonLogger]:
        """Configura o logger JSON"""
        try:
            if self.args.json_out:
                if isinstance(source, int):
                    src_desc = f"webcam_{int(source)}"
                else:
                    src_desc = os.path.basename(str(source))
                run_id = self.args.run_id or str(uuid.uuid4())
                return JsonLogger(self.args.json_out, source_desc=src_desc, run_id=run_id)
        except Exception:
            return None
        return None
    
    def _create_labels(self, detections: sv.Detections, det_canonical_ids: List[Optional[int]]) -> List[str]:
        """Cria labels para as detecções com IDs canônicos"""
        labels: List[str] = []
        for i in range(len(detections)):
            cls_id = int(detections.class_id[i]) if detections.class_id is not None else -1
            conf = float(detections.confidence[i]) if detections.confidence is not None else 0.0
            canon_id = det_canonical_ids[i] if i < len(det_canonical_ids) else None
            name = self.detector.get_class_name(cls_id)
            id_txt = f"#{int(canon_id)}" if canon_id is not None else ""
            labels.append(f"{name} {id_txt} {conf:.2f}")
        return labels
    
    def _annotate_frame(self, frame: np.ndarray, detections: sv.Detections, labels: List[str]) -> np.ndarray:
        """Anota o frame com detecções"""
        annotated = frame.copy()
        if len(detections) > 0:
            annotated = self.box_annotator.annotate(scene=annotated, detections=detections)
            annotated = self.label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
        return annotated
    
    def _add_hud(self, frame: np.ndarray, det_canonical_ids: List[Optional[int]], elapsed: float) -> np.ndarray:
        """Adiciona HUD com estatísticas"""
        fps_inst = 1.0 / max(elapsed, 1e-6)
        active_tracked = self.tracker.get_active_count(det_canonical_ids) if self.tracker else 0
        unique_total = self.tracker.get_unique_count() if self.tracker else 0
        
        hud_text = (
            f"Motos ativas: {active_tracked} | Únicas conf.: {unique_total} | "
            f"FPS: {fps_inst:.1f} | conf>={self.args.conf:.2f} iou={self.args.iou:.2f}"
        )
        
        cv2.putText(
            frame,
            hud_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        return frame
    
    def _log_newly_confirmed_motorcycles(
        self,
        detections: sv.Detections,
        det_canonical_ids: List[Optional[int]],
        db_logger: Optional[OracleLogger],
        json_logger: Optional[JsonLogger],
        canonical_logged_db: set
    ) -> None:
        """Registra motocicletas recém-confirmadas"""
        if not (len(detections) > 0 and detections.tracker_id is not None):
            return
            
        try:
            centers = compute_centers(detections.xyxy)
            now = datetime.now()
            logged_canons = set()
            
            for i in range(len(detections)):
                cid = det_canonical_ids[i]
                if cid is None or cid in logged_canons:
                    continue
                
                # Só loga quando é recém-confirmado
                if self.tracker and self.tracker.is_newly_confirmed(cid):
                    cx, cy = centers[i]
                    db_id = None
                    if db_logger is not None:
                        db_id = db_logger.insert_moto(int(cid), float(cx), float(cy), now)
                    if json_logger is not None:
                        json_logger.insert_moto(int(cid), float(cx), float(cy), now, db_id=db_id)
                    print(f"TRACK #{int(cid)}: x={cx:.2f}, y={cy:.2f}, time={now}")
                    logged_canons.add(int(cid))
                    canonical_logged_db.add(int(cid))
                    
        except Exception as e:
            print(f"Aviso: falha ao registrar detecções no Oracle (vídeo): {e}")
    
    def _check_quit_key(self) -> bool:
        """Verifica se foi pressionada tecla de saída"""
        key = cv2.waitKey(1) & 0xFF
        quit_pressed = False
        
        if key == ord("q"):
            quit_pressed = True
            
        # Verifica se janela foi fechada
        try:
            if cv2.getWindowProperty("GeoSense - Mottu x FIAP", cv2.WND_PROP_VISIBLE) < 1:
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
                
        return quit_pressed
    
    def _save_final_snapshot(
        self,
        detections: sv.Detections,
        det_canonical_ids: List[Optional[int]],
        db_logger: Optional[OracleLogger],
        json_logger: Optional[JsonLogger],
        canonical_logged_db: set
    ) -> None:
        """Salva snapshot final das detecções"""
        if not ((db_logger is not None or json_logger is not None) and 
                len(detections) > 0 and detections.tracker_id is not None):
            return
            
        try:
            centers = compute_centers(detections.xyxy)
            now = datetime.now()
            newly_logged = set()
            
            for i in range(len(detections)):
                cid = det_canonical_ids[i] if i < len(det_canonical_ids) else None
                if cid is None:
                    continue
                if int(cid) in canonical_logged_db or int(cid) in newly_logged:
                    continue
                    
                cx, cy = centers[i]
                db_id = None
                if db_logger is not None:
                    db_id = db_logger.insert_moto(int(cid), float(cx), float(cy), now)
                if json_logger is not None:
                    json_logger.insert_moto(int(cid), float(cx), float(cy), now, db_id=db_id)
                newly_logged.add(int(cid))
                canonical_logged_db.add(int(cid))
                
            print(f"Snapshot (vídeo) salvo no banco: {len(newly_logged)} registros")
        except Exception as e:
            print(f"Aviso: falha ao salvar snapshot (vídeo) no Oracle: {e}")
    
    def _cleanup_resources(
        self, 
        cap: cv2.VideoCapture, 
        writer: Optional[cv2.VideoWriter], 
        window_name: str
    ) -> None:
        """Limpa recursos utilizados"""
        cap.release()
        if writer is not None:
            writer.release()
        if self.args.show:
            try:
                cv2.destroyWindow(window_name)
            except Exception:
                cv2.destroyAllWindows()
    
    def _show_final_popup(self, final_total: int) -> None:
        """Mostra popup final no Windows"""
        try:
            import tkinter as _tk  
            from tkinter import messagebox as _msg  
            _root = _tk.Tk()
            _root.withdraw()
            _msg.showinfo("GeoSense", f"Motas únicas no vídeo: {final_total}")
            _root.destroy()
        except Exception:
            pass
