#!/usr/bin/env python3
"""
GeoSense - Sistema de Detecção e Rastreamento de Motos
Arquivo de entrada principal que executa o sistema organizado
"""

import os
import sys

# Garante que o projeto está no path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Executa o main
from src.main import main

if __name__ == "__main__":
    main()
