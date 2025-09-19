import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, Set

project_root = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe") if os.name == "nt" else os.path.join(project_root, ".venv", "bin", "python")
if os.name == "nt" and os.path.exists(venv_python):
    try:
        if os.path.normcase(sys.executable) != os.path.normcase(venv_python):
            os.execv(venv_python, [venv_python, os.path.abspath(__file__)] + sys.argv[1:])
    except Exception:
        pass

try:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(line_buffering=True, write_through=True)
        except TypeError:
            sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

try:
    import cv2
except ModuleNotFoundError:
    if os.path.exists(venv_python) and os.path.normcase(sys.executable) != os.path.normcase(venv_python):
        os.execv(venv_python, [venv_python, os.path.abspath(__file__)] + sys.argv[1:])
    raise
import numpy as np
from ultralytics import YOLO

try:
    import supervision as sv
except Exception as exc:  
    raise RuntimeError(
        "A dependência 'supervision' é necessária. Instale com: pip install supervision"
    ) from exc

try:
    import oracledb  
except Exception:
    print("Aviso: pacote 'oracledb' não está disponível; integração Oracle desativada. Instale com: pip install oracledb")
    oracledb = None  


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "GeoSense - Detecção e rastreamento de motos em tempo real com YOLO + ByteTrack, "
            "com overlay e contagem por zonas."
        )
    )
    parser.add_argument(
        "--source",
        type=str,
        default="",
        help="Fonte de mídia: caminho de arquivo de vídeo/imagem. Vazio = escolher da pasta",
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Mostra menu para escolher imagem/vídeo do diretório atual",
    )
    parser.add_argument(
        "--webcam",
        type=int,
        default=-1,
        help="Usar webcam pelo índice (ex.: --webcam 0). Padrão: desativado",
    )
    parser.add_argument(
        "--select",
        type=int,
        default=0,
        help="Seleciona N-ésimo arquivo listado (1..N) sem digitar no menu",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help=(
            "Modelo YOLO da Ultralytics (ex.: yolov8n.pt, yolov8s.pt, caminho .pt). "
            "Modelos COCO detectam 'motorcycle'."
        ),
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Confiança mínima para detecção",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.60,
        help="IoU do NMS (maior = mais estrito para sobreposições)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Dispositivo: 'cpu' ou 'cuda' se tiver GPU NVIDIA",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=960,
        help="Tamanho da imagem de inferência (maior = mais qualidade, mais lento)",
    )
    parser.add_argument(
        "--tta",
        action="store_true",
        help="Ativa Test-Time Augmentation para maior precisão (mais lento)",
    )
    parser.add_argument(
        "--min-track-frames",
        type=int,
        default=3,
        help="Frames consecutivos para confirmar uma moto única (anti-flicker)",
    )
    parser.add_argument(
        "--track-buffer",
        type=int,
        default=60,
        help="Tamanho do buffer de rastreamento (maior = IDs mais persistentes)",
    )
    parser.add_argument(
        "--track-thresh",
        type=float,
        default=0.50,
        help="Confiança mínima para iniciar/continuar um track (ByteTrack)",
    )
    parser.add_argument(
        "--match-thresh",
        type=float,
        default=0.80,
        help="Limiar de matching entre detecções e tracks (ByteTrack)",
    )
    parser.add_argument(
        "--reassoc-window",
        type=int,
        default=45,
        help=(
            "Janela (em frames) para reassociar um novo track_id a um ID canônico "
            "recente e evitar recontagem quando o ByteTrack troca o ID"
        ),
    )
    parser.add_argument(
        "--reassoc-iou",
        type=float,
        default=0.30,
        help=(
            "IoU mínimo com o último bbox de um ID perdido para considerá-lo a mesma moto"
        ),
    )
    parser.add_argument(
        "--reassoc-dist-frac",
        type=float,
        default=0.03,
        help=(
            "Limite adicional por distância do centro, como fração da diagonal do frame, "
            "para reassociar quando o IoU for baixo (oclusões/variações)"
        ),
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="auto",
        choices=["auto", "any", "dshow", "msmf"],
        help="Backend de captura para webcam no Windows (auto, any, dshow, msmf)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Exibe janela com visualização ao vivo",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Salva o vídeo anotado em disco",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join("runs", "geosense_output.mp4"),
        help="Caminho do arquivo de saída (se --save)",
    )
    parser.add_argument(
        "--half",
        action="store_true",
        help="Usa half-precision (se suportado) para acelerar",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Para após N frames (0 = infinito)",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default=os.path.join("runs", "motos.json"),
        help="Caminho do arquivo JSON para registrar motos únicas (atualiza incrementalmente)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="",
        help="ID único da execução. Se vazio, é gerado automaticamente",
    )
    return parser.parse_args()


