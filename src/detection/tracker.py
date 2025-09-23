"""Tracker de motocicletas usando ByteTrack"""

import numpy as np
import supervision as sv
from typing import Dict, List, Optional, Set, Tuple

from ..utils.geometry import bbox_iou_xyxy, center_distance_xyxy


class MotorcycleTracker:
    """Tracker especializado para motocicletas com reassociação de IDs"""
    
    def __init__(
        self,
        track_thresh: float = 0.50,
        match_thresh: float = 0.80,
        track_buffer: int = 60,
        min_track_frames: int = 3,
        reassoc_window: int = 45,
        reassoc_iou: float = 0.30,
        reassoc_dist_frac: float = 0.03,
        frame_width: int = 1920,
        frame_height: int = 1080
    ):
        """
        Args:
            track_thresh: Confiança mínima para iniciar/continuar um track
            match_thresh: Limiar de matching entre detecções e tracks
            track_buffer: Tamanho do buffer de rastreamento
            min_track_frames: Frames consecutivos para confirmar uma moto única
            reassoc_window: Janela em frames para reassociar IDs
            reassoc_iou: IoU mínimo para reassociação
            reassoc_dist_frac: Fração da diagonal do frame para distância máxima
            frame_width: Largura do frame
            frame_height: Altura do frame
        """
        self.byte_tracker = sv.ByteTrack(
            track_thresh=track_thresh,
            match_thresh=match_thresh,
            track_buffer=track_buffer,
        )
        
        self.min_track_frames = min_track_frames
        self.reassoc_window = reassoc_window
        self.reassoc_iou = reassoc_iou
        self.reassoc_dist_frac = reassoc_dist_frac
        
        self.frame_diagonal = float(np.hypot(frame_width, frame_height))
        
        # Controle de IDs canônicos
        self.unique_canonical_ids: Set[int] = set()
        self.canonical_seen_frames: Dict[int, int] = {}
        self.track_to_canonical: Dict[int, int] = {}
        self.canonical_last_bbox: Dict[int, np.ndarray] = {}
        self.canonical_last_seen_frame: Dict[int, int] = {}
        
        self.frame_count = 0
    
    def update(self, detections: sv.Detections) -> Tuple[sv.Detections, List[Optional[int]]]:
        """
        Atualiza o tracker com novas detecções
        
        Returns:
            Tuple de (detecções com tracker_id, lista de IDs canônicos correspondentes)
        """
        # Atualiza ByteTrack
        detections = self.byte_tracker.update_with_detections(detections)
        
        # Gerencia IDs canônicos
        current_canonical_ids: Set[int] = set()
        det_canonical_ids: List[Optional[int]] = [None] * len(detections)
        
        # Primeiro passo: mapeia tracks existentes para IDs canônicos
        if len(detections) > 0 and detections.tracker_id is not None:
            for i in range(len(detections)):
                tid = detections.tracker_id[i]
                if tid is None:
                    continue
                tid_int = int(tid)
                
                if tid_int in self.track_to_canonical:
                    cid = self.track_to_canonical[tid_int]
                    det_canonical_ids[i] = cid
                    current_canonical_ids.add(cid)
                    
                    # Atualiza último bbox e frame visto
                    try:
                        self.canonical_last_bbox[cid] = detections.xyxy[i].copy()
                    except Exception:
                        self.canonical_last_bbox[cid] = np.array(detections.xyxy[i], dtype=float)
                    self.canonical_last_seen_frame[cid] = self.frame_count
        
        # Segundo passo: reassocia tracks novos ou perdidos
        if len(detections) > 0 and detections.tracker_id is not None:
            for i in range(len(detections)):
                tid = detections.tracker_id[i]
                if tid is None:
                    continue
                tid_int = int(tid)
                
                # Se já tem mapeamento, pula
                if tid_int in self.track_to_canonical:
                    continue
                
                bbox = detections.xyxy[i]
                best_cid: Optional[int] = None
                best_iou = -1.0
                best_dist = 1e12
                
                # Procura por ID canônico próximo recentemente perdido
                for cid, last_bbox in list(self.canonical_last_bbox.items()):
                    last_seen = self.canonical_last_seen_frame.get(cid, -10**9)
                    
                    # Ignora se muito antigo ou já em uso
                    if self.frame_count - last_seen > self.reassoc_window:
                        continue
                    if cid in current_canonical_ids:
                        continue
                    
                    # Calcula similaridade
                    iou = bbox_iou_xyxy(bbox, last_bbox)
                    dist = center_distance_xyxy(bbox, last_bbox)
                    
                    if iou > best_iou or (abs(iou - best_iou) < 1e-9 and dist < best_dist):
                        best_iou = iou
                        best_dist = dist
                        best_cid = cid
                
                # Decide se reassocia ou cria novo ID
                dist_thresh = self.reassoc_dist_frac * self.frame_diagonal
                if best_cid is not None and (best_iou >= self.reassoc_iou or best_dist <= dist_thresh):
                    cid = best_cid
                else:
                    cid = tid_int  # Novo ID canônico
                
                # Mapeia e atualiza
                self.track_to_canonical[tid_int] = cid
                det_canonical_ids[i] = cid
                current_canonical_ids.add(cid)
                
                try:
                    self.canonical_last_bbox[cid] = bbox.copy()
                except Exception:
                    self.canonical_last_bbox[cid] = np.array(bbox, dtype=float)
                self.canonical_last_seen_frame[cid] = self.frame_count
        
        # Atualiza contadores de frames vistos
        for cid in current_canonical_ids:
            self.canonical_seen_frames[cid] = self.canonical_seen_frames.get(cid, 0) + 1
            
            # Confirma como único se atingiu o mínimo de frames
            if cid not in self.unique_canonical_ids and self.canonical_seen_frames[cid] >= self.min_track_frames:
                self.unique_canonical_ids.add(cid)
        
        self.frame_count += 1
        
        return detections, det_canonical_ids
    
    def get_unique_count(self) -> int:
        """Retorna o número de motos únicas confirmadas"""
        return len(self.unique_canonical_ids)
    
    def get_active_count(self, det_canonical_ids: List[Optional[int]]) -> int:
        """Retorna o número de motos ativas no frame atual"""
        return len(set(cid for cid in det_canonical_ids if cid is not None))
    
    def is_newly_confirmed(self, canonical_id: int) -> bool:
        """Verifica se o ID canônico foi recém confirmado neste frame"""
        return self.canonical_seen_frames.get(canonical_id, 0) == self.min_track_frames
