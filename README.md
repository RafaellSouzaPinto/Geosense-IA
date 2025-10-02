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
- **Integração Oracle**: Opção de banco de dados empresarial
- **Dados Incrementais**: Atualização contínua sem duplicatas

## 🔧 Configuração Avançada

### Banco Oracle (Opcional)

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

## 📈 Melhorias da Organização

### Benefícios da Nova Estrutura

1. **Modularidade**: Cada funcionalidade em módulo dedicado
2. **Manutenibilidade**: Código mais fácil de entender e modificar
3. **Testabilidade**: Módulos independentes facilitam testes
4. **Escalabilidade**: Estrutura preparada para crescimento
5. **Reutilização**: Componentes podem ser usados independentemente

### Separação de Responsabilidades

- **Config**: Centraliza toda configuração de argumentos
- **Detection**: Isola lógica de detecção e rastreamento
- **Processing**: Separa processamento de imagem e vídeo
- **Logging**: Abstrai sistemas de persistência
- **UI**: Concentra toda interação com usuário
- **Utils**: Agrupa utilitários reutilizáveis

## 🧪 Desenvolvimento

### Executar Testes

```bash
python -m pytest tests/
```

### Estrutura de Desenvolvimento

```bash
# Desenvolvimento local
python -m src.main --menu

# Debug mode
python -m src.main --source debug.mp4 --show --conf 0.1
```

## 🔧 Troubleshooting

### Problemas Comuns

#### Erro: "python não é reconhecido"

```bash
# Verificar se Python está instalado
python --version

# Se não estiver, instalar Python 3.8+ do site oficial
# https://www.python.org/downloads/
```

#### Erro: "módulo não encontrado"

```bash
# Verificar se o ambiente virtual está ativado
# Deve aparecer (.venv) no início do prompt

# Se não estiver ativado:
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Reinstalar dependências
pip install -r requirements.txt
```

#### Erro: "CUDA out of memory"

```bash
# Usar CPU em vez de GPU
python geosense.py --source video.mp4 --device cpu

# Ou reduzir resolução do vídeo
python geosense.py --source video.mp4 --imgsz 640
```

#### Erro: "webcam não encontrada"

```bash
# Listar dispositivos disponíveis
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# Usar índice correto
python geosense.py --webcam 1 --show  # Tenta câmera 1
```

#### Performance Lenta

```bash
# Usar modelo menor
python geosense.py --source video.mp4 --model yolov8n.pt

# Reduzir resolução
python geosense.py --source video.mp4 --imgsz 416

# Desabilitar visualização
python geosense.py --source video.mp4  # Sem --show
```

### Verificação de Saúde do Sistema

```bash
# Verificar instalação completa
python -c "import torch, ultralytics, cv2; print('✅ Todas as dependências OK')"

# Verificar GPU (se disponível)
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"

# Testar detecção básica
python geosense.py --source data/media/images/imagem.jpg --show
```

## 📊 Resultados Parciais do Sistema

### O que Esperar ao Usar o Sistema

Baseado na análise do código, aqui está o que acontece quando você executa o GeoSense com diferentes fontes:

#### 🖼️ **Processamento de Imagem** 

**O que acontece:**

1. **Carregamento**: Sistema carrega a imagem usando OpenCV
2. **Detecção**: YOLO detecta motocicletas com confiança mínima de 0.35 (35%)
3. **Anotação**: Desenha bounding boxes laranja e labels com confiança
4. **Contagem**: Mostra "Motos detectadas: X" no canto superior esquerdo
5. **Exibição**: Abre janela "GeoSense - Imagem" (pressione 'q' para sair)
6. **Logging**: Salva dados no JSON e Oracle (se configurado)

**Exemplo de saída:**

```
Motos detectadas: 6
Pressione 'q' na janela para sair.
Snapshot (imagem) salvo: 6 registros
```

#### 🎥 **Processamento de Vídeo** 

**O que acontece:**