def is_webcam_source(source: str) -> bool:
    return source.isdigit()
def is_image_file(path: str) -> bool:
    ext = os.path.splitext(path.lower())[1]
    return ext in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def gather_media_files(directory: str) -> List[str]:
    allowed = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".flv", ".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    items = []
    for name in os.listdir(directory):
        ext = os.path.splitext(name.lower())[1]
        if ext in allowed and os.path.isfile(os.path.join(directory, name)):
            items.append(name)
    items.sort()
    return items


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


def interactive_select_file(directory: str, preselect: int = 0) -> Optional[str]:
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


def process_image(source_path: str, args: argparse.Namespace, db_logger: Optional["OracleLogger"] = None) -> None:
    model = YOLO(args.model)

    image = cv2.imread(source_path)
    if image is None:
        raise RuntimeError(f"Não foi possível abrir a imagem: {source_path}")
    frame_h, frame_w = image.shape[:2]

    try:
        model_names: Dict[int, str] = (
            model.names if hasattr(model, "names") else model.model.names  # type: ignore[attr-defined]
        )
    except Exception:
        model_names = {}
    motorcycle_synonyms = {"motorcycle", "motorbike", "moto"}

    def resolve_class_ids_for_keywords(model_names_map: Dict[int, str], keywords: Set[str]) -> List[int]:
        ids: List[int] = []
        try:
            for cid, name in model_names_map.items():
                if str(name).lower() in keywords:
                    try:
                        ids.append(int(cid))
                    except Exception:
                        continue
        except Exception:
            return []
        return sorted(list(set(ids)))

    motorcycle_class_ids = resolve_class_ids_for_keywords(model_names, motorcycle_synonyms) if model_names else []


    results = model.predict(
        source=image,
        conf=args.conf,
        iou=args.iou,
        imgsz=args.imgsz,
        device=args.device,
        half=args.half,
        augment=args.tta,
        classes=motorcycle_class_ids if motorcycle_class_ids else None,
        verbose=False,
    )
    result = results[0]
    detections = sv.Detections.from_ultralytics(result)
    if len(detections) > 0 and model_names:
        class_names = np.array(
            [str(model_names.get(int(c), "")).lower() for c in detections.class_id],
            dtype=object,
        )
        mask_moto = np.isin(class_names, list(motorcycle_synonyms))
        detections = detections[mask_moto]

    box_annotator = sv.BoxAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
    label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.5)
    labels: List[str] = []
    for i in range(len(detections)):
        cls_id = int(detections.class_id[i]) if detections.class_id is not None else -1
        conf = float(detections.confidence[i]) if detections.confidence is not None else 0.0
        name = str(model_names.get(cls_id, "obj")) if model_names else "obj"
        labels.append(f"{name} {conf:.2f}")

    annotated = image.copy()
    if len(detections) > 0:
        annotated = box_annotator.annotate(scene=annotated, detections=detections)
        annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

    json_logger: Optional[JsonLogger] = None
    try:
        if args.json_out:
            run_id = args.run_id or str(uuid.uuid4())
            json_logger = JsonLogger(args.json_out, source_desc=os.path.basename(source_path), run_id=run_id)
    except Exception:
        json_logger = None

    if db_logger is not None and len(detections) > 0 and not args.show:
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

    if args.show:
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

    if args.save:
        os.makedirs(os.path.dirname(args.output) or "runs", exist_ok=True)
        out_path = args.output
        root, ext = os.path.splitext(out_path)
        if ext.lower() in {"", ".mp4", ".mov", ".avi"}:
            base = os.path.splitext(os.path.basename(source_path))[0]
            out_path = os.path.join("runs", f"{base}_annotated.jpg")
        cv2.imwrite(out_path, annotated)
        print(f"Imagem salva em: {out_path}")


