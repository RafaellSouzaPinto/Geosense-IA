"""
GeoSense - Sistema Principal de Detecção e Rastreamento de Motos
Desenvolvido para Mottu x FIAP
"""

import os
import sys
from typing import Optional, Tuple

# Adiciona o diretório src ao path se necessário
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import parse_args
from src.logging import create_oracle_logger_from_env
from src.processing import ImageProcessor, VideoProcessor
from src.ui import startup_menu, gui_startup_menu, interactive_select_file
from src.utils.io_utils import is_image_file


def main() -> None:
    """Função principal do GeoSense"""
    args = parse_args()
    db_logger = create_oracle_logger_from_env()
    
    source: Optional[object] = None
    used_menu = False
    
    # Modo menu interativo
    if args.menu or (not args.source and (args.webcam is None or args.webcam < 0)):
        used_menu = True
        while True:
            picked: Optional[Tuple[str, Optional[str], Optional[int]]] = None
            
            # Tenta GUI primeiro no Windows
            if os.name == "nt":
                picked = gui_startup_menu()
            
            # Fallback para menu texto
            if picked is None:
                picked = startup_menu(preselect=args.select)
            
            if picked is None:
                return
            
            mode, path, cam_idx = picked
            
            if mode == "image" and path:
                args.source = path
                args.show = True
                processor = ImageProcessor(args)
                processor.process(path, db_logger=db_logger)
                continue
                
            if mode == "video" and path:
                args.source = path
                args.show = True
                processor = VideoProcessor(args)
                processor.process(path, db_logger=db_logger)
                continue
                
            if mode == "webcam" and cam_idx is not None:
                args.webcam = int(cam_idx)
                args.show = True
                processor = VideoProcessor(args)
                processor.process(int(cam_idx), db_logger=db_logger)
                continue
    
    # Modo direto (sem menu)
    if source is None and not used_menu:
        if args.webcam is not None and args.webcam >= 0:
            # Webcam especificada
            source = int(args.webcam)
        else:
            # Arquivo especificado ou seleção interativa
            selected: Optional[str] = None
            if args.source:
                selected = args.source
            else:
                selected = interactive_select_file(os.getcwd(), preselect=args.select)
                if selected is None:
                    return
                # Exibição automática quando selecionado interativamente
                args.show = True
            
            args.source = selected
            
            # Verifica se é imagem
            if os.path.isfile(selected) and is_image_file(selected):
                processor = ImageProcessor(args)
                processor.process(selected, db_logger=db_logger)
                return
            
            source = selected
    
    # Processa vídeo
    if source is not None:
        processor = VideoProcessor(args)
        processor.process(source, db_logger=db_logger)


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
