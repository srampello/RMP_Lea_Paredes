# Labyrinth Control v1

Panel de puesta a punto para Windows y firmware de prueba para un robot con
ESP32-S3 SuperMini y DRV8833.

## Qué permite hacer

- Conectarse al robot por Wi-Fi directo.
- Regular por separado la velocidad de cada motor (0 a 255).
- Avanzar, retroceder y girar mientras se mantiene presionado el control.
- Invertir el sentido de cada motor desde la interfaz, sin cambiar cables.
- Usar las teclas `W`, `A`, `S`, `D` y `Espacio`.
- Detener automáticamente los motores si se pierde la comunicación.

## 1. Cargar el firmware en el ESP32-S3

1. Abrir `firmware/firmware_esp32_s3.ino` con Arduino IDE.
2. Seleccionar la placa ESP32-S3 correspondiente y su puerto COM.
3. Compilar y cargar.
4. Dejar inicialmente las ruedas levantadas del suelo.

Pinout utilizado:

| Función | GPIO |
|---|---:|
| Motor izquierdo IN1 | 5 |
| Motor izquierdo IN2 | 6 |
| Motor derecho IN3 | 7 |
| Motor derecho IN4 | 8 |

El pin `SLEEP` del DRV8833 debe estar conectado a `3V3`, tal como figura en el
esquema del robot.

## 2. Conectar Windows al robot

En la lista de redes Wi-Fi de Windows:

- Red: `LABERINTO-ESP32`
- Contraseña: `robot1234`

Windows puede indicar que la red no tiene Internet. Es normal: es una conexión
directa entre la notebook y el robot.

## 3. Abrir la aplicación

Con Python 3 instalado, ejecutar `iniciar.bat`. La aplicación usa únicamente
módulos incluidos con Python; no necesita instalar paquetes adicionales.

1. Mantener la IP `192.168.4.1`.
2. Pulsar **CONECTAR**.
3. Elegir velocidades bajas, por ejemplo 80–100.
4. Mantener presionado un botón de movimiento.
5. Soltarlo para detener los motores.

Si una rueda avanza al revés, activar **Invertir sentido** en ese motor.

## Seguridad

- El botón **STOP** y la barra espaciadora envían una parada inmediata.
- El firmware detiene los motores si pasan 800 ms sin recibir una orden.
- Al cerrar la ventana, la aplicación intenta detener ambos motores.
- La primera prueba debe realizarse con las ruedas en el aire.

## Crear un `.exe` opcional

Ejecutar `crear_exe.bat`. El script instala PyInstaller si hace falta y genera:

`dist/LabyrinthControl.exe`

El `.exe` puede copiarse a otra PC con Windows y no requiere Python instalado.
