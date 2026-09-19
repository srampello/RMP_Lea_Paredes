/*
 * PRUEBA 1 - MOTORES
 * ESP32-S3 SuperMini + DRV8833
 *
 * Objetivo:
 *   - Verificar cada motor por separado.
 *   - Comprobar sentido positivo y negativo.
 *   - Comprobar ambos motores juntos.
 *
 * IMPORTANTE: hacer la primera prueba con las ruedas en el aire.
 */

// Motor izquierdo: DRV8833 IN1 / IN2
constexpr uint8_t M1_IN1 = 5;
constexpr uint8_t M1_IN2 = 6;

// Motor derecho: DRV8833 IN3 / IN4
constexpr uint8_t M2_IN1 = 7;
constexpr uint8_t M2_IN2 = 8;

constexpr int PWM_PRUEBA = 80;  // Rango: 0 a 255

// Cambiar a true únicamente si un motor gira al revés.
constexpr bool INVERTIR_MOTOR_IZQ = false;
constexpr bool INVERTIR_MOTOR_DER = false;


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


void motorIzquierdo(int velocidad) {
  escribirMotor(M1_IN1, M1_IN2,
                INVERTIR_MOTOR_IZQ ? -velocidad : velocidad);
}


void motorDerecho(int velocidad) {
  escribirMotor(M2_IN1, M2_IN2,
                INVERTIR_MOTOR_DER ? -velocidad : velocidad);
}


void motores(int izquierdo, int derecho) {
  motorIzquierdo(izquierdo);
  motorDerecho(derecho);
}


void detener() {
  motores(0, 0);
}


void ejecutarPrueba(const char *nombre, int izquierdo, int derecho,
                    uint32_t duracionMs) {
  Serial.println();
  Serial.println(nombre);
  Serial.printf("Orden logica: izquierdo=%d  derecho=%d\n",
                izquierdo, derecho);

  motores(izquierdo, derecho);
  delay(duracionMs);
  detener();
  Serial.println("STOP");
  delay(1000);
}


void setup() {
  Serial.begin(115200);

  pinMode(M1_IN1, OUTPUT);
  pinMode(M1_IN2, OUTPUT);
  pinMode(M2_IN1, OUTPUT);
  pinMode(M2_IN2, OUTPUT);
  detener();

  delay(3000);
  Serial.println("========================================");
  Serial.println("PRUEBA 1: MOTORES");
  Serial.println("Las ruedas deben estar levantadas.");
  Serial.println("========================================");
}


void loop() {
  ejecutarPrueba("1/6 - Motor IZQUIERDO positivo", PWM_PRUEBA, 0, 2000);
  ejecutarPrueba("2/6 - Motor IZQUIERDO negativo", -PWM_PRUEBA, 0, 2000);
  ejecutarPrueba("3/6 - Motor DERECHO positivo", 0, PWM_PRUEBA, 2000);
  ejecutarPrueba("4/6 - Motor DERECHO negativo", 0, -PWM_PRUEBA, 2000);
  ejecutarPrueba("5/6 - Ambos en sentido ADELANTE", PWM_PRUEBA, PWM_PRUEBA, 2000);
  ejecutarPrueba("6/6 - Ambos en sentido ATRAS", -PWM_PRUEBA, -PWM_PRUEBA, 2000);

  Serial.println();
  Serial.println("Ciclo terminado. Se repite en 5 segundos.");
  detener();
  delay(5000);
}
