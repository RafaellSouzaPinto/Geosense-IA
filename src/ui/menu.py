"""Módulo de menus interativos para o GeoSense"""

import os
from typing import Any, Dict, Optional, Tuple

from ..utils.io_utils import safe_read_line
from .file_selector import interactive_select_file_by_kind


def startup_menu(preselect: int = 0) -> Optional[Tuple[str, Optional[str], Optional[int]]]:
    """Exibe um menu inicial para escolher entre Vídeo, Foto (Imagem) ou Webcam.

    Retorna uma tupla (mode, path, cam_index):
      - mode: 'video' | 'image' | 'webcam'
      - path: caminho do arquivo (para video/image) ou None
      - cam_index: índice da webcam (para webcam) ou None
    """
    print("\n=== GeoSense - Menu Inicial ===", flush=True)
    print("1) Processar VÍDEO de arquivo", flush=True)
    print("2) Processar FOTO (imagem) de arquivo", flush=True)
    print("3) Usar WEBCAM", flush=True)
    print("q) Sair", flush=True)

    while True:
        try:
            opt = safe_read_line("Escolha uma opção: ").strip().lower()
        except Exception:
            opt = "1"  

        if opt in {"q", "quit", "exit"}:
            return None
        if opt == "1":
            path = interactive_select_file_by_kind(os.getcwd(), "video", preselect=preselect)
            if path is None:
                return None
            return ("video", path, None)
        if opt == "2":
            path = interactive_select_file_by_kind(os.getcwd(), "image", preselect=preselect)
            if path is None:
                return None
            return ("image", path, None)
        if opt == "3":
            cam_idx = 0
            try:
                txt = safe_read_line("Índice da webcam (padrão 0): ").strip()
                cam_idx = int(txt) if txt else 0
            except Exception:
                cam_idx = 0
            return ("webcam", None, cam_idx)
        print("Opção inválida. Tente novamente.")


def gui_startup_menu() -> Optional[Tuple[str, Optional[str], Optional[int]]]:
    """Mostra um menu simples em GUI (Tkinter) para escolher modo e arquivo.

    Retorna (mode, path, cam_index) ou None se cancelado.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog, simpledialog, messagebox

        root = tk.Tk()
        root.title("GeoSense - Menu")
        root.geometry("360x220")
        root.resizable(False, False)

        selection: Dict[str, Any] = {"result": None}

        def pick_video() -> None:
            path = filedialog.askopenfilename(
                title="Selecione o vídeo",
                filetypes=[
                    ("Vídeos", "*.mp4;*.mov;*.avi;*.mkv;*.m4v;*.wmv;*.flv"),
                    ("Todos", "*.*"),
                ],
            )
            if path:
                selection["result"] = ("video", path, None)
                root.destroy()

        def pick_image() -> None:
            path = filedialog.askopenfilename(
                title="Selecione a imagem",
                filetypes=[
                    ("Imagens", "*.jpg;*.jpeg;*.png;*.bmp;*.webp"),
                    ("Todos", "*.*"),
                ],
            )
            if path:
                selection["result"] = ("image", path, None)
                root.destroy()

        def pick_webcam() -> None:
            try:
                idx_str = simpledialog.askstring("Webcam", "Índice da webcam (0, 1, ...):", initialvalue="0")
                if idx_str is None:
                    return
                idx = int(idx_str.strip()) if idx_str.strip() else 0
            except Exception:
                messagebox.showerror("Erro", "Índice inválido.")
                return
            selection["result"] = ("webcam", None, idx)
            root.destroy()

        def cancel() -> None:
            selection["result"] = None
            root.destroy()

        lbl = tk.Label(root, text="Escolha uma opção", font=("Segoe UI", 11))
        lbl.pack(pady=12)

        btn_video = tk.Button(root, text="Vídeo de arquivo", width=24, command=pick_video)
        btn_video.pack(pady=6)

        btn_img = tk.Button(root, text="Foto (imagem) de arquivo", width=24, command=pick_image)
        btn_img.pack(pady=6)

        btn_cam = tk.Button(root, text="Usar webcam", width=24, command=pick_webcam)
        btn_cam.pack(pady=6)

        btn_cancel = tk.Button(root, text="Cancelar", width=24, command=cancel)
        btn_cancel.pack(pady=10)

        try:
            root.mainloop()
        except KeyboardInterrupt:
            try:
                root.destroy()
            except Exception:
                pass
            return None

        return selection["result"]
    except Exception:
        return None
