"""Seletores de arquivo interativos"""

import os
from typing import List, Optional

from ..utils.io_utils import gather_media_files, safe_read_line


def interactive_select_file_by_kind(directory: str, kind: str, preselect: int = 0) -> Optional[str]:
    """Seleciona interativamente um arquivo filtrado por tipo: 'video' ou 'image'."""
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".flv"}
    image_exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    allowed = video_exts if kind == "video" else image_exts

    files = []
    for name in os.listdir(directory):
        ext = os.path.splitext(name.lower())[1]
        if ext in allowed and os.path.isfile(os.path.join(directory, name)):
            files.append(name)
    files.sort()

    if not files:
        print("Nenhum arquivo encontrado do tipo selecionado neste diretório.")
        return None

    if isinstance(preselect, int) and preselect >= 1 and preselect <= len(files):
        return os.path.join(directory, files[preselect - 1])

    print("Selecione um arquivo:", flush=True)
    for idx, name in enumerate(files, start=1):
        print(f"  {idx}) {name}", flush=True)
    while True:
        try:
            choice = safe_read_line("Digite o número (ou 'q' para sair): ").strip().lower()
        except Exception:
            print("Entrada indisponível. Usando o primeiro arquivo da lista.")
            return os.path.join(directory, files[0])
        if choice in {"q", "quit", "exit"}:
            return None
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(files):
                return os.path.join(directory, files[num - 1])
        print("Opção inválida. Tente novamente.")


def interactive_select_file(directory: str, preselect: int = 0) -> Optional[str]:
    """Seleciona interativamente um arquivo de mídia do diretório"""
    files = gather_media_files(directory)
    if not files:
        print("Nenhum arquivo de mídia encontrado no diretório atual.")
        return None
    if isinstance(preselect, int) and preselect >= 1 and preselect <= len(files):
        return os.path.join(directory, files[preselect - 1])
    print("Selecione um arquivo para processar:", flush=True)
    for idx, name in enumerate(files, start=1):
        print(f"  {idx}) {name}", flush=True)
    while True:
        try:
            choice = safe_read_line("Digite o número (ou 'q' para sair): ").strip().lower()
        except Exception:
            print("Entrada indisponível. Usando o primeiro arquivo da lista.")
            return os.path.join(directory, files[0])
        if choice in {"q", "quit", "exit"}:
            return None
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(files):
                return os.path.join(directory, files[num - 1])
        print("Opção inválida. Tente novamente.")
