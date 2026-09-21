# LEA_PAREDES — Esquemático V1

Primera versión editable del circuito para KiCad. El objetivo es que sirva como
base de trabajo y que luego pueda ajustarse con mediciones reales, experiencia
de pista y los componentes físicos.

## Arquitectura eléctrica

- Batería Tattu LiHV 2S 300 mAh: `VBAT` (7,6 V nominal, 8,7 V completamente cargada).
- `VBAT` alimenta directamente `VM` del TB6612FNG y la entrada del Matek Micro BEC.
- Matek configurado a 5 V: genera `+5V_RAW` para emisores IR y turbina.
- Un SS14 separa `+5V_RAW` de `ESP_5V`, reduciendo el riesgo de realimentar el resto
  del robot al conectar USB al ESP32-C3.
- El regulador de 3,3 V del módulo ESP32 genera `+3V3` para lógica, TB6612 y receptores.
- Todas las masas están unidas en `GND`.

## Pines del ESP32-C3 Super Mini

| GPIO | Función | Observación |
|---:|---|---|
| 0 | ADC sensor frontal izquierdo | `SENS_FL` |
| 1 | ADC sensor frontal derecho | `SENS_FR` |
| 2 | PWM motor izquierdo | `PWM_A`; pin de strap, pull-up de 10 kΩ |
| 3 | ADC sensor lateral izquierdo | `SENS_L` |
| 4 | ADC sensor lateral derecho | `SENS_R` |
| 5 | Dirección A1 | `AIN1` |
| 6 | Dirección A2 | `AIN2` |
| 7 | Dirección B1 | `BIN1` |
| 8 | PWM motor derecho | `PWM_B`; pin de strap y LED integrado en muchas placas |
| 9 | Pulsador de inicio | también es `BOOT`; no mantener pulsado durante reset |
| 10 | Dirección B2 | `BIN2` |
| 20 | PWM turbina | `FAN_PWM` |
| 21 | Encendido común de emisores IR | `IR_EN` |

`PWMA` y `PWMB` no están conectados permanentemente a 3,3 V. Ambos llegan al
ESP32 para usar PWM convencional del TB6612. Los pull-up de 10 kΩ sólo fijan un
estado seguro durante el arranque y no impiden que el ESP32 genere PWM.

## Sensores infrarrojos

Hay cuatro pares: frontal izquierdo, frontal derecho, lateral izquierdo y
lateral derecho.

- Cada TSAL6100 recibe 5 V mediante dos resistencias de 150 Ω en paralelo
  (75 Ω equivalentes). Al pasar de tres a cuatro emisores hacen falta **ocho
  resistencias de 150 Ω**, no seis.
- Los cuatro cátodos se conmutan juntos mediante un AO3400A en el lado bajo.
- Cada PT334-6B tiene colector a 3,3 V, emisor al ADC y 10 kΩ del ADC a GND.
- Confirmar la identificación física de ánodo/cátodo y colector/emisor con los
  datasheets y una prueba de banco antes de fabricar la PCB.

## Turbina

- Motor coreless 8520 conectado a `+5V_TURBINE`.
- AO3400A en conmutación low-side, resistencia de gate de 100 Ω y pull-down de
  10 kΩ.
- Diodo SS34 de rueda libre, cátodo al positivo del motor.
- `SJ1` une `+5V_RAW` con `+5V_TURBINE` y queda cerrado por defecto. Si más
  adelante la turbina necesita otro regulador, se abre el puente y se inyecta
  allí la nueva alimentación.
- `C7` de 470 µF está marcado DNP/opcional; se coloca sólo si las pruebas muestran
  caídas o ruido importantes y el Matek tolera el pico de arranque.
- Empezar las pruebas con límite de PWM alrededor de 70 % y rampa de arranque.

## Advertencias para la primera PCB

1. Verificar con multímetro la polaridad real del JST-PH de la batería. En el
   esquema se define `J1.1 = BAT+` y `J1.2 = GND`.
2. Mantener abierto el puente de 9 V del Matek para obtener 5 V.
3. Los motores nominales de 6 V reciben `VBAT` a través del TB6612. Aunque se
   probaron a PWM 255, revisar corriente de bloqueo y temperatura; el firmware
   debería usar rampa y, si hace falta, limitar duty.
4. La capacidad nominal del Matek es 1,5 A continua. Medir el consumo conjunto
   de turbina, IR y lógica antes de dar por cerrada la alimentación.
5. Confirmar huellas físicas del JST-PH, capacitor electrolítico, pulsador,
   TSAL6100 y PT334-6B antes del ruteo final.

## Regeneración

El archivo `tools/generate_schematic.py` reconstruye tanto
`LEA_PAREDES.kicad_sch` como `LEA_PAREDES.kicad_sym`. Abrir el `.kicad_sch` en
KiCad y guardarlo una vez permite que KiCad lo actualice automáticamente a la
versión instalada.

La validación automática incluida comprueba balance de S-expressions y que
todos los pines de cada símbolo tengan una red asignada. Todavía es necesario
ejecutar ERC desde KiCad después de abrirlo y revisar manualmente las huellas.
