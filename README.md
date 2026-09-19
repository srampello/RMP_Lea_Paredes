# RMP LEA_PAREDES

Repositorio principal de **LEA_PAREDES**, robot micromouse de competición desarrollado por RMP Robotics.

<p align="center">
  <img src="https://rmp-robotics.santii-rampe.chatgpt.site/assets/lea-paredes-emblem.png" alt="Logo LEA_PAREDES" width="460">
</p>

<p align="center">
  <a href="https://rmp-robotics.santii-rampe.chatgpt.site/robots/lea-paredes">Ver página del robot</a>
</p>

## Objetivo

Diseñar un micromouse compacto capaz de recorrer laberintos de celdas de **18 × 18 cm**, comenzando con seguimiento de pared derecha y giros temporizados, para evolucionar posteriormente hacia navegación autónoma y resolución de laberintos.

## Configuración actual

- ESP32-C3 Super Mini
- Driver dual TB6612FNG
- 2 × motores Pololu 1000 RPM
- Ruedas de 26 mm
- 4 pares de sensores infrarrojos:
  - 2 frontales
  - 1 lateral derecho
  - 1 lateral izquierdo
- Turbina con motor coreless 8520 y fan de 30 mm
- LiPo 2S 7,4 V con conector XT30
- Matek MICRO BEC 6–30 V ajustado a 5 V
- Capacitor de 470 µF / 25 V sobre la alimentación principal
- Base impresa en 3D y PCB superior

## Arquitectura

- **VBAT / 2S:** TB6612FNG, motores de tracción y etapa de potencia de la turbina.
- **5 V:** Matek MICRO BEC → ESP32-C3 y bloques que requieran alimentación regulada.
- **3,3 V:** lógica y señales compatibles con la ESP32-C3.
- **GND:** masa común para todos los módulos.

## Navegación inicial

La primera estrategia de control sigue la regla de la pared derecha:

1. Mantener una distancia de referencia respecto de la pared derecha.
2. Corregir la trayectoria mediante control diferencial de motores.
3. Detectar paredes frontales con los sensores delanteros.
4. Ejecutar giros temporizados durante las primeras pruebas.
5. Incorporar navegación con mapa y encoders en futuras revisiones.

## Estado del proyecto

El diseño mecánico se encuentra en evolución. La primera base impresa integra motores, batería y turbina; la electrónica se monta sobre una PCB superior. Por el momento, los motores se utilizan **sin encoders**.

## Documentación

- [Arquitectura del sistema](docs/ARQUITECTURA.md)
- [Conexiones actuales](docs/CONEXIONES.md)
- [Firmware](firmware/README.md)
- [Hardware electrónico](hardware/README.md)
- [Diseño mecánico y CAD](cad/README.md)
- [Lista de materiales](bom/README.md)
- [Changelog](CHANGELOG.md)
- [Página pública de RMP Robotics](https://rmp-robotics.santii-rampe.chatgpt.site/robots/lea-paredes)

## Estructura

```text
RMP_Lea_Paredes/
├── docs/
├── firmware/
│   ├── pruebas/
│   └── lea_paredes/
├── hardware/
│   ├── esquematicos/
│   └── pcb/
├── cad/
├── bom/
└── images/
    ├── components/
    ├── logos/
    └── lea-paredes/
```

El objetivo es mantener en un único repositorio el firmware, los esquemáticos, el diseño de PCB, los modelos CAD, la lista de materiales y toda la documentación técnica de LEA_PAREDES.
