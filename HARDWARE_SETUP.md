# 🔧 Guia de Montagem de Hardware (J.A.R.V.I.S. Mini)

Este documento destina-se a desenvolvedores e makers que desejam "dar um corpo" ao J.A.R.V.I.S. Mini utilizando microcontroladores e microcomputadores físicos.

A arquitetura física foi desenhada para separar o processamento pesado (Cérebro) da execução de ações elétricas (Corpo).

## 🧠 O Cérebro: Raspberry Pi 3 Model B (ou PC)

O Raspberry Pi atua como o **Servidor Central** (FastAPI) e processa todo o áudio. Devido à limitação de 1GB de RAM do RPi 3, os modelos foram escolhidos a dedo (Faster Whisper `tiny`/`base` e Piper TTS).

### Componentes Conectados ao Raspberry Pi:
1. **Microfone USB**: Recomendado usar um microfone USB externo, pois a entrada P2 do RPi não suporta microfone diretamente (apenas áudio e vídeo analógico). 
2. **Alto-falante / Caixa de Som**: Conectado via cabo P2 (jack de 3.5mm) na saída de áudio do Raspberry Pi, ou via Bluetooth.
3. **Webcam USB**: Para o módulo de visão (OpenCV).

### Dicas de Configuração (Raspberry OS):
- Instale dependências de áudio no sistema operacional: `sudo apt install libportaudio2 libasound-dev`
- Crie um arquivo *Service* do `systemd` para que o script `python -m src.main` inicie automaticamente quando o Raspberry for ligado.

---

## 🦾 O Corpo: Nós ESP32 (Automação Residencial)

O Raspberry Pi **não** deve controlar os Relés diretamente via GPIO. Em vez disso, usamos o ESP32 espalhado pela casa. O ESP32 se conecta à mesma rede Wi-Fi do Raspberry e levanta um minisservidor HTTP.

### Componentes Conectados ao ESP32:
1. **Módulo Relé (1, 2, 4 ou 8 canais)**: Para ligar/desligar lâmpadas e ventiladores. (Ligue no pino 5V e GND, com os pinos de sinal nos GPIOs digitais do ESP).
2. **LEDs RGB**: Para feedback visual (ex: azul quando o Jarvis está ouvindo, vermelho para erro).
3. **Display OLED (SSD1306) via I2C**: Pinos SDA e SCL para exibir "olhos" animados do Jarvis ou textos como "Online".

### Fluxo de Comunicação (Rede Local):
1. Você diz ao microfone do Raspberry: *"Jarvis, ligue a luz da sala"*.
2. O LLaMA 3.3 deduz que a intenção é acionar o IoT.
3. O Python (Raspberry Pi) envia um POST: `http://192.168.1.100/relay/1/on`.
4. O ESP32 recebe o POST, aciona o relé e retorna status 200.
5. O Python avisa no alto-falante: *"A luz foi ligada, senhor"*.

### Firmware do ESP32 (Resumo do que será feito):
O código (que será disponibilizado na pasta `esp32_firmware/`) utilizará a biblioteca `<WebServer.h>`.
```cpp
// Exemplo de Endpoint no ESP32
server.on("/relay/on", HTTP_POST, []() {
    digitalWrite(RELAY_PIN, HIGH); // Ativa o relé
    server.send(200, "text/plain", "Luz ligada");
});
```

---

---

## 🛠️ Tutorial de Montagem e Integração

### 1. Preparação do Raspberry Pi 3
1. Instale o Raspberry Pi OS Lite (64-bit).
2. Instale as dependências de sistema:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip portaudio19-dev libatlas-base-dev libopencv-dev
   ```
3. Clone o projeto e instale os requirements:
   ```bash
   pip install -r requirements.txt
   ```

### 2. Conexão do ESP32 (Fisico)
Para controlar uma lâmpada ou dispositivo AC:
- **GPIO 12**: Conecte ao pino de sinal (IN) do Módulo Relé.
- **GPIO 21 (SDA)**: Conecte ao pino SDA do Display OLED.
- **GPIO 22 (SCL)**: Conecte ao pino SCL do Display OLED.
- **VCC/GND**: Alimente os módulos com 5V (Relé) e 3.3V (OLED).
- **Relé (Saída)**: Interrompa o fio da fase da lâmpada nos pinos COM e NO (Normalmente Aberto).

### 3. Registro no J.A.R.V.I.S.
No arquivo `.env` do servidor principal, adicione o nó:
```env
ESP32_NODES='[{"id": "quarto", "ip": "192.168.1.105", "name": "Luz do Quarto"}]'
ESP32_MOCK=false
```

---

## 🏗️ Topologia Final

```text
[ SEU QUARTO ]
      |
      |-- (Voz) --> Microfone USB --> [ RASPBERRY PI 3 ]
      |                                      |
      |-- (Som) <-- Alto-falante  <-- [ SERVIDOR CORE  ]
      |                                      |
      |-- (Visao) <-- Webcam Notebook <------|
                                             |
                                          (Wi-Fi)
                                             |
                                             v
                           [ ROTEADOR WI-FI DA CASA ]
                                             |
                                          (Wi-Fi)
                                             |
                                             v
                                  [ ESP32 NODE (Sala) ] --> [ MÓDULO RELÉ ] --> [ LÂMPADA DA SALA ]
                                            |
                                            v
                                  [ DISPLAY OLED I2C ] (Exibindo animação)
```

---

## ❓ Solução de Problemas (Troubleshooting)

1. **"Audio device not found"**: Verifique se o microfone está conectado e rode `python -c "import sounddevice; print(sounddevice.query_devices())"` para ver o ID.
2. **Reconhecimento Facial Lento**: No Raspberry Pi, mude `VISION_MODE=on_demand` no `.env`. Isso fará ele processar a foto apenas quando você falar.
3. **ESP32 Offline**: Certifique-se de que o ESP32 e o Jarvis estão na **mesma rede Wi-Fi**. Teste o IP do ESP32 no navegador primeiro.
4. **Wake Word não detecta**: Ajuste o `silence_threshold` no `microphone_adapter.py` ou chegue mais perto do microfone.
