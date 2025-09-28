# GeoSense - Sistema de Detecção e Rastreamento de Motos

Sistema inteligente para detecção e rastreamento de motocicletas em tempo real usando YOLO + ByteTrack, desenvolvido para Mottu x FIAP.

## ⚡ Início Rápido

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar sistema
python geosense.py --menu
```

**Pronto!** O sistema está funcionando. Use `--menu` para interface gráfica ou veja [Exemplos de Uso](#exemplos-de-uso) para comandos específicos.

## 🏗️ Estrutura do Projeto

```
iotSprint2/
├── src/                          # Código fonte principal
│   ├── __init__.py
│   ├── main.py                   # Arquivo principal simplificado
│   ├── config/                   # Configurações e argumentos
│   │   ├── __init__.py
│   │   └── args_parser.py
│   ├── detection/                # Módulos de detecção
│   │   ├── __init__.py
│   │   ├── yolo_detector.py      # Detector YOLO especializado
│   │   └── tracker.py            # Tracker com reassociação de IDs
│   ├── processing/               # Processadores de mídia
│   │   ├── __init__.py
│   │   ├── image_processor.py    # Processamento de imagens
│   │   └── video_processor.py    # Processamento de vídeos
│   ├── logging/                  # Sistema de logging
│   │   ├── __init__.py
│   │   ├── json_logger.py        # Logger JSON
│   │   └── oracle_logger.py      # Logger Oracle DB
│   ├── ui/                       # Interface de usuário
│   │   ├── __init__.py
│   │   ├── menu.py               # Menus interativos
│   │   └── file_selector.py      # Seleção de arquivos
│   └── utils/                    # Utilitários
│       ├── __init__.py
│       ├── geometry.py           # Cálculos geométricos
│       ├── zones.py              # Configuração de zonas
│       └── io_utils.py           # Utilitários de I/O
├── data/                         # Dados e recursos
│   ├── models/                   # Modelos YOLO
│   │   └── yolov8n.pt
│   ├── media/                    # Arquivos de mídia
│   │   ├── images/
│   │   │   └── imagem.jpg
│   │   └── videos/
│   │       └── video.mp4
│   └── configs/                  # Arquivos de configuração
│       └── zones_example.json
├── output/                       # Resultados e saídas
│   └── runs/
│       └── motos.json
├── tests/                        # Testes unitários
├── docs/                         # Documentação
├── geosense.py                   # Script de entrada principal
├── requirements.txt              # Dependências
├── setup.py                     # Configuração de instalação
└── README.md                     # Este arquivo
```

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.8 ou superior
- Git (para clonar o repositório)

### Instalação Completa

#### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd iotSprint3
```

#### 2. Criar Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual (Windows)
.venv\Scripts\activate

# Ativar ambiente virtual (Linux/Mac)
source .venv/bin/activate
```

#### 3. Instalar Dependências

```bash
# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências do projeto
pip install -r requirements.txt

# Ou instalar como pacote (opcional)
pip install -e .
```

#### 4. Verificar Instalação

```bash
# Verificar se tudo foi instalado corretamente
python geosense.py --help
```

### Desativação do Ambiente Virtual

```bash
# Para desativar o ambiente virtual
deactivate
```

### Uso Básico

#### Primeira Execução (Recomendado)

```bash
# 1. Ativar ambiente virtual
.venv\Scripts\activate  # Windows
# ou
source .venv/bin/activate  # Linux/Mac

# 2. Executar com menu interativo (mais fácil para iniciantes)
python geosense.py --menu
```

#### Exemplos de Uso

```bash
# Processar vídeo específico com visualização
python geosense.py --source data/media/videos/video.mp4 --show

# Usar webcam (câmera padrão)
python geosense.py --webcam 0 --show

# Processar imagem e salvar resultado
python geosense.py --source data/media/images/imagem.jpg --show --save

# Processar vídeo sem visualização (mais rápido)
python geosense.py --source data/media/videos/video.mp4

# Usar modelo customizado
python geosense.py --source video.mp4 --model data/models/yolov8n.pt --show

# Ajustar sensibilidade de detecção
python geosense.py --source video.mp4 --conf 0.5 --show
```

#### Fluxo de Trabalho Típico

1. **Ativar ambiente virtual**: `.venv\Scripts\activate`
2. **Executar sistema**: `python geosense.py --menu`
3. **Selecionar fonte**: Escolher entre vídeo, imagem ou webcam
4. **Configurar parâmetros**: Ajustar confiança, modelo, etc.
5. **Processar**: Aguardar detecção e rastreamento
6. **Visualizar resultados**: Ver estatísticas e salvar se necessário
7. **Desativar ambiente**: `deactivate`

### Argumentos Principais

- `--menu`: Mostra menu interativo para seleção
- `--source PATH`: Caminho para arquivo de vídeo/imagem
- `--webcam N`: Usar webcam com índice N
- `--show`: Exibir janela de visualização
- `--save`: Salvar resultado anotado
- `--conf FLOAT`: Confiança mínima (padrão: 0.35)
- `--model PATH`: Caminho do modelo YOLO (padrão: data/models/yolov8n.pt)

## 🎯 Características

### Detecção Inteligente

- **YOLO Especializado**: Detector otimizado para motocicletas
- **Filtros Adaptativos**: Foca apenas em objetos relevantes
- **Múltiplas Fontes**: Suporte a vídeos, imagens e webcam

### Rastreamento Avançado

- **ByteTrack**: Rastreamento robusto com persistência de IDs
- **Reassociação Inteligente**: Recupera IDs perdidos por oclusões
- **Anti-flickering**: Confirma objetos após N frames consecutivos

### Interface Amigável

- **Menu Gráfico**: Interface Tkinter no Windows
- **Seleção Intuitiva**: Navegação simplificada de arquivos
- **Feedback Visual**: HUD com estatísticas em tempo real

### Sistema de Logging

- **JSON Estruturado**: Logs organizados por fonte
- **Integração Oracle**: Banco de dados 
- **Dados Incrementais**: Atualização contínua sem duplicatas

## 🔧 Configuração Avançada

### Banco Oracle

Configure variáveis de ambiente para integração com Oracle:

```bash
export ORACLE_USER="seu_usuario"
export ORACLE_PASSWORD="sua_senha"
export ORACLE_HOST="localhost"
export ORACLE_PORT="xxxx"
export ORACLE_SERVICE="xxxx"
```

### Parâmetros de Rastreamento

```bash
# Ajustar sensibilidade de rastreamento
python geosense.py --track-thresh 0.6 --match-thresh 0.85

# Configurar anti-flickering
python geosense.py --min-track-frames 5

# Ajustar reassociação de IDs
python geosense.py --reassoc-window 60 --reassoc-iou 0.4
```

## 📊 Saída de Dados

### Arquivo JSON

```json
{
  "updated_at": "2025-09-23T18:48:00",
  "run_id": "uuid-unique-id",
  "sources": {
    "video.mp4": {
      "updated_at": "2025-09-23T18:48:00",
      "motos": [
        {
          "source": "video.mp4",
          "track_id": 1,
          "x": 640.5,
          "y": 360.25,
          "detected_at": "2025-09-23T18:47:30",
          "run_id": "uuid-unique-id"
        }
      ]
    }
  }
}
```

## 📝 Licença

Desenvolvido para Mottu x FIAP - Sprint 2 IoT.
