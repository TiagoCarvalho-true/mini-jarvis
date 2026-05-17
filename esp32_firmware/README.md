# Firmware ESP32 — J.A.R.V.I.S. Mini

Este código transforma o seu ESP32 em um nó IoT controlado pelo Jarvis.

## 🚀 Como usar

1.  Abra o arquivo `config.h` e coloque o nome e a senha do seu **Wi-Fi**.
2.  Abra o arquivo `main.ino` na **Arduino IDE**.
3.  Instale as bibliotecas necessárias na Arduino IDE:
    - **Adafruit SSD1306**
    - **Adafruit GFX Library**
4.  Abra o arquivo `main.ino` na **Arduino IDE**.
5.  Instale a placa ESP32 na Arduino IDE (Vá em *Boards Manager* e procure por `esp32` by Expressif).
6.  Conecte o seu ESP32 no PC via USB.
7.  Selecione a placa (ex: *DOIT ESP32 DEVKIT V1*) e a porta COM correta.
8.  Clique em **Upload**.

## 🔌 Pinagem (GPIO)

- **Relé**: Conecte o pino de sinal no **GPIO 12**.
- **OLED (SDA)**: Conecte no **GPIO 21**.
- **OLED (SCL)**: Conecte no **GPIO 22**.
- **LED Status**: O LED interno (geralmente azul) no **GPIO 2** piscará quando o relé for acionado.

## 🔗 Integração com o Jarvis

Após o upload, abra o Monitor Serial (115200 baud) para ver o **Endereço IP** que o ESP32 recebeu (ex: `192.168.1.105`).

Coloque esse IP no seu arquivo `.env` do Jarvis:
```env
ESP32_NODES='[{"id": "quarto", "ip": "192.168.1.105", "name": "Luz do Quarto"}]'
ESP32_MOCK=false
```
