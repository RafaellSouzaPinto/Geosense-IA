"""Utilitários de entrada e saída para arquivos e webcam"""

import os
from typing import List, Optional


def is_webcam_source(source: str) -> bool:
    """Verifica se a fonte é uma webcam (número)"""
    return source.isdigit()


def is_image_file(path: str) -> bool:
    """Verifica se o arquivo é uma imagem suportada"""
    ext = os.path.splitext(path.lower())[1]
    return ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def gather_media_files(directory: str) -> List[str]:
    """Coleta arquivos de mídia (vídeos e imagens) de um diretório"""
    allowed = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".flv", ".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    items = []
    for name in os.listdir(directory):
        ext = os.path.splitext(name.lower())[1]
        if ext in allowed and os.path.isfile(os.path.join(directory, name)):
            items.append(name)
    items.sort()
    return items


def safe_read_line(prompt: str = "") -> str:
    """Lê uma linha do console de forma robusta no Windows e outros SOs.

    No Windows, usa msvcrt.getwch para evitar problemas de buffer no PowerShell.
    Em outros sistemas, usa input().
    """
    try:
        print(prompt, end="", flush=True)
        if os.name == "nt":
            try:
                import msvcrt  
            except Exception:
                return input()
            buffer_chars: List[str] = []
            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    print("", flush=True)
                    return "".join(buffer_chars)
                if ch == "\x03":
                    raise KeyboardInterrupt
                if ch in ("\x08", "\x7f"):
                    if buffer_chars:
                        buffer_chars.pop()
                        print("\b \b", end="", flush=True)
                    continue
                buffer_chars.append(ch)
                print(ch, end="", flush=True)
        else:
            return input()
    except EOFError:
        return ""
