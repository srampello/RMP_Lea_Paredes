/*
 * PRUEBA 3 - 4 SENSORES SHARP GP2Y0E03
 * ESP32-S3 SuperMini
 *
 * Muestra la lectura ADC cruda (0 a 4095) y el voltaje aproximado.
 * Primero se verifican las lecturas crudas; la conversión a centímetros se
 * calibrará después sobre el robot real.
 *
 * Abrir el Monitor Serie a 115200 baudios.
 */

constexpr uint8_t SENSOR_FRONTAL_IZQ = 1;
constexpr uint8_t SENSOR_FRONTAL_DER = 2;
constexpr uint8_t SENSOR_LATERAL_IZQ = 3;
constexpr uint8_t SENSOR_LATERAL_DER = 4;

constexpr uint8_t CANTIDAD_MUESTRAS = 20;
constexpr uint32_t PERIODO_LECTURA_MS = 100;

// false: tabla completa para el Monitor Serie.
// true: formato corto para Herramientas > Serial Plotter.
constexpr bool MODO_GRAFICO = false;

struct LecturaSensor {
  uint16_t raw;
  uint16_t milivoltios;
};


LecturaSensor leerSensor(uint8_t pin) {
  uint32_t sumaRaw = 0;
  uint32_t sumaMv = 0;

  // Se descarta una lectura después de cambiar de canal del ADC.
  analogRead(pin);
  delayMicroseconds(50);

  for (uint8_t i = 0; i < CANTIDAD_MUESTRAS; i++) {
    sumaRaw += analogRead(pin);
    sumaMv += analogReadMilliVolts(pin);
    delayMicroseconds(100);
  }

  LecturaSensor lectura;
  lectura.raw = sumaRaw / CANTIDAD_MUESTRAS;
  lectura.milivoltios = sumaMv / CANTIDAD_MUESTRAS;
  return lectura;
}


void setup() {
  Serial.begin(115200);

  pinMode(SENSOR_FRONTAL_IZQ, INPUT);
  pinMode(SENSOR_FRONTAL_DER, INPUT);
  pinMode(SENSOR_LATERAL_IZQ, INPUT);
  pinMode(SENSOR_LATERAL_DER, INPUT);

  analogReadResolution(12);       // 0 a 4095
  analogSetAttenuation(ADC_11db); // Permite leer aproximadamente hasta 3,3 V

  delay(2000);
  Serial.println("========================================");
  Serial.println("PRUEBA 3: SENSORES SHARP GP2Y0E03");
  Serial.println("Acercar y alejar una pared de cada sensor.");
  Serial.println("========================================");

  if (!MODO_GRAFICO) {
    Serial.println("FI raw/mV\tFD raw/mV\tLI raw/mV\tLD raw/mV");
  }
}


void loop() {
  LecturaSensor fi = leerSensor(SENSOR_FRONTAL_IZQ);
  LecturaSensor fd = leerSensor(SENSOR_FRONTAL_DER);
  LecturaSensor li = leerSensor(SENSOR_LATERAL_IZQ);
  LecturaSensor ld = leerSensor(SENSOR_LATERAL_DER);

  if (MODO_GRAFICO) {
    // Arduino Serial Plotter reconoce nombre:valor separado por tabulaciones.
    Serial.printf("Frontal_I:%u\tFrontal_D:%u\tLateral_I:%u\tLateral_D:%u\n",
                  fi.raw, fd.raw, li.raw, ld.raw);
  } else {
    Serial.printf("%4u/%4umV\t%4u/%4umV\t%4u/%4umV\t%4u/%4umV\n",
                  fi.raw, fi.milivoltios,
                  fd.raw, fd.milivoltios,
                  li.raw, li.milivoltios,
                  ld.raw, ld.milivoltios);
  }

  delay(PERIODO_LECTURA_MS);
}
