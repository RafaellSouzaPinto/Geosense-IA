"""Logger JSON para salvar dados de motos detectadas"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Set


class JsonLogger:
    """Logger para salvar dados de detecção em formato JSON"""
    
    def __init__(self, path: str, source_desc: Optional[str] = None, run_id: Optional[str] = None) -> None:
        self._path = path
        self._seen_keys: Set[str] = set()
        self._data: Dict[str, Any] = {}
        self._current_source: str = source_desc or ""
        self._run_id: str = run_id or ""
        try:
            os.makedirs(os.path.dirname(path) or "output/runs", exist_ok=True)
        except Exception:
            pass
        try:
            self._cleanup_temp()
        except Exception:
            pass
        self._load_or_init(source_desc)

    def _load_or_init(self, source_desc: Optional[str]) -> None:
        """Carrega dados existentes ou inicializa novo arquivo"""
        loaded: Dict[str, Any] = {}
        try:
            if os.path.isfile(self._path):
                with open(self._path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
        except Exception:
            loaded = {}

        sources: Dict[str, Any] = {}
        now_iso = datetime.now().isoformat()

        if isinstance(loaded.get("sources"), dict):
            sources = loaded["sources"]  
        else:
            if isinstance(loaded.get("motos"), list):
                old_src = str(loaded.get("source", ""))
                sources[old_src or "unknown"] = {
                    "updated_at": loaded.get("updated_at", now_iso),
                    "motos": loaded["motos"],
                }
            else:
                sources = {}

        # Normaliza nomes de webcam
        try:
            numeric_keys = [k for k in list(sources.keys()) if isinstance(k, str) and k.isdigit()]
            for k in numeric_keys:
                new_key = f"webcam_{k}"
                if new_key in sources:
                    dst = sources[new_key]
                    src_bucket = sources[k]
                    try:
                        dst.setdefault("motos", []).extend(src_bucket.get("motos", []) or [])
                    except Exception:
                        pass
                    try:
                        dst["updated_at"] = src_bucket.get("updated_at", dst.get("updated_at"))
                    except Exception:
                        pass
                    del sources[k]
                else:
                    sources[new_key] = sources.pop(k)
        except Exception:
            pass

        # Garante que cada item tem a fonte correta
        try:
            for src, bucket in list(sources.items()):
                motos_list = bucket.get("motos", []) or []
                for item in motos_list:
                    if isinstance(item, dict):
                        item.setdefault("source", src)
                bucket["motos"] = motos_list
                bucket.setdefault("updated_at", now_iso)
        except Exception:
            pass

        norm_source = (source_desc or "unknown")
        try:
            if isinstance(norm_source, str) and norm_source.isdigit():
                norm_source = f"webcam_{norm_source}"
        except Exception:
            pass
        
        self._current_source = norm_source
        self._data = {"updated_at": now_iso, "sources": sources}
        if self._run_id:
            self._data["run_id"] = self._run_id

        # Reconstrói as chaves já vistas
        self._seen_keys = set()
        try:
            for src, bucket in self._data.get("sources", {}).items():
                for item in bucket.get("motos", []) or []:
                    try:
                        tid = int(item.get("track_id"))
                        self._seen_keys.add(f"{src}|{tid}")
                    except Exception:
                        continue
        except Exception:
            self._seen_keys = set()

    def _cleanup_temp(self) -> None:
        """Remove arquivos temporários órfãos"""
        tmp_path = self._path + ".tmp"
        if os.path.isfile(tmp_path):
            try:
                if not os.path.isfile(self._path):
                    os.replace(tmp_path, self._path)
                else:
                    os.remove(tmp_path)
            except Exception:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _atomic_write_json(self) -> None:
        """Escreve o JSON de forma atômica usando arquivo temporário"""
        tmp_path = self._path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
                try:
                    f.flush()
                    os.fsync(f.fileno())
                except Exception:
                    pass
            try:
                os.replace(tmp_path, self._path)
            except Exception:
                with open(self._path, "w", encoding="utf-8") as g:
                    json.dump(self._data, g, ensure_ascii=False, indent=2)
                    try:
                        g.flush()
                        os.fsync(g.fileno())
                    except Exception:
                        pass
                try:
                    if os.path.isfile(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
        except Exception:
            try:
                if os.path.isfile(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def _ensure_source_bucket(self) -> Dict[str, Any]:
        """Garante que existe um bucket para a fonte atual"""
        now_iso = datetime.now().isoformat()
        sources = self._data.setdefault("sources", {})
        bucket = sources.get(self._current_source)
        if not isinstance(bucket, dict):
            bucket = {"updated_at": now_iso, "motos": []}
            sources[self._current_source] = bucket
        bucket.setdefault("motos", [])
        bucket["updated_at"] = now_iso
        self._data["updated_at"] = now_iso
        return bucket

    def insert_moto(self, track_id: Optional[int], x: float, y: float, detected_at: datetime, db_id: Optional[int] = None) -> None:
        """Insere uma nova moto detectada no log"""
        if track_id is None:
            return
        try:
            tid = int(track_id)
        except Exception:
            return
        
        run_key = self._run_id or ""  
        key = f"{self._current_source}|{tid}|{run_key}"
        if key in self._seen_keys:
            return
            
        bucket = self._ensure_source_bucket()
        entry = {
            "source": self._current_source,
            "track_id": tid,
            "x": float(round(x, 2)),
            "y": float(round(y, 2)),
            "detected_at": detected_at.isoformat(),
        }
        if db_id is not None:
            entry["db_id"] = int(db_id)
        if self._run_id:
            entry["run_id"] = self._run_id
        
        try:
            bucket["motos"].append(entry)
            self._atomic_write_json()
            self._seen_keys.add(key)
        except Exception:
            pass
