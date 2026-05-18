#include <OneWire.h>
#include <DallasTemperature.h>

// =========================
// PINOS DOS SENSORES
// =========================

#define PH_PIN 34
#define TEMP_PIN 4

// =========================
// SENSOR DE TEMPERATURA
// =========================

OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);

// =========================
// CONFIGURAÇÃO DO pH
// =========================

float fatorDivisor = 2.0;

// Valor que funcionou melhor no seu teste
float tensaoReferenciaPH7 = 3.27;

// Inclinação aproximada
float inclinacao = -5.70;

void setup() {
  Serial.begin(115200);
  delay(1000);

  analogReadResolution(12);
  sensors.begin();
}

void loop() {
  // =========================
  // LEITURA DO pH
  // =========================

  int somaPH = 0;

  for (int i = 0; i < 10; i++) {
    somaPH += analogRead(PH_PIN);
    delay(30);
  }

  int leituraPH = somaPH / 10;

  float tensaoGPIO = leituraPH * (3.3 / 4095.0);
  float tensaoSensorPH = tensaoGPIO * fatorDivisor;

  float ph = 7.0 + ((tensaoSensorPH - tensaoReferenciaPH7) * inclinacao);

  // =========================
  // LEITURA DA TEMPERATURA
  // =========================

  sensors.requestTemperatures();
  float temperatura = sensors.getTempCByIndex(0);

  // =========================
  // ENVIO DOS DADOS EM JSON
  // =========================

  Serial.print("{");

  Serial.print("\"ph\":");
  Serial.print(ph, 2);
  Serial.print(",");

  Serial.print("\"temperatura\":");
  Serial.print(temperatura, 2);
  Serial.print(",");

  Serial.print("\"tensao_gpio\":");
  Serial.print(tensaoGPIO, 3);
  Serial.print(",");

  Serial.print("\"tensao_sensor\":");
  Serial.print(tensaoSensorPH, 3);

  Serial.println("}");

  delay(1000);
}