#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

WebServer server(80);

// Desenha olhos no OLED
void drawEyes(bool closed = false) {
  display.clearDisplay();
  if (closed) {
    display.drawLine(30, 32, 50, 32, WHITE);
    display.drawLine(78, 32, 98, 32, WHITE);
  } else {
    display.fillCircle(40, 32, 10, WHITE);
    display.fillCircle(88, 32, 10, WHITE);
  }
  display.display();
}

void handleStatus() {
  String json = "{";
  json += "\"id\":\"" + String(node_id) + "\",";
  json += "\"name\":\"" + String(node_name) + "\",";
  json += "\"status\":\"online\",";
  json += "\"relay1\":" + String(digitalRead(RELAY_PIN_1) == HIGH ? "true" : "false");
  json += "}";
  server.send(200, "application/json", json);
}

void handleRelayOn() {
  digitalWrite(RELAY_PIN_1, HIGH);
  digitalWrite(LED_PIN, HIGH);
  drawEyes(true); delay(200); drawEyes(false); // Pisca os olhos
  server.send(200, "application/json", "{\"status\":\"success\",\"action\":\"on\"}");
}

void handleRelayOff() {
  digitalWrite(RELAY_PIN_1, LOW);
  digitalWrite(LED_PIN, LOW);
  drawEyes(true); delay(200); drawEyes(false); // Pisca os olhos
  server.send(200, "application/json", "{\"status\":\"success\",\"action\":\"off\"}");
}

void handleOled() {
  if (server.hasArg("text")) {
    String message = server.arg("text");
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(WHITE);
    display.setCursor(0, 10);
    display.println("JARVIS MINI:");
    display.setTextSize(2);
    display.println(message);
    display.display();
    server.send(200, "application/json", "{\"status\":\"success\"}");
  } else {
    server.send(400, "application/json", "{\"status\":\"error\",\"message\":\"Missing text arg\"}");
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(RELAY_PIN_1, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(RELAY_PIN_1, LOW);
  digitalWrite(LED_PIN, LOW);

  // Inicializa OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("Erro ao iniciar OLED SSD1306");
  } else {
    drawEyes();
  }

  // Conectar ao Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWi-Fi Conectado!");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());

  // Definir Rotas
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/relay/1/on", HTTP_POST, handleRelayOn);
  server.on("/relay/1/off", HTTP_POST, handleRelayOff);
  server.on("/oled", HTTP_POST, handleOled);

  server.begin();
  Serial.println("Servidor HTTP iniciado");
}

void loop() {
  server.handleClient();
  delay(10);
}
