#!/usr/bin/env python3
"""Generate the editable KiCad schematic for LEA_PAREDES v1.

The file is intentionally self-contained: every symbol used by the schematic is
embedded in the .kicad_sch.  A matching project-local symbol library is emitted
as well, so the custom module symbols remain reusable when the design evolves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5


SCRIPT_DIR = Path(__file__).resolve().parent
# The repository keeps this script in tools/.  Keeping this fallback makes it
# convenient to run while developing the generator next to the output files.
OUT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "tools" else SCRIPT_DIR
PROJECT = "LEA_PAREDES"


def uid(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"https://lea-paredes.local/kicad/{key}"))


def fnum(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def indent(text: str, spaces: int = 2) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


def effects(size: float = 1.27, hide: bool = False, justify: str | None = None) -> str:
    extra = ""
    if justify:
        extra += f"\n      (justify {justify})"
    if hide:
        extra += "\n      (hide yes)"
    return f"(effects\n  (font (size {fnum(size)} {fnum(size)})){extra}\n)"


@dataclass(frozen=True)
class Pin:
    number: str
    name: str
    side: str
    electrical: str = "passive"


@dataclass
class SymbolType:
    name: str
    reference: str
    width: float
    pins: list[Pin]
    description: str
    pin_positions: dict[str, tuple[float, float, int]] = field(default_factory=dict)

    @property
    def height(self) -> float:
        left = sum(p.side == "left" for p in self.pins)
        right = sum(p.side == "right" for p in self.pins)
        return max(7.62, (max(left, right) + 1) * 2.54)

    def calculate_positions(self) -> None:
        for side in ("left", "right"):
            pins = [p for p in self.pins if p.side == side]
            start = (len(pins) - 1) * 1.27
            for index, pin in enumerate(pins):
                y = start - index * 2.54
                if side == "left":
                    self.pin_positions[pin.number] = (-self.width / 2 - 2.54, y, 0)
                else:
                    self.pin_positions[pin.number] = (self.width / 2 + 2.54, y, 180)


@dataclass(frozen=True)
class Part:
    ref: str
    value: str
    symbol: str
    x: float
    y: float
    footprint: str = ""
    datasheet: str = "~"
    dnp: bool = False


TYPES: dict[str, SymbolType] = {}
PARTS: list[Part] = []
NETS: dict[tuple[str, str], str] = {}


def add_type(name: str, reference: str, width: float, pins: list[Pin], description: str) -> None:
    symbol = SymbolType(name, reference, width, pins, description)
    symbol.calculate_positions()
    TYPES[name] = symbol


def add_part(ref: str, value: str, symbol: str, x: float, y: float,
             footprint: str = "", datasheet: str = "~", dnp: bool = False,
             nets: dict[str, str] | None = None) -> None:
    if symbol not in TYPES:
        raise KeyError(symbol)
    PARTS.append(Part(ref, value, symbol, x, y, footprint, datasheet, dnp))
    assigned = nets or {}
    expected = {p.number for p in TYPES[symbol].pins}
    if set(assigned) != expected:
        raise ValueError(f"{ref}: pins {sorted(expected)} require nets; got {sorted(assigned)}")
    for number, net in assigned.items():
        NETS[(ref, number)] = net


def symbol_definition(symbol: SymbolType, embedded: bool) -> str:
    lib_name = f"LEA_PAREDES:{symbol.name}" if embedded else symbol.name
    body = symbol.name.replace(":", "_")
    half_w = symbol.width / 2
    half_h = symbol.height / 2
    pin_defs = []
    for pin in symbol.pins:
        x, y, angle = symbol.pin_positions[pin.number]
        pin_defs.append(
            f'''(pin {pin.electrical} line
  (at {fnum(x)} {fnum(y)} {angle})
  (length 2.54)
  (name "{pin.name}" {indent(effects(0.8), 4)})
  (number "{pin.number}" {indent(effects(0.8), 4)})
)'''
        )
    return f'''(symbol "{lib_name}"
  (pin_names (offset 0.8))
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (property "Reference" "{symbol.reference}"
    (at 0 {fnum(half_h + 2.54)} 0)
    {indent(effects(), 4)}
  )
  (property "Value" "{symbol.name}"
    (at 0 {fnum(-half_h - 2.54)} 0)
    {indent(effects(), 4)}
  )
  (property "Footprint" ""
    (at 0 0 0)
    {indent(effects(hide=True), 4)}
  )
  (property "Datasheet" "~"
    (at 0 0 0)
    {indent(effects(hide=True), 4)}
  )
  (property "Description" "{symbol.description}"
    (at 0 0 0)
    {indent(effects(hide=True), 4)}
  )
  (symbol "{body}_0_1"
    (rectangle
      (start {fnum(-half_w)} {fnum(half_h)})
      (end {fnum(half_w)} {fnum(-half_h)})
      (stroke (width 0.254) (type default))
      (fill (type background))
    )
  )
  (symbol "{body}_1_1"
{indent(chr(10).join(pin_defs), 4)}
  )
)'''


def property_block(name: str, value: str, x: float, y: float, hide: bool = False) -> str:
    return f'''(property "{name}" "{value}"
  (at {fnum(x)} {fnum(y)} 0)
  {indent(effects(1.27, hide=hide), 2)}
)'''


def part_instance(part: Part) -> str:
    st = TYPES[part.symbol]
    half_h = st.height / 2
    pins = []
    for pin in st.pins:
        pins.append(f'(pin "{pin.number}" (uuid "{uid(f"part/{part.ref}/pin/{pin.number}")}"))')
    return f'''(symbol
  (lib_id "LEA_PAREDES:{part.symbol}")
  (at {fnum(part.x)} {fnum(part.y)} 0)
  (unit 1)
  (exclude_from_sim no)
  (in_bom yes)
  (on_board yes)
  (dnp {'yes' if part.dnp else 'no'})
  (uuid "{uid(f'part/{part.ref}')}")
  {indent(property_block('Reference', part.ref, part.x, part.y - half_h - 2.54), 2)}
  {indent(property_block('Value', part.value, part.x, part.y + half_h + 2.54), 2)}
  {indent(property_block('Footprint', part.footprint, part.x, part.y, hide=True), 2)}
  {indent(property_block('Datasheet', part.datasheet, part.x, part.y, hide=True), 2)}
  {indent(chr(10).join(pins), 2)}
  (instances
    (project "{PROJECT}"
      (path "/{uid('root')}"
        (reference "{part.ref}")
        (unit 1)
      )
    )
  )
)'''


def net_stubs() -> str:
    blocks = []
    for part in PARTS:
        st = TYPES[part.symbol]
        for pin in st.pins:
            px, py, angle = st.pin_positions[pin.number]
            x = part.x + px
            y = part.y - py
            dx = -5.08 if angle == 0 else 5.08
            x2 = x + dx
            net = NETS[(part.ref, pin.number)]
            wire_id = uid(f"wire/{part.ref}/{pin.number}")
            label_id = uid(f"label/{part.ref}/{pin.number}")
            label_angle = 180 if angle == 0 else 0
            justify = "right bottom" if angle == 0 else "left bottom"
            blocks.append(f'''(wire
  (pts (xy {fnum(x)} {fnum(y)}) (xy {fnum(x2)} {fnum(y)}))
  (stroke (width 0) (type default))
  (uuid "{wire_id}")
)''')
            blocks.append(f'''(label "{net}"
  (at {fnum(x2)} {fnum(y)} {label_angle})
  (fields_autoplaced yes)
  {indent(effects(1.0, justify=justify), 2)}
  (uuid "{label_id}")
)''')
    return "\n".join(blocks)


def text_note(text: str, x: float, y: float, size: float = 1.27, bold: bool = False) -> str:
    bold_line = " (bold yes)" if bold else ""
    return f'''(text "{text}"
  (exclude_from_sim no)
  (at {fnum(x)} {fnum(y)} 0)
  (effects (font (size {fnum(size)} {fnum(size)}){bold_line}) (justify left bottom))
  (uuid "{uid(f'text/{text}/{x}/{y}')}")
)'''


def build_types() -> None:
    add_type("ESP32_C3_SUPERMINI", "U", 22.86, [
        Pin("5V", "5V", "right", "power_in"), Pin("GND", "GND", "right", "power_in"),
        Pin("3V3", "3V3", "right", "power_out"), Pin("GPIO4", "GPIO4/ADC", "right", "bidirectional"),
        Pin("GPIO3", "GPIO3/ADC", "right", "bidirectional"), Pin("GPIO2", "GPIO2/STRAP", "right", "bidirectional"),
        Pin("GPIO1", "GPIO1/ADC", "right", "bidirectional"), Pin("GPIO0", "GPIO0/ADC", "right", "bidirectional"),
        Pin("GPIO5", "GPIO5", "left", "bidirectional"), Pin("GPIO6", "GPIO6", "left", "bidirectional"),
        Pin("GPIO7", "GPIO7", "left", "bidirectional"), Pin("GPIO8", "GPIO8/LED/STRAP", "left", "bidirectional"),
        Pin("GPIO9", "GPIO9/BOOT", "left", "bidirectional"), Pin("GPIO10", "GPIO10", "left", "bidirectional"),
        Pin("GPIO20", "GPIO20", "left", "bidirectional"), Pin("GPIO21", "GPIO21", "left", "bidirectional"),
    ], "ESP32-C3 Super Mini castellated module")
    add_type("TB6612FNG_MODULE", "U", 22.86, [
        Pin("VM", "VM", "left", "power_in"), Pin("VCC", "VCC", "left", "power_in"),
        Pin("GND1", "GND", "left", "power_in"), Pin("AO1", "AO1", "left", "power_out"),
        Pin("AO2", "AO2", "left", "power_out"), Pin("BO2", "BO2", "left", "power_out"),
        Pin("BO1", "BO1", "left", "power_out"), Pin("GND2", "GND", "left", "power_in"),
        Pin("PWMA", "PWMA", "right", "input"), Pin("AIN2", "AIN2", "right", "input"),
        Pin("AIN1", "AIN1", "right", "input"), Pin("STBY", "STBY", "right", "input"),
        Pin("BIN1", "BIN1", "right", "input"), Pin("BIN2", "BIN2", "right", "input"),
        Pin("PWMB", "PWMB", "right", "input"), Pin("GND3", "GND", "right", "power_in"),
    ], "TB6612FNG dual motor-driver breakout")
    add_type("MATEK_MICRO_BEC", "U", 17.78, [
        Pin("VIN_6-30V", "VIN 6-30V", "left", "power_in"), Pin("GND1", "GND", "left", "power_in"),
        Pin("5V_OUT", "5V OUT", "right", "power_out"), Pin("GND2", "GND", "right", "power_in"),
    ], "Matek 6-30V synchronous BEC configured for 5V")
    add_type("PASSIVE_2", "R", 7.62, [Pin("1", "1", "left"), Pin("2", "2", "right")], "Generic two-pin passive")
    add_type("CAPACITOR", "C", 7.62, [Pin("1", "+", "left"), Pin("2", "-", "right")], "Capacitor; pin 1 positive for polarized parts")
    add_type("DIODE", "D", 7.62, [Pin("2", "A", "left"), Pin("1", "K", "right")], "Diode; pin 1 cathode, pin 2 anode")
    add_type("IR_LED", "D", 7.62, [Pin("2", "A", "left"), Pin("1", "K", "right")], "TSAL6100 infrared LED; pin 1 cathode, pin 2 anode")
    add_type("PHOTOTRANSISTOR", "Q", 10.16, [Pin("1", "C", "left"), Pin("2", "E", "right")], "PT334-6B phototransistor; verify physical lead polarity before PCB")
    add_type("NMOS_GSD", "Q", 10.16, [Pin("1", "G", "left", "input"), Pin("2", "S", "right", "power_in"), Pin("3", "D", "right", "power_out")], "AO3400A N-channel MOSFET, pins 1=G 2=S 3=D")
    add_type("CONNECTOR_2", "J", 10.16, [Pin("1", "+/1", "left"), Pin("2", "-/2", "right")], "Two-pin connector")
    add_type("MOTOR_2", "M", 10.16, [Pin("1", "+", "left"), Pin("2", "-", "right")], "Two-wire DC motor")
    add_type("SWITCH_NO", "SW", 10.16, [Pin("1", "1", "left"), Pin("2", "2", "right")], "Normally-open push button")
    add_type("SOLDER_JUMPER", "SJ", 10.16, [Pin("1", "1", "left"), Pin("2", "2", "right")], "Normally-closed solder jumper")
    add_type("TESTPOINT", "TP", 7.62, [Pin("1", "TP", "left")], "Single test point")


def build_parts() -> None:
    r0805 = "Resistor_SMD:R_0805_2012Metric"
    c0805 = "Capacitor_SMD:C_0805_2012Metric"
    sma = "Diode_SMD:D_SMA"
    sot23 = "Package_TO_SOT_SMD:SOT-23"
    led5 = "LED_THT:LED_D5.0mm"
    jst = "Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal"
    wire2 = "Connector_Wire:SolderWire-1x02_P5.08mm_Drill1mm"

    # POWER INPUT AND REGULATION
    add_part("J1", "Tattu LiHV 2S / JST-PH", "CONNECTOR_2", 25, 35, jst,
             nets={"1": "VBAT", "2": "GND"})
    add_part("C1", "470uF 25V", "CAPACITOR", 25, 50, "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
             nets={"1": "VBAT", "2": "GND"})
    add_part("C2", "100nF", "CAPACITOR", 25, 63, c0805, nets={"1": "VBAT", "2": "GND"})
    add_part("U3", "Matek Micro BEC 5V", "MATEK_MICRO_BEC", 62, 45,
             "LEA_PAREDES:Matek_MicroBEC_6-30V_Castellated",
             nets={"VIN_6-30V": "VBAT", "GND1": "GND", "5V_OUT": "+5V_RAW", "GND2": "GND"})
    add_part("D1", "SS14 USB isolation", "DIODE", 95, 35, sma,
             nets={"2": "+5V_RAW", "1": "ESP_5V"})
    add_part("C3", "10uF", "CAPACITOR", 95, 50, c0805, nets={"1": "+5V_RAW", "2": "GND"})
    add_part("C4", "100nF", "CAPACITOR", 95, 63, c0805, nets={"1": "+5V_RAW", "2": "GND"})
    add_part("TP1", "VBAT", "TESTPOINT", 25, 76, "TestPoint:TestPoint_Pad_D1.5mm", nets={"1": "VBAT"})
    add_part("TP2", "+5V_RAW", "TESTPOINT", 62, 76, "TestPoint:TestPoint_Pad_D1.5mm", nets={"1": "+5V_RAW"})
    add_part("TP3", "GND", "TESTPOINT", 95, 76, "TestPoint:TestPoint_Pad_D1.5mm", nets={"1": "GND"})

    # MCU AND MOTOR DRIVER
    add_part("U1", "ESP32-C3 Super Mini", "ESP32_C3_SUPERMINI", 145, 47,
             "LEA_PAREDES:ESP32-C3_SuperMini_Castellated",
             nets={"5V": "ESP_5V", "GND": "GND", "3V3": "+3V3", "GPIO4": "SENS_R", "GPIO3": "SENS_L",
                   "GPIO2": "PWM_A", "GPIO1": "SENS_FR", "GPIO0": "SENS_FL", "GPIO5": "AIN1",
                   "GPIO6": "AIN2", "GPIO7": "BIN1", "GPIO8": "PWM_B", "GPIO9": "START_BTN",
                   "GPIO10": "BIN2", "GPIO20": "FAN_PWM", "GPIO21": "IR_EN"})
    add_part("C5", "10uF", "CAPACITOR", 125, 76, c0805, nets={"1": "+3V3", "2": "GND"})
    add_part("C6", "100nF", "CAPACITOR", 145, 76, c0805, nets={"1": "+3V3", "2": "GND"})
    add_part("U2", "TB6612FNG module", "TB6612FNG_MODULE", 220, 47,
             "LEA_PAREDES:TB6612FNG_Module_Castellated",
             nets={"VM": "VBAT", "VCC": "+3V3", "GND1": "GND", "AO1": "MOTOR_L1", "AO2": "MOTOR_L2",
                   "BO2": "MOTOR_R2", "BO1": "MOTOR_R1", "GND2": "GND", "PWMA": "PWM_A", "AIN2": "AIN2",
                   "AIN1": "AIN1", "STBY": "STBY_EN", "BIN1": "BIN1", "BIN2": "BIN2", "PWMB": "PWM_B", "GND3": "GND"})
    add_part("R17", "10k PWM_A pull-up", "PASSIVE_2", 180, 30, r0805, nets={"1": "+3V3", "2": "PWM_A"})
    add_part("R18", "10k PWM_B pull-up", "PASSIVE_2", 180, 42, r0805, nets={"1": "+3V3", "2": "PWM_B"})
    add_part("R19", "10k STBY pull-up", "PASSIVE_2", 180, 54, r0805, nets={"1": "+3V3", "2": "STBY_EN"})
    add_part("R20", "10k BOOT pull-up", "PASSIVE_2", 180, 66, r0805, nets={"1": "+3V3", "2": "START_BTN"})
    add_part("SW1", "START / BOOT", "SWITCH_NO", 180, 78, "Button_Switch_THT:SW_PUSH_6mm",
             nets={"1": "START_BTN", "2": "GND"})
    add_part("J2", "MOTOR LEFT", "CONNECTOR_2", 275, 38, wire2,
             nets={"1": "MOTOR_L1", "2": "MOTOR_L2"})
    add_part("J3", "MOTOR RIGHT", "CONNECTOR_2", 275, 60, wire2,
             nets={"1": "MOTOR_R1", "2": "MOTOR_R2"})
    add_part("TP4", "+3V3", "TESTPOINT", 125, 88, "TestPoint:TestPoint_Pad_D1.5mm", nets={"1": "+3V3"})

    # SHARED IR EMITTER DRIVER
    add_part("R13", "100R IR gate", "PASSIVE_2", 30, 112, r0805, nets={"1": "IR_EN", "2": "IR_GATE"})
    add_part("R14", "10k IR gate pull-down", "PASSIVE_2", 30, 125, r0805, nets={"1": "IR_GATE", "2": "GND"})
    add_part("Q5", "AO3400A IR", "NMOS_GSD", 65, 118, sot23,
             nets={"1": "IR_GATE", "2": "GND", "3": "IR_LED_K"})

    # FOUR SENSOR PAIRS. Two 150R in parallel feed each TSAL6100.
    sensor_data = [
        ("FL", 95, "SENS_FL", "IR_FL_A", "FRONT LEFT"),
        ("FR", 150, "SENS_FR", "IR_FR_A", "FRONT RIGHT"),
        ("L", 205, "SENS_L", "IR_L_A", "SIDE LEFT"),
        ("R", 260, "SENS_R", "IR_R_A", "SIDE RIGHT"),
    ]
    resistor_index = 1
    photo_index = 1
    for suffix, x, adc_net, anode_net, label in sensor_data:
        add_part(f"R{resistor_index}", "150R", "PASSIVE_2", x, 108, r0805, nets={"1": "+5V_RAW", "2": anode_net})
        resistor_index += 1
        add_part(f"R{resistor_index}", "150R", "PASSIVE_2", x, 120, r0805, nets={"1": "+5V_RAW", "2": anode_net})
        resistor_index += 1
        add_part(f"D{photo_index + 1}", f"TSAL6100 {label}", "IR_LED", x, 134, led5,
                 nets={"2": anode_net, "1": "IR_LED_K"})
        add_part(f"Q{photo_index}", f"PT334-6B {label}", "PHOTOTRANSISTOR", x, 151, led5,
                 nets={"1": "+3V3", "2": adc_net})
        add_part(f"R{8 + photo_index}", "10k sensor", "PASSIVE_2", x, 166, r0805,
                 nets={"1": adc_net, "2": "GND"})
        photo_index += 1

    # TURBINE: 5V rail can later be isolated by opening SJ1.
    add_part("SJ1", "FAN SUPPLY / closed", "SOLDER_JUMPER", 185, 198,
             "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm",
             nets={"1": "+5V_RAW", "2": "+5V_TURBINE"})
    add_part("M1", "Coreless 8520 / turbine", "MOTOR_2", 225, 198, wire2,
             nets={"1": "+5V_TURBINE", "2": "FAN_DRAIN"})
    add_part("D6", "SS34 flyback", "DIODE", 225, 214, sma,
             nets={"2": "FAN_DRAIN", "1": "+5V_TURBINE"})
    add_part("R15", "100R FAN gate", "PASSIVE_2", 185, 230, r0805,
             nets={"1": "FAN_PWM", "2": "FAN_GATE"})
    add_part("R16", "10k FAN gate pull-down", "PASSIVE_2", 185, 243, r0805,
             nets={"1": "FAN_GATE", "2": "GND"})
    add_part("Q6", "AO3400A FAN", "NMOS_GSD", 225, 237, sot23,
             nets={"1": "FAN_GATE", "2": "GND", "3": "FAN_DRAIN"})
    add_part("C7", "470uF DNP / optional", "CAPACITOR", 270, 198,
             "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", dnp=True,
             nets={"1": "+5V_TURBINE", "2": "GND"})
    add_part("C8", "100nF", "CAPACITOR", 270, 214, c0805,
             nets={"1": "+5V_TURBINE", "2": "GND"})


def generate_schematic() -> str:
    definitions = "\n".join(indent(symbol_definition(t, embedded=True), 4) for t in TYPES.values())
    instances = "\n".join(indent(part_instance(p), 2) for p in PARTS)
    notes = [
        text_note("LEA_PAREDES — ESQUEMATICO V1", 15, 15, 2.0, True),
        text_note("POWER / BEC 5V", 15, 23, 1.4, True),
        text_note("MCU + TB6612 + MOTORES", 120, 23, 1.4, True),
        text_note("4 PARES IR: FL / FR / L / R", 90, 96, 1.4, True),
        text_note("TURBINA 8520 — PWM LOW-SIDE", 170, 187, 1.4, True),
        text_note("J1 pin 1 = BAT+; VERIFICAR POLARIDAD REAL DEL JST-PH ANTES DE CONECTAR", 15, 260, 1.15, True),
        text_note("Matek: salida 5V; puente 9V ABIERTO. Bateria LiHV 2S: 7.6V nominal / 8.7V cargada.", 15, 266, 1.05),
        text_note("PWM_A=GPIO2 (strap, pull-up 10k). PWM_B=GPIO8 (LED onboard puede variar brillo). START=GPIO9/BOOT.", 15, 272, 1.05),
        text_note("Motores 6V reciben VBAT por TB6612: limitar/acelerar suavemente por firmware si la temperatura o corriente son altas.", 15, 278, 1.05),
        text_note("C7 es opcional/DNP. Abrir SJ1 si en el futuro la turbina usa otro regulador.", 15, 284, 1.05),
    ]
    return f'''(kicad_sch
  (version 20231120)
  (generator "lea_paredes_generator")
  (generator_version "1.0")
  (uuid "{uid('root')}")
  (paper "A3")
  (lib_symbols
{definitions}
  )
{indent(net_stubs(), 2)}
{indent(chr(10).join(notes), 2)}
{instances}
  (sheet_instances
    (path "/" (page "1"))
  )
)\n'''


def generate_library() -> str:
    definitions = "\n".join(indent(symbol_definition(t, embedded=False), 2) for t in TYPES.values())
    return f'''(kicad_symbol_lib
  (version 20231120)
  (generator "lea_paredes_generator")
  (generator_version "1.0")
{definitions}
)\n'''


def validate(text: str) -> None:
    depth = 0
    in_string = False
    escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced S-expression")
    if depth != 0 or in_string:
        raise ValueError(f"invalid S-expression: depth={depth}, in_string={in_string}")
    if len(NETS) != sum(len(TYPES[p.symbol].pins) for p in PARTS):
        raise ValueError("not every physical pin has an assigned net")


def main() -> None:
    build_types()
    build_parts()
    schematic = generate_schematic()
    library = generate_library()
    validate(schematic)
    validate(library)
    (OUT / "LEA_PAREDES.kicad_sch").write_text(schematic, encoding="utf-8")
    (OUT / "LEA_PAREDES.kicad_sym").write_text(library, encoding="utf-8")
    print(f"Generated {len(PARTS)} parts, {len(NETS)} connected pins, {len(TYPES)} symbol types")


if __name__ == "__main__":
    main()
