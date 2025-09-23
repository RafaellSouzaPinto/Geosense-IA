"""Parser de argumentos para o GeoSense"""

import argparse
import os


def parse_args() -> argparse.Namespace:
    """Parse argumentos da linha de comando para o GeoSense"""
    parser = argparse.ArgumentParser(
        description=(
            "GeoSense - Detecção e rastreamento de motos em tempo real com YOLO + ByteTrack, "
            "com overlay e contagem por zonas."
        )
    )
    
    # Argumentos de fonte
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
    
    # Argumentos do modelo
    parser.add_argument(
        "--model",
        type=str,
        default="data/models/yolov8n.pt",
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
        "--half",
        action="store_true",
        help="Usa half-precision (se suportado) para acelerar",
    )
    
    # Argumentos de rastreamento
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
    
    # Argumentos de captura
    parser.add_argument(
        "--backend",
        type=str,
        default="auto",
        choices=["auto", "any", "dshow", "msmf"],
        help="Backend de captura para webcam no Windows (auto, any, dshow, msmf)",
    )
    
    # Argumentos de exibição e saída
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
        default=os.path.join("output", "runs", "geosense_output.mp4"),
        help="Caminho do arquivo de saída (se --save)",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Para após N frames (0 = infinito)",
    )
    
    # Argumentos de logging
    parser.add_argument(
        "--json-out",
        type=str,
        default=os.path.join("output", "runs", "motos.json"),
        help="Caminho do arquivo JSON para registrar motos únicas (atualiza incrementalmente)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default="",
        help="ID único da execução. Se vazio, é gerado automaticamente",
    )
    
    return parser.parse_args()
