# Medidas y orientación de módulos

Estas huellas se prepararon a partir de las fotografías de los módulos reales y de sus dimensiones nominales.

| Módulo | Cuerpo nominal | Paso vertical | Separación entre hileras |
|---|---:|---:|---:|
| ESP32-C3 Super Mini | 18,0 × 22,5 mm | 2,54 mm | 15,24 mm |
| TB6612FNG rojo genérico | 18,0 × 20,5 mm | 2,54 mm | 15,24 mm |
| AO3400/AO3400A | SOT-23 | — | — |

## Orientación

- ESP32: vista desde arriba, componentes visibles y USB-C hacia arriba. La antena queda abajo. No colocar cobre, pistas ni vías bajo la zona marcada `ANTENNA_KEEP_OUT`.
- TB6612FNG: vista desde arriba, integrado visible, capacitor hacia arriba y el texto `TB6612FNG` legible abajo.
- Los nombres de los pads coinciden con el texto funcional del módulo para reducir errores de asignación.

## Montaje recomendado

Para el micromouse se recomienda la variante `Castellated`, soldada directamente sobre la PCB: es más baja, liviana y resistente a vibraciones. Las variantes `THT` quedan para prototipo o módulos reemplazables.

## Pendientes antes de fabricar

1. Imprimir las huellas a escala 1:1 y apoyar físicamente ambos módulos.
2. Confirmar con multímetro los tres GND del TB6612FNG y la orientación indicada.
3. Medir el Matek Micro BEC y agregar su huella. Mientras tanto debe representarse como conexión de cuatro pads: `BAT+`, `BAT-`, `5V` y `GND`.
4. El AO3400 usa el SOT-23 estándar de KiCad: `Package_TO_SOT_SMD:SOT-23`, con 1=G, 2=S y 3=D.
