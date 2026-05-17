# Usar uma imagem Python slim
FROM python:3.11-slim

# Evitar que o Python gere arquivos .pyc e permitir logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias de sistema para Audio, OpenCV e Faster Whisper
RUN apt-get update && apt-get install -y \
    build-essential \
    libasound2-dev \
    portaudio19-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Definir diretorio de trabalho
WORKDIR /app

# Copiar requirements primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do codigo
COPY . .

# Criar pasta para o banco de dados e logs
RUN mkdir -p data known_faces

# Comando padrao (sera sobrescrito pelo compose)
CMD ["python", "src/main_voice.py"]
