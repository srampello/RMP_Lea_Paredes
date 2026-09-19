/*
 * LABYRINTH CONTROL - firmware de prueba de motores
 * ESP32-S3 SuperMini + DRV8833
 *
 * Red Wi-Fi creada por el robot:
 *   SSID: LABERINTO-ESP32
 *   Clave: robot1234
 *   IP: 192.168.4.1
 */

#include <WiFi.h>
#include <WebServer.h>

// DRV8833
constexpr uint8_t M1_IN1 = 5;
constexpr uint8_t M1_IN2 = 6;
constexpr uint8_t M2_IN1 = 7;
constexpr uint8_t M2_IN2 = 8;

constexpr char AP_SSID[] = "LABERINTO-ESP32";
constexpr char AP_PASSWORD[] = "robot1234";

// Si la app deja de enviar órdenes, se detiene automáticamente.
constexpr uint32_t COMMAND_TIMEOUT_MS = 800;

WebServer server(80);

int motorLeft = 0;
int motorRight = 0;
uint32_t lastCommandMs = 0;


void writeMotor(uint8_t in1, uint8_t in2, int speedValue) {
  speedValue = constrain(speedValue, -255, 255);

  if (speedValue > 0) {
    analogWrite(in1, speedValue);
    analogWrite(in2, 0);
  } else if (speedValue < 0) {
    analogWrite(in1, 0);
    analogWrite(in2, -speedValue);
  } else {
    // Coast: ambas entradas en LOW.
    analogWrite(in1, 0);
    analogWrite(in2, 0);
  }
}


void setMotors(int left, int right) {
  motorLeft = constrain(left, -255, 255);
  motorRight = constrain(right, -255, 255);
  writeMotor(M1_IN1, M1_IN2, motorLeft);
  writeMotor(M2_IN1, M2_IN2, motorRight);
}


String statusJson() {
  String json = "{";
  json += "\"ok\":true,";
  json += "\"left\":" + String(motorLeft) + ",";
  json += "\"right\":" + String(motorRight) + ",";
  json += "\"clients\":" + String(WiFi.softAPgetStationNum()) + ",";
  json += "\"uptime_ms\":" + String(millis());
  json += "}";
  return json;
}


void sendJson(int code, const String &json) {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(code, "application/json", json);
}


void handleStatus() {
  sendJson(200, statusJson());
}


void handleMotors() {
  if (!server.hasArg("left") || !server.hasArg("right")) {
    sendJson(400, "{\"ok\":false,\"error\":\"Faltan left y right\"}");
    return;
  }

  setMotors(server.arg("left").toInt(), server.arg("right").toInt());
  lastCommandMs = millis();
  sendJson(200, statusJson());
}


void handleStop() {
  setMotors(0, 0);
  lastCommandMs = millis();
  sendJson(200, statusJson());
}


void handleNotFound() {
  sendJson(404, "{\"ok\":false,\"error\":\"Ruta no encontrada\"}");
}


void setup() {
  pinMode(M1_IN1, OUTPUT);
  pinMode(M1_IN2, OUTPUT);
  pinMode(M2_IN1, OUTPUT);
  pinMode(M2_IN2, OUTPUT);
  setMotors(0, 0);

  Serial.begin(115200);
  delay(250);

  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  Serial.println();
  Serial.println("LABYRINTH CONTROL iniciado");
  Serial.print("Red: ");
  Serial.println(AP_SSID);
  Serial.print("IP: ");
  Serial.println(WiFi.softAPIP());

  server.on("/status", HTTP_GET, handleStatus);
  server.on("/motors", HTTP_POST, handleMotors);
  server.on("/stop", HTTP_POST, handleStop);
  server.onNotFound(handleNotFound);
  server.begin();

  lastCommandMs = millis();
}


void loop() {
  server.handleClient();

  if ((motorLeft != 0 || motorRight != 0) &&
      millis() - lastCommandMs > COMMAND_TIMEOUT_MS) {
    setMotors(0, 0);
  }

  delay(1);
}