def process_video(source: object, args: argparse.Namespace, db_logger: Optional["OracleLogger"] = None) -> None:
    """Processa um fluxo de vídeo (arquivo ou webcam) com detecção e rastreamento."""
    cap = None
    backend_map = {
        "any": getattr(cv2, "CAP'_ANY", 0),
        "dshow": getattr(cv2, "CAP_DSHOW", 700),
        "msmf": getattr(cv2, "CAP_MSMF", 1400),
    }

    if isinstance(source, int):
        if args.backend != "auto":
            cap = cv2.VideoCapture(source, backend_map[args.backend])
        else:
            cap = cv2.VideoCapture(source)
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
        cap = cv2.VideoCapture(source)

    if not cap or not cap.isOpened():
        raise RuntimeError(f"Não foi possível abrir a fonte: {args.source or args.webcam}")

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Não foi possível ler o primeiro frame do vídeo.")
    frame_h, frame_w = first_frame.shape[:2]

    model = YOLO(args.model)
    try:
        model_names: Dict[int, str] = (
            model.names if hasattr(model, "names") else model.model.names  # type: ignore[attr-defined]
        )
    except Exception:
        model_names = {}

    motorcycle_synonyms = {"motorcycle", "motorbike", "moto"}

    def resolve_class_ids_for_keywords(model_names_map: Dict[int, str], keywords: Set[str]) -> List[int]:
        ids: List[int] = []
        try:
            for cid, name in model_names_map.items():
                if str(name).lower() in keywords:
                    try:
                        ids.append(int(cid))
                    except Exception:
                        continue
        except Exception:
            return []
        return sorted(list(set(ids)))

    motorcycle_class_ids = resolve_class_ids_for_keywords(model_names, motorcycle_synonyms) if model_names else []

    box_annotator = sv.BoxAnnotator(thickness=2, text_thickness=1, text_scale=0.5)
    label_annotator = sv.LabelAnnotator(text_thickness=1, text_scale=0.5)
    byte_tracker = sv.ByteTrack(
        track_thresh=float(args.track_thresh),
        match_thresh=float(args.match_thresh),
        track_buffer=int(args.track_buffer),
    )

    writer: Optional[cv2.VideoWriter] = None
    json_logger: Optional[JsonLogger] = None
    try:
        if args.json_out:
            if isinstance(source, int):
                src_desc = f"webcam_{int(source)}"
            else:
                src_desc = os.path.basename(str(source))
            run_id = args.run_id or str(uuid.uuid4())
            json_logger = JsonLogger(args.json_out, source_desc=src_desc, run_id=run_id)
    except Exception:
        json_logger = None
    if args.save:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        writer = cv2.VideoWriter(args.output, fourcc, float(fps), (frame_w, frame_h))

    window_name = "GeoSense - Mottu x FIAP"
    if args.show:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, min(1280, frame_w), min(720, frame_h))

    frame_count = 0
    frame_diagonal = float(np.hypot(frame_w, frame_h))
    unique_canonical_ids: Set[int] = set()
    canonical_seen_frames: Dict[int, int] = {}
    track_to_canonical: Dict[int, int] = {}
    canonical_last_bbox: Dict[int, np.ndarray] = {}
    canonical_last_seen_frame: Dict[int, int] = {}
    canonical_logged_db: Set[int] = set()
    try:
        frame = first_frame
        while True:
            if frame is None:
                break

            start = time.time()
            results = model.predict(
                source=frame,
                conf=args.conf,
                iou=args.iou,
                imgsz=args.imgsz,
                device=args.device,
                half=args.half,
                augment=args.tta,
                classes=motorcycle_class_ids if motorcycle_class_ids else None,
                verbose=False,
            )

            result = results[0]
            detections = sv.Detections.from_ultralytics(result)

            if len(detections) > 0 and model_names:
                class_names = np.array(
                    [str(model_names.get(int(c), "")).lower() for c in detections.class_id],
                    dtype=object,
                )
                mask_moto = np.isin(class_names, list(motorcycle_synonyms))
                detections = detections[mask_moto]

            detections = byte_tracker.update_with_detections(detections)

            current_canonical_ids: Set[int] = set()
            det_canonical_ids: List[Optional[int]] = [None] * len(detections)
            if len(detections) > 0 and detections.tracker_id is not None:
                for i in range(len(detections)):
                    tid = detections.tracker_id[i]
                    if tid is None:
                        continue
                    tid_int = int(tid)
                    if tid_int in track_to_canonical:
                        cid = track_to_canonical[tid_int]
                        det_canonical_ids[i] = cid
                        current_canonical_ids.add(cid)
                        try:
                            canonical_last_bbox[cid] = detections.xyxy[i].copy()
                        except Exception:
                            canonical_last_bbox[cid] = np.array(detections.xyxy[i], dtype=float)
                        canonical_last_seen_frame[cid] = frame_count
            if len(detections) > 0 and detections.tracker_id is not None:
                for i in range(len(detections)):
                    tid = detections.tracker_id[i]
                    if tid is None:
                        continue
                    tid_int = int(tid)
                    if tid_int in track_to_canonical:
                        continue
                    bbox = detections.xyxy[i]
                    best_cid: Optional[int] = None
                    best_iou = -1.0
                    best_dist = 1e12
                    for cid, last_bbox in list(canonical_last_bbox.items()):
                        last_seen = canonical_last_seen_frame.get(cid, -10**9)
                        if frame_count - last_seen > int(args.reassoc_window):
                            continue
                        if cid in current_canonical_ids:
                            continue
                        iou = _bbox_iou_xyxy(bbox, last_bbox)
                        dist = _center_distance_xyxy(bbox, last_bbox)
                        if iou > best_iou or (abs(iou - best_iou) < 1e-9 and dist < best_dist):
                            best_iou = iou
                            best_dist = dist
                            best_cid = cid
                    dist_thresh = float(args.reassoc_dist_frac) * frame_diagonal
                    if best_cid is not None and (best_iou >= float(args.reassoc_iou) or best_dist <= dist_thresh):
                        cid = best_cid
                    else:
                        cid = tid_int
                    track_to_canonical[tid_int] = cid
                    det_canonical_ids[i] = cid
                    current_canonical_ids.add(cid)
                    try:
                        canonical_last_bbox[cid] = bbox.copy()
                    except Exception:
                        canonical_last_bbox[cid] = np.array(bbox, dtype=float)
                    canonical_last_seen_frame[cid] = frame_count

            for cid in current_canonical_ids:
                canonical_seen_frames[cid] = canonical_seen_frames.get(cid, 0) + 1
                if cid not in unique_canonical_ids and canonical_seen_frames[cid] >= int(args.min_track_frames):
                    unique_canonical_ids.add(cid)

            if (db_logger is not None or json_logger is not None) and len(detections) > 0 and detections.tracker_id is not None:
                try:
                    centers = compute_centers(detections.xyxy)
                    now = datetime.now()
                    logged_canons: Set[int] = set()
                    for i in range(len(detections)):
                        cid = det_canonical_ids[i]
                        if cid is None:
                            continue
                        if cid in logged_canons:
                            continue
                        if canonical_seen_frames.get(cid, 0) == int(args.min_track_frames):
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

            current_ids: Set[int] = set(current_canonical_ids)

            labels: List[str] = []
            for i in range(len(detections)):
                cls_id = int(detections.class_id[i]) if detections.class_id is not None else -1
                conf = float(detections.confidence[i]) if detections.confidence is not None else 0.0
                canon_id = det_canonical_ids[i] if i < len(det_canonical_ids) else None
                name = str(model_names.get(cls_id, "obj")) if model_names else "obj"
                id_txt = f"#{int(canon_id)}" if canon_id is not None else ""
                labels.append(f"{name} {id_txt} {conf:.2f}")

            annotated = frame.copy()
            if len(detections) > 0:
                annotated = box_annotator.annotate(scene=annotated, detections=detections)
                annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)

            elapsed = time.time() - start
            fps_inst = 1.0 / max(elapsed, 1e-6)
            active_tracked = len(current_ids)
            unique_total = len(unique_canonical_ids)
            hud_text = (
                f"Motos ativas: {active_tracked} | Únicas conf.: {unique_total} | "
                f"FPS: {fps_inst:.1f} | conf>={args.conf:.2f} iou={args.iou:.2f}"
            )
            cv2.putText(
                annotated,
                hud_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

            if args.show:
                cv2.imshow(window_name, annotated)
                key = cv2.waitKey(1) & 0xFF
                quit_pressed = False
                if key == ord("q"):
                    quit_pressed = True
                try:
                    if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                        quit_pressed = True
                except Exception:
                    pass
                if not quit_pressed and os.name == "nt":
                    try:
                        import msvcrt  
                            ch = msvcrt.getwch()
                            if ch.lower() == "q":
                                quit_pressed = True
                    except Exception:
                        pass
                if quit_pressed:
                    if (db_logger is not None or json_logger is not None) and len(detections) > 0 and detections.tracker_id is not None:
                        try:
                            centers = compute_centers(detections.xyxy)
                            now = datetime.now()
                            newly_logged: Set[int] = set()
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
                    break

            if writer is not None:
                writer.write(annotated)

            frame_count += 1
            if args.max_frames and frame_count >= args.max_frames:
                break

            ret, frame = cap.read()
            if not ret:
                break
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if args.show:
            try:
                cv2.destroyWindow(window_name)
            except Exception:
                cv2.destroyAllWindows()
        try:
            final_total = len(unique_canonical_ids)
        except Exception:
            final_total = 0
        print(f"Total de motos únicas vistas no vídeo: {final_total}")
        if os.name == "nt" and args.show:
            try:
                import tkinter as _tk  
                from tkinter import messagebox as _msg  
                _root = _tk.Tk()
                _root.withdraw()
                _msg.showinfo("GeoSense", f"Motos únicas no vídeo: {final_total}")
                _root.destroy()
            except Exception:
                pass


def read_zones_config(
    zones_path: str, frame_width: int, frame_height: int
) -> List[Dict[str, Any]]:
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


def compute_centers(xyxy: np.ndarray) -> np.ndarray:
    x1 = xyxy[:, 0]
    y1 = xyxy[:, 1]
    x2 = xyxy[:, 2]
    y2 = xyxy[:, 3]
    cx = (x1 + x2) / 2.0
    cy = (y1 + y2) / 2.0
    return np.stack([cx, cy], axis=1)


 


class JsonLogger:
    def __init__(self, path: str, source_desc: Optional[str] = None, run_id: Optional[str] = None) -> None:
        self._path = path
        self._seen_keys: Set[str] = set()
        self._data: Dict[str, Any] = {}
        self._current_source: str = source_desc or ""
        self._run_id: str = run_id or ""
        try:
            os.makedirs(os.path.dirname(path) or "runs", exist_ok=True)
        except Exception:
            pass
        try:
            self._cleanup_temp()
        except Exception:
            pass
        self._load_or_init(source_desc)

    def _load_or_init(self, source_desc: Optional[str]) -> None:
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


def _bbox_iou_xyxy(a: np.ndarray, b: np.ndarray) -> float:
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


def _center_distance_xyxy(a: np.ndarray, b: np.ndarray) -> float:
    try:
        acx = (float(a[0]) + float(a[2])) / 2.0
        acy = (float(a[1]) + float(a[3])) / 2.0
        bcx = (float(b[0]) + float(b[2])) / 2.0
        bcy = (float(b[1]) + float(b[3])) / 2.0
        return float(np.hypot(acx - bcx, acy - bcy))
    except Exception:
        return 1e9


class OracleLogger:
    def __init__(
        self,
        user: str,
        password: str,
        host: str,
        port: int,
        service_name: str,
    ) -> None:
        self._conn = None
        self._enabled = False
        if oracledb is None:
            print("Aviso: pacote 'oracledb' não está disponível; integração Oracle desativada.")
            return
        try:
            dsn = oracledb.makedsn(host, int(port), service_name=service_name)  
            self._conn = oracledb.connect(user=user, password=password, dsn=dsn)  
            self._enabled = True
            self._ensure_table()
        except Exception as e:
            print(f"Aviso: falha ao conectar no Oracle: {e}. Integração desativada.")
            self._conn = None
            self._enabled = False

    def _ensure_table(self) -> None:
        if not self._enabled or self._conn is None:
            return
        try:
            with self._conn.cursor() as cur:  # type: ignore[attr-defined]
                cur.execute("SELECT 1 FROM user_tables WHERE table_name = :t", {"t": "MOTOS"})
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        (
                            "CREATE TABLE MOTOS ("
                            "ID NUMBER GENERATED BY DEFAULT AS IDENTITY,"
                            "TRACK_ID NUMBER NULL,"
                            "X NUMBER(10,2) NOT NULL,"
                            "Y NUMBER(10,2) NOT NULL,"
                            "DETECTED_AT TIMESTAMP NOT NULL)"
                        )
                    )
                    self._conn.commit()
                else:
                    try:
                        cur.execute(
                            "SELECT 1 FROM user_tab_columns WHERE table_name = :t AND column_name = :c",
                            {"t": "MOTOS", "c": "TRACK_ID"},
                        )
                        if not cur.fetchone():
                            cur.execute("ALTER TABLE MOTOS ADD (TRACK_ID NUMBER NULL)")
                            self._conn.commit()
                    except Exception:
                        pass
                    try:
                        cur.execute(
                            "SELECT 1 FROM user_tab_columns WHERE table_name = :t AND column_name = :c",
                            {"t": "MOTOS", "c": "ID"},
                        )
                        id_exists = bool(cur.fetchone())
                        if not id_exists:
                            try:
                                cur.execute("ALTER TABLE MOTOS ADD (ID NUMBER)")
                                self._conn.commit()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        cur.execute("SELECT 1 FROM user_sequences WHERE sequence_name = :s", {"s": "MOTOS_SEQ"})
                        seq_exists = bool(cur.fetchone())
                        if not seq_exists:
                            start_with = 1
                            try:
                                cur.execute("SELECT NVL(MAX(ID),0) FROM MOTOS")
                                row2 = cur.fetchone()
                                max_id = int(row2[0]) if row2 and row2[0] is not None else 0
                                start_with = max_id + 1
                            except Exception:
                                start_with = 1
                            try:
                                cur.execute(f"CREATE SEQUENCE MOTOS_SEQ START WITH {start_with} INCREMENT BY 1 NOCACHE")
                                self._conn.commit()
                            except Exception:
                                pass
                    except Exception:
                        pass
        except Exception as e:
            print(f"Aviso: não foi possível garantir a tabela MOTOS: {e}")

    def insert_moto(self, track_id: Optional[int], x: float, y: float, detected_at: datetime) -> Optional[int]:
        if not self._enabled or self._conn is None:
            return None
        try:
            with self._conn.cursor() as cur:  
                db_id: Optional[int] = None
                out_id = None
                try:
                    if hasattr(cur, "var") and hasattr(oracledb, "NUMBER"):
                        out_id = cur.var(oracledb.NUMBER)  
                        cur.execute(
                            "INSERT INTO MOTOS (ID, TRACK_ID, X, Y, DETECTED_AT) VALUES (MOTOS_SEQ.NEXTVAL, :id, :x, :y, :dt) RETURNING ID INTO :out_id",
                            {"id": track_id, "x": float(round(x, 2)), "y": float(round(y, 2)), "dt": detected_at, "out_id": out_id},
                        )
                        try:
                            val = out_id.getvalue()  
                            if isinstance(val, list):
                                val = val[0]
                            if val is not None:
                                db_id = int(val)
                        except Exception:
                            db_id = None
                    else:
                        cur.execute(
                            "INSERT INTO MOTOS (ID, TRACK_ID, X, Y, DETECTED_AT) VALUES (MOTOS_SEQ.NEXTVAL, :id, :x, :y, :dt)",
                            {"id": track_id, "x": float(round(x, 2)), "y": float(round(y, 2)), "dt": detected_at},
                        )
                except Exception:
                    try:
                        if hasattr(cur, "var") and hasattr(oracledb, "NUMBER"):
                            out_id = cur.var(oracledb.NUMBER)  
                            cur.execute(
                                "INSERT INTO MOTOS (TRACK_ID, X, Y, DETECTED_AT) VALUES (:id, :x, :y, :dt) RETURNING ID INTO :out_id",
                                {"id": track_id, "x": float(round(x, 2)), "y": float(round(y, 2)), "dt": detected_at, "out_id": out_id},
                            )
                            try:
                                val = out_id.getvalue()  
                                if isinstance(val, list):
                                    val = val[0]
                                if val is not None:
                                    db_id = int(val)
                            except Exception:
                                db_id = None
                        else:
                            cur.execute(
                                "INSERT INTO MOTOS (TRACK_ID, X, Y, DETECTED_AT) VALUES (:id, :x, :y, :dt)",
                                {"id": track_id, "x": float(round(x, 2)), "y": float(round(y, 2)), "dt": detected_at},
                            )
                    except Exception:
                        pass
            self._conn.commit()
            return db_id
        except Exception as e:
            print(f"Aviso: falha ao inserir na tabela MOTOS: {e}")
            return None

    def close(self) -> None:
        try:
            if self._conn is not None:
                self._conn.close()
        except Exception:
            pass


