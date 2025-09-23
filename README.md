# GeoSense - Sistema de Detecção e Rastreamento de Motos

Sistema inteligente para detecção e rastreamento de motocicletas em tempo real usando YOLO + ByteTrack, desenvolvido para Mottu x FIAP.

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

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Ou instalar como pacote
pip install -e .
```

### Uso Básico

```bash
# Executar com menu interativo
python geosense.py --menu

# Processar vídeo específico
python geosense.py --source data/media/videos/video.mp4 --show

# Usar webcam
python geosense.py --webcam 0 --show

# Processar imagem
python geosense.py --source data/media/images/imagem.jpg --show --save
```

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

## 📋 Próximos Passos

- [ ] Implementar testes unitários
- [ ] Adicionar suporte a zonas de detecção
- [ ] Interface web para monitoramento
- [ ] API REST para integração
- [ ] Análise de padrões de movimento
- [ ] Relatórios automatizados

## 🤝 Contribuição

Este projeto foi reorganizado para facilitar contribuições. Cada módulo tem responsabilidade clara e pode ser desenvolvido independentemente.

## 📝 Licença

Desenvolvido para Mottu x FIAP - Sprint 2 IoT.
