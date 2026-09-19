"""Labyrinth Control - panel de pruebas Wi-Fi para ESP32-S3 + DRV8833."""

from __future__ import annotations

import json
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BG = "#0b1018"
PANEL = "#121a26"
PANEL_2 = "#182333"
TEXT = "#f3f6fb"
MUTED = "#8fa0b8"
CYAN = "#21d4d8"
GREEN = "#41d68b"
RED = "#ff5266"
ORANGE = "#ffad42"
BORDER = "#27364a"


class LabyrinthControl(tk.Tk):
    """Interfaz principal."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Labyrinth Control")
        self.geometry("1120x720")
        self.minsize(980, 650)
        self.configure(bg=BG)

        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.connected = False
        self.last_command = "STOP"
        self.active_motion: str | None = None
        self.command_in_flight = False
        self.last_keepalive = 0.0

        self.host_var = tk.StringVar(value="192.168.4.1")
        self.left_speed = tk.IntVar(value=100)
        self.right_speed = tk.IntVar(value=100)
        self.invert_left = tk.BooleanVar(value=False)
        self.invert_right = tk.BooleanVar(value=False)
        self.left_output = tk.StringVar(value="0")
        self.right_output = tk.StringVar(value="0")
        self.uptime_var = tk.StringVar(value="--:--")

        self._configure_styles()
        self._build_ui()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(60, self._process_results)
        self.after(100, self._service_loop)

    def _configure_styles(self) -> None:
        self.option_add("*Font", ("Segoe UI", 10))
        self.option_add("*foreground", TEXT)
        self.option_add("*background", BG)

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=22)

        self._build_header(outer)

        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True, pady=(22, 0))
        body.grid_columnconfigure(0, weight=1, uniform="body")
        body.grid_columnconfigure(1, weight=1, uniform="body")
        body.grid_rowconfigure(0, weight=1)

        left_panel = self._card(body)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 11))
        right_panel = self._card(body)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(11, 0))

        self._build_motor_controls(left_panel)
        self._build_drive_controls(right_panel)
        self._build_footer(outer)

    def _build_header(self, parent: tk.Widget) -> None:
        header = tk.Frame(parent, bg=BG)
        header.pack(fill="x")

        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")
        tk.Label(
            title_box,
            text="LABYRINTH",
            font=("Segoe UI Semibold", 24),
            fg=TEXT,
            bg=BG,
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="ESP32-S3  •  PANEL DE PUESTA A PUNTO",
            font=("Segoe UI", 9),
            fg=MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(2, 0))

        connection = tk.Frame(header, bg=BG)
        connection.pack(side="right", pady=4)
        tk.Label(connection, text="IP DEL ROBOT", fg=MUTED, bg=BG).grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.host_entry = tk.Entry(
            connection,
            textvariable=self.host_var,
            width=16,
            justify="center",
            bg=PANEL_2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=CYAN,
        )
        self.host_entry.grid(row=1, column=0, ipady=8, padx=(0, 8))
        self.connect_button = tk.Button(
            connection,
            text="CONECTAR",
            command=self.toggle_connection,
            cursor="hand2",
            bg=CYAN,
            fg="#071316",
            activebackground="#49e5e8",
            activeforeground="#071316",
            relief="flat",
            padx=22,
            pady=8,
            font=("Segoe UI Semibold", 10),
        )
        self.connect_button.grid(row=1, column=1)

    def _card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=PANEL,
            highlightthickness=1,
            highlightbackground=BORDER,
        )

    def _section_title(self, parent: tk.Widget, title: str, subtitle: str) -> None:
        tk.Label(
            parent,
            text=title,
            font=("Segoe UI Semibold", 17),
            fg=TEXT,
            bg=PANEL,
        ).pack(anchor="w")
        tk.Label(parent, text=subtitle, fg=MUTED, bg=PANEL).pack(
            anchor="w", pady=(3, 0)
        )

    def _build_motor_controls(self, parent: tk.Frame) -> None:
        content = tk.Frame(parent, bg=PANEL)
        content.pack(fill="both", expand=True, padx=26, pady=24)
        self._section_title(
            content,
            "Velocidad de motores",
            "PWM independiente para compensar diferencias mecánicas.",
        )

        self._motor_slider(
            content,
            "MOTOR IZQUIERDO",
            self.left_speed,
            self.left_output,
            self.invert_left,
        ).pack(fill="x", pady=(30, 16))
        self._motor_slider(
            content,
            "MOTOR DERECHO",
            self.right_speed,
            self.right_output,
            self.invert_right,
        ).pack(fill="x", pady=16)

        safety = tk.Frame(content, bg="#1b2024", highlightthickness=1, highlightbackground="#4b3d2b")
        safety.pack(fill="x", side="bottom", pady=(18, 0))
        tk.Label(
            safety,
            text="MODO SEGURO",
            font=("Segoe UI Semibold", 9),
            fg=ORANGE,
            bg="#1b2024",
        ).pack(anchor="w", padx=15, pady=(12, 2))
        tk.Label(
            safety,
            text="Los botones deben mantenerse presionados. Al soltarlos, los motores se detienen.",
            wraplength=430,
            justify="left",
            fg="#d7c5a8",
            bg="#1b2024",
        ).pack(anchor="w", padx=15, pady=(0, 12))

    def _motor_slider(
        self,
        parent: tk.Widget,
        label: str,
        speed_var: tk.IntVar,
        output_var: tk.StringVar,
        invert_var: tk.BooleanVar,
    ) -> tk.Frame:
        box = tk.Frame(parent, bg=PANEL_2, highlightthickness=1, highlightbackground=BORDER)
        top = tk.Frame(box, bg=PANEL_2)
        top.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(top, text=label, font=("Segoe UI Semibold", 10), fg=MUTED, bg=PANEL_2).pack(side="left")
        value_label = tk.Label(
            top,
            textvariable=speed_var,
            width=4,
            font=("Consolas", 18, "bold"),
            fg=CYAN,
            bg=PANEL_2,
        )
        value_label.pack(side="right")

        slider = tk.Scale(
            box,
            from_=0,
            to=255,
            orient="horizontal",
            variable=speed_var,
            showvalue=False,
            resolution=1,
            bg=PANEL_2,
            fg=TEXT,
            troughcolor="#29384c",
            activebackground=CYAN,
            highlightthickness=0,
            bd=0,
            sliderrelief="flat",
            length=380,
        )
        slider.pack(fill="x", padx=13)

        bottom = tk.Frame(box, bg=PANEL_2)
        bottom.pack(fill="x", padx=16, pady=(5, 13))
        tk.Checkbutton(
            bottom,
            text="Invertir sentido",
            variable=invert_var,
            selectcolor=PANEL_2,
            activebackground=PANEL_2,
            activeforeground=TEXT,
            fg=MUTED,
            bg=PANEL_2,
            command=self._resend_active_motion,
        ).pack(side="left")
        tk.Label(bottom, text="Salida actual:", fg=MUTED, bg=PANEL_2).pack(side="right")
        tk.Label(
            bottom,
            textvariable=output_var,
            font=("Consolas", 10, "bold"),
            fg=TEXT,
            bg=PANEL_2,
            width=5,
        ).pack(side="right")
        return box

    def _build_drive_controls(self, parent: tk.Frame) -> None:
        content = tk.Frame(parent, bg=PANEL)
        content.pack(fill="both", expand=True, padx=26, pady=24)
        self._section_title(
            content,
            "Control manual",
            "Mantené presionado un botón o usá W A S D.",
        )

        dpad = tk.Frame(content, bg=PANEL)
        dpad.pack(pady=(28, 20))
        dpad.grid_columnconfigure((0, 1, 2), minsize=102)
        dpad.grid_rowconfigure((0, 1, 2), minsize=76)

        self._motion_button(dpad, "▲\nADELANTE", "forward").grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self._motion_button(dpad, "◀\nIZQUIERDA", "left").grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.stop_button = tk.Button(
            dpad,
            text="STOP",
            command=self.stop,
            cursor="hand2",
            bg=RED,
            fg="white",
            activebackground="#ff7584",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI Semibold", 12),
        )
        self.stop_button.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
        self._motion_button(dpad, "▶\nDERECHA", "right").grid(row=1, column=2, padx=5, pady=5, sticky="nsew")
        self._motion_button(dpad, "▼\nATRÁS", "backward").grid(row=2, column=1, padx=5, pady=5, sticky="nsew")

        telemetry = tk.Frame(content, bg=PANEL_2, highlightthickness=1, highlightbackground=BORDER)
        telemetry.pack(fill="x", side="bottom")
        tk.Label(telemetry, text="ESTADO DEL ROBOT", font=("Segoe UI Semibold", 10), fg=MUTED, bg=PANEL_2).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 10)
        )
        self.command_label = self._status_value(telemetry, "ÚLTIMO COMANDO", "STOP", 0)
        self.uptime_label = self._status_value(telemetry, "ENCENDIDO", "--:--", 1, self.uptime_var)
        self.clients_label = self._status_value(telemetry, "CLIENTES WI-FI", "0", 2)
        telemetry.grid_columnconfigure((0, 1, 2), weight=1)

    def _motion_button(self, parent: tk.Widget, text: str, motion: str) -> tk.Button:
        button = tk.Button(
            parent,
            text=text,
            cursor="hand2",
            bg=PANEL_2,
            fg=TEXT,
            activebackground=CYAN,
            activeforeground="#071316",
            relief="flat",
            font=("Segoe UI Semibold", 10),
        )
        button.bind("<ButtonPress-1>", lambda _event, m=motion: self.start_motion(m))
        button.bind("<ButtonRelease-1>", lambda _event: self.stop())
        button.bind("<Leave>", lambda _event: self.stop() if self.active_motion == motion else None)
        return button

    def _status_value(
        self,
        parent: tk.Widget,
        caption: str,
        initial: str,
        column: int,
        variable: tk.StringVar | None = None,
    ) -> tk.Label:
        cell = tk.Frame(parent, bg=PANEL_2)
        cell.grid(row=1, column=column, sticky="ew", padx=16, pady=(0, 15))
        tk.Label(cell, text=caption, font=("Segoe UI", 8), fg=MUTED, bg=PANEL_2).pack(anchor="w")
        label = tk.Label(
            cell,
            text=initial if variable is None else "",
            textvariable=variable,
            font=("Consolas", 14, "bold"),
            fg=TEXT,
            bg=PANEL_2,
        )
        label.pack(anchor="w", pady=(3, 0))
        return label

    def _build_footer(self, parent: tk.Widget) -> None:
        footer = tk.Frame(parent, bg=BG)
        footer.pack(fill="x", pady=(16, 0))
        self.status_dot = tk.Label(footer, text="●", fg=RED, bg=BG, font=("Segoe UI", 13))
        self.status_dot.pack(side="left")
        self.status_text = tk.Label(
            footer,
            text="DESCONECTADO — conectá Windows a LABERINTO-ESP32",
            fg=MUTED,
            bg=BG,
        )
        self.status_text.pack(side="left", padx=(6, 0))
        tk.Label(
            footer,
            text="ESPACIO = parada de emergencia",
            fg=MUTED,
            bg=BG,
        ).pack(side="right")

    def _bind_keys(self) -> None:
        keymap = {"w": "forward", "a": "left", "s": "backward", "d": "right"}
        for key, motion in keymap.items():
            self.bind(f"<KeyPress-{key}>", lambda _event, m=motion: self.start_motion(m))
            self.bind(f"<KeyRelease-{key}>", lambda _event: self.stop())
            self.bind(f"<KeyPress-{key.upper()}>", lambda _event, m=motion: self.start_motion(m))
            self.bind(f"<KeyRelease-{key.upper()}>", lambda _event: self.stop())
        self.bind("<space>", lambda _event: self.stop())

    def toggle_connection(self) -> None:
        if self.connected:
            self.stop()
            self._set_connected(False, "DESCONECTADO")
            return
        self.status_text.config(text="BUSCANDO ROBOT...")
        self.connect_button.config(state="disabled")
        self._request_async("status", "/status", method="GET")

    def start_motion(self, motion: str) -> None:
        if not self.connected or self.active_motion == motion:
            return
        self.active_motion = motion
        self._send_motion(motion)

    def _resend_active_motion(self) -> None:
        if self.active_motion:
            self._send_motion(self.active_motion)

    def stop(self) -> None:
        self.active_motion = None
        self._set_outputs(0, 0)
        self.last_command = "STOP"
        self.command_label.config(text="STOP", fg=RED)
        if self.connected:
            self._request_async("command", "/motors?left=0&right=0", method="POST")

    def _send_motion(self, motion: str) -> None:
        left = self.left_speed.get()
        right = self.right_speed.get()
        commands = {
            "forward": (left, right, "ADELANTE"),
            "backward": (-left, -right, "ATRÁS"),
            "left": (-left, right, "IZQUIERDA"),
            "right": (left, -right, "DERECHA"),
        }
        left_out, right_out, label = commands[motion]
        if self.invert_left.get():
            left_out *= -1
        if self.invert_right.get():
            right_out *= -1

        self._set_outputs(left_out, right_out)
        self.last_command = label
        self.command_label.config(text=label, fg=GREEN)
        self.last_keepalive = time.monotonic()
        self._request_async(
            "command",
            f"/motors?left={left_out}&right={right_out}",
            method="POST",
        )

    def _set_outputs(self, left: int, right: int) -> None:
        self.left_output.set(str(left))
        self.right_output.set(str(right))

    def _base_url(self) -> str:
        host = self.host_var.get().strip().replace("http://", "").replace("https://", "").rstrip("/")
        return f"http://{host}"

    def _request_async(self, kind: str, path: str, method: str = "GET") -> None:
        if kind == "command" and self.command_in_flight:
            return
        if kind == "command":
            self.command_in_flight = True

        def worker() -> None:
            try:
                request = Request(self._base_url() + path, method=method)
                with urlopen(request, timeout=0.65) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self.result_queue.put((kind, payload))
            except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                self.result_queue.put(("error", (kind, str(exc))))

        threading.Thread(target=worker, daemon=True).start()

    def _process_results(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "error":
                    request_kind, _message = payload  # type: ignore[misc]
                    if request_kind == "command":
                        self.command_in_flight = False
                    self._set_connected(False, "SIN RESPUESTA DEL ROBOT")
                    self.active_motion = None
                    self._set_outputs(0, 0)
                else:
                    if kind == "command":
                        self.command_in_flight = False
                    self._set_connected(True, "CONECTADO AL ESP32-S3")
                    if isinstance(payload, dict):
                        self._update_status(payload)
        except queue.Empty:
            pass
        self.after(60, self._process_results)

    def _update_status(self, payload: dict[str, object]) -> None:
        uptime_ms = int(payload.get("uptime_ms", 0))
        minutes, seconds = divmod(uptime_ms // 1000, 60)
        hours, minutes = divmod(minutes, 60)
        self.uptime_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.clients_label.config(text=str(payload.get("clients", 0)))

    def _set_connected(self, connected: bool, text: str) -> None:
        self.connected = connected
        self.status_dot.config(fg=GREEN if connected else RED)
        self.status_text.config(text=text)
        self.connect_button.config(
            text="DESCONECTAR" if connected else "CONECTAR",
            state="normal",
            bg=PANEL_2 if connected else CYAN,
            fg=TEXT if connected else "#071316",
        )

    def _service_loop(self) -> None:
        now = time.monotonic()
        if self.connected and self.active_motion and now - self.last_keepalive >= 0.25:
            self._send_motion(self.active_motion)
        elif self.connected and not self.command_in_flight:
            # La consulta de estado también permite detectar una desconexión.
            if not hasattr(self, "_last_poll") or now - self._last_poll >= 1.0:
                self._last_poll = now
                self._request_async("status", "/status", method="GET")
        self.after(100, self._service_loop)

    def _on_close(self) -> None:
        if self.connected:
            try:
                request = Request(self._base_url() + "/motors?left=0&right=0", method="POST")
                urlopen(request, timeout=0.25).close()
            except OSError:
                pass
        self.destroy()


if __name__ == "__main__":
    app = LabyrinthControl()
    app.mainloop()
