/*
 * PRUEBA 2 - MOTORES CON ENCODERS
 * ESP32-S3 SuperMini + DRV8833 + 2 encoders de cuadratura
 *
 * Esta prueba mueve un motor por vez y muestra los pulsos cada 250 ms.
 * No calcula RPM porque primero hay que confirmar la cantidad exacta de
 * pulsos por vuelta del motorreductor instalado.
 *
 * IMPORTANTE: hacer la primera prueba con las ruedas en el aire.
 */

// DRV8833
constexpr uint8_t M1_IN1 = 5;
constexpr uint8_t M1_IN2 = 6;
constexpr uint8_t M2_IN1 = 7;
constexpr uint8_t M2_IN2 = 8;

// Encoder izquierdo
constexpr uint8_t ENC_IZQ_A = 9;   // Cable verde C1
constexpr uint8_t ENC_IZQ_B = 10;  // Cable amarillo C2

// Encoder derecho
constexpr uint8_t ENC_DER_A = 11;  // Cable verde C1
constexpr uint8_t ENC_DER_B = 12;  // Cable amarillo C2

constexpr int PWM_PRUEBA = 80;
constexpr uint32_t DURACION_PRUEBA_MS = 3000;
constexpr uint32_t PERIODO_REPORTE_MS = 250;

// Ajustar estos valores después de observar la primera prueba.
constexpr bool INVERTIR_MOTOR_IZQ = false;
constexpr bool INVERTIR_MOTOR_DER = false;
constexpr bool INVERTIR_ENCODER_IZQ = false;
constexpr bool INVERTIR_ENCODER_DER = false;

volatile int32_t pulsosIzquierdo = 0;
volatile int32_t pulsosDerecho = 0;


void IRAM_ATTR encoderIzquierdoISR() {
  int paso = digitalRead(ENC_IZQ_B) ? 1 : -1;
  pulsosIzquierdo += INVERTIR_ENCODER_IZQ ? -paso : paso;
}


void IRAM_ATTR encoderDerechoISR() {
  int paso = digitalRead(ENC_DER_B) ? 1 : -1;
  pulsosDerecho += INVERTIR_ENCODER_DER ? -paso : paso;
}


void escribirMotor(uint8_t in1, uint8_t in2, int velocidad) {
  velocidad = constrain(velocidad, -255, 255);

  if (velocidad > 0) {
    analogWrite(in1, velocidad);
    analogWrite(in2, 0);
  } else if (velocidad < 0) {
    analogWrite(in1, 0);
    analogWrite(in2, -velocidad);
  } else {
    analogWrite(in1, 0);
    analogWrite(in2, 0);
  }
}


void motores(int izquierdo, int derecho) {
  escribirMotor(M1_IN1, M1_IN2,
                INVERTIR_MOTOR_IZQ ? -izquierdo : izquierdo);
  escribirMotor(M2_IN1, M2_IN2,
                INVERTIR_MOTOR_DER ? -derecho : derecho);
}


void detener() {
  motores(0, 0);
}


void ponerContadoresEnCero() {
  noInterrupts();
  pulsosIzquierdo = 0;
  pulsosDerecho = 0;
  interrupts();
}


void leerContadores(int32_t &izquierdo, int32_t &derecho) {
  noInterrupts();
  izquierdo = pulsosIzquierdo;
  derecho = pulsosDerecho;
  interrupts();
}


void probarMovimiento(const char *nombre, int velocidadIzq, int velocidadDer) {
  ponerContadoresEnCero();

  Serial.println();
  Serial.println(nombre);
  Serial.printf("PWM logico: IZQ=%d  DER=%d\n", velocidadIzq, velocidadDer);
  Serial.println("Tiempo(ms)\tPulsos IZQ\tPulsos DER\tDelta IZQ\tDelta DER");

  int32_t anteriorIzq = 0;
  int32_t anteriorDer = 0;
  uint32_t inicio = millis();
  uint32_t proximoReporte = inicio;

  motores(velocidadIzq, velocidadDer);

  while (millis() - inicio < DURACION_PRUEBA_MS) {
    if ((int32_t)(millis() - proximoReporte) >= 0) {
      int32_t actualIzq;
      int32_t actualDer;
      leerContadores(actualIzq, actualDer);

      Serial.printf("%lu\t\t%ld\t\t%ld\t\t%ld\t\t%ld\n",
                    millis() - inicio,
                    (long)actualIzq,
                    (long)actualDer,
                    (long)(actualIzq - anteriorIzq),
                    (long)(actualDer - anteriorDer));

      anteriorIzq = actualIzq;
      anteriorDer = actualDer;
      proximoReporte += PERIODO_REPORTE_MS;
    }
    delay(1);
  }

  detener();
  int32_t totalIzq;
  int32_t totalDer;
  leerContadores(totalIzq, totalDer);
  Serial.printf("STOP - Totales: IZQ=%ld  DER=%ld\n",
                (long)totalIzq, (long)totalDer);
  delay(1500);
}


void setup() {
  Serial.begin(115200);

  pinMode(M1_IN1, OUTPUT);
  pinMode(M1_IN2, OUTPUT);
  pinMode(M2_IN1, OUTPUT);
  pinMode(M2_IN2, OUTPUT);
  detener();

  // Los encoders están alimentados a 3V3. Si el módulo ya incorpora
  // resistencias de salida, INPUT también puede utilizarse.
  pinMode(ENC_IZQ_A, INPUT_PULLUP);
  pinMode(ENC_IZQ_B, INPUT_PULLUP);
  pinMode(ENC_DER_A, INPUT_PULLUP);
  pinMode(ENC_DER_B, INPUT_PULLUP);

  // Se cuenta un pulso por cada flanco ascendente del canal A.
  attachInterrupt(digitalPinToInterrupt(ENC_IZQ_A), encoderIzquierdoISR, RISING);
  attachInterrupt(digitalPinToInterrupt(ENC_DER_A), encoderDerechoISR, RISING);

  delay(3000);
  Serial.println("========================================");
  Serial.println("PRUEBA 2: MOTORES + ENCODERS");
  Serial.println("Monitor serie: 115200 baudios");
  Serial.println("========================================");
}


void loop() {
  probarMovimiento("1/4 - Motor IZQUIERDO positivo", PWM_PRUEBA, 0);
  probarMovimiento("2/4 - Motor IZQUIERDO negativo", -PWM_PRUEBA, 0);
  probarMovimiento("3/4 - Motor DERECHO positivo", 0, PWM_PRUEBA);
  probarMovimiento("4/4 - Motor DERECHO negativo", 0, -PWM_PRUEBA);

  Serial.println();
  Serial.println("Ciclo terminado. Se repite en 5 segundos.");
  detener();
  delay(5000);
}