def create_oracle_logger_from_env() -> Optional["OracleLogger"]:
    user = os.getenv("ORACLE_USER", "xxxx")
    password = os.getenv("ORACLE_PASSWORD", "xxxx")
    host = os.getenv("ORACLE_HOST", "xxxx")
    port = int(os.getenv("ORACLE_PORT", "xxxx") or "xxxx")
    service = os.getenv("ORACLE_SERVICE", "orcl")
    try:
        return OracleLogger(user=user, password=password, host=host, port=port, service_name=service)
    except Exception:
        return None


def main() -> None:
    args = parse_args()
    db_logger = create_oracle_logger_from_env()
    source: Optional[object] = None
    used_menu = False
    if args.menu or (not args.source and (args.webcam is None or args.webcam < 0)):
        used_menu = True
        while True:
            picked: Optional[Tuple[str, Optional[str], Optional[int]]] = None
            if os.name == "nt":
                picked = gui_startup_menu()
            if picked is None:
                picked = startup_menu(preselect=args.select)
            if picked is None:
                return
            mode, path, cam_idx = picked
            if mode == "image" and path:
                args.source = path
                process_image(path, args, db_logger=db_logger)
                continue
            if mode == "video" and path:
                args.source = path
                process_video(path, args, db_logger=db_logger)
                continue
            if mode == "webcam" and cam_idx is not None:
                args.webcam = int(cam_idx)
                process_video(int(cam_idx), args, db_logger=db_logger)
                continue

    if source is None and not used_menu:
        if args.webcam is not None and args.webcam >= 0:
            source = int(args.webcam)
        else:
            selected: Optional[str] = None
            if args.source:
                selected = args.source
            else:
                selected = interactive_select_file(os.getcwd(), preselect=args.select)
                if selected is None:
                    return
            args.source = selected
            if os.path.isfile(selected) and is_image_file(selected):
                process_image(selected, args, db_logger=db_logger)
                return
            source = selected

    process_video(source, args, db_logger=db_logger)


if __name__ == "__main__":
    try:
        main()
        print("Obrigado por usar o sistema da GeoSense.")
    except KeyboardInterrupt:
        print("Obrigado por usar o sistema da GeoSense.")
        sys.exit(0)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)