1. **Inicialização**: Abre vídeo e configura ByteTrack para rastreamento
2. **Loop de frames**: Processa cada frame em tempo real
3. **HUD em tempo real**: Mostra estatísticas no canto superior esquerdo:
   - `Motos ativas: X | Únicas conf.: Y | FPS: Z.Z | conf>=0.35 iou=0.60`
4. **Rastreamento**: ByteTrack mantém IDs consistentes entre frames
5. **Confirmação**: Motos são confirmadas após 3 frames consecutivos (anti-flicker)
6. **Reassociação**: Sistema reassocia IDs perdidos em até 45 frames
7. **Logging**: Registra apenas motos recém-confirmadas (evita duplicatas)

**Exemplo de HUD:**

```
Motos ativas: 4 | Únicas conf.: 6 | FPS: 12.8 | conf>=0.35 iou=0.60
```

#### 📹 **Webcam** 

**O que acontece:**

1. **Detecção de câmera**: Tenta diferentes backends no Windows (DShow, MSMF)
2. **Captura contínua**: Processa frames da webcam em tempo real
3. **Mesmo HUD**: Estatísticas idênticas ao processamento de vídeo
4. **Controle**: Pressione 'q' ou feche a janela para parar
5. **Logging**: Salva dados com source "webcam_0"

### 🔧 **Configurações Padrão do Sistema**

| Parâmetro            | Valor Padrão | Função                              |
| -------------------- | ------------ | ----------------------------------- |
| `--conf`             | 0.35         | Confiança mínima para detecção      |
| `--iou`              | 0.60         | IoU para supressão de sobreposições |
| `--imgsz`            | 960          | Resolução de entrada                |
| `--min-track-frames` | 3            | Frames para confirmar moto única    |
| `--track-buffer`     | 60           | Buffer de rastreamento              |
| `--reassoc-window`   | 45           | Janela para reassociar IDs          |
| `--reassoc-iou`      | 0.30         | IoU mínimo para reassociação        |

### 📈 **Dados Gerados Automaticamente**

**Arquivo JSON** (`output/runs/motos.json`):

```json
{
  "updated_at": "2025-09-28T11:51:52.897455",
  "sources": {
    "video.mp4": {
      "updated_at": "2025-09-28T11:51:52.897455",
      "motos": [
        {
          "source": "video.mp4",
          "track_id": 1,
          "x": 542.36,
          "y": 437.72,
          "detected_at": "2025-09-28T11:51:52.690126",
          "db_id": 138,
          "run_id": "740d3ec9-892c-4864-9692-8f31e4eedf36"
        }
      ]
    }
  }
}
```

**Campos Explicados:**

- `track_id`: ID único da motocicleta (reassociado automaticamente)
- `x, y`: Coordenadas do centro da detecção
- `detected_at`: Timestamp exato da detecção
- `db_id`: ID no banco Oracle (se configurado)
- `run_id`: ID único da sessão de execução

### 🎯 **Performance Esperada**

| Fonte      | FPS Típico  | Uso de CPU | Memória |
| ---------- | ----------- | ---------- | ------- |
| **Imagem** | Instantâneo | Baixo      | ~200MB  |
| **Vídeo**  | 10-15 FPS   | Médio      | ~300MB  |
| **Webcam** | 15-25 FPS   | Médio      | ~250MB  |

### 🚨 **Comportamentos Especiais**

1. **Anti-Flicker**: Motos só são contadas após 3 frames consecutivos
2. **Reassociação**: IDs perdidos são recuperados em até 45 frames
3. **Logging Inteligente**: Evita duplicatas, só registra motos confirmadas
4. **Fallback de Câmera**: Tenta múltiplos backends no Windows
5. **Snapshots**: Salva estado final ao fechar janela


## 🤝 Contribuição

Este projeto foi reorganizado para facilitar contribuições. Cada módulo tem responsabilidade clara e pode ser desenvolvido independentemente.

## 📝 Licença

Desenvolvido para Mottu x FIAP - Sprint 2 IoT.
