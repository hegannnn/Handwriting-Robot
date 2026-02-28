from flask import Flask, render_template, request, jsonify
import os
import sys
import time
import io
import contextlib
from typing import List, Optional

sys.path.append(os.path.abspath("./src"))

try:
    from word_assembler import assemble_human_hierarchy_text as assemble_words
except ImportError:
    try:
        from word_assembler import assemble_words
    except ImportError:
        def assemble_words(text):
            return []

try:
    from gcode_generator import strokes_to_gcode
except ImportError:
    strokes_to_gcode = None

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    serial = None
    list_ports = None

app = Flask(__name__)


def _parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _available_ports() -> List[str]:
    if list_ports is None:
        return []
    return [p.device for p in list_ports.comports() if p.device]


def _resolve_port(explicit_port: Optional[str]) -> Optional[str]:
    if explicit_port:
        return explicit_port.strip()

    env_port = os.getenv("ROBOT_SERIAL_PORT", "").strip()
    if env_port:
        return env_port

    ports = _available_ports()
    if len(ports) == 1:
        return ports[0]
    return None


def _wait_for_ok(ser, timeout_s=8.0):
    deadline = time.time() + timeout_s
    last_lines: List[str] = []

    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue

        line = raw.decode("utf-8", errors="ignore").strip()
        if not line:
            continue

        last_lines.append(line)
        if len(last_lines) > 5:
            last_lines.pop(0)

        lower = line.lower()
        if lower.startswith("ok"):
            return
        if "error" in lower or "alarm" in lower:
            raise RuntimeError(f"Controller error: {line}")

    tail = " | ".join(last_lines) if last_lines else "no response"
    raise TimeoutError(f"Timed out waiting for controller ack ({tail}).")


def _stream_gcode(gcode_lines: List[str], port: str, baudrate: int, line_timeout_s=8.0):
    if serial is None:
        raise RuntimeError("pyserial is not installed. Run: pip install pyserial")

    sent_lines = 0

    with serial.Serial(port=port, baudrate=baudrate, timeout=1, write_timeout=2) as ser:
        time.sleep(2.0)
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        ser.write(b"\r\n")
        ser.flush()
        time.sleep(0.2)

        for raw_line in gcode_lines:
            line = raw_line.split(";", 1)[0].strip()
            if not line:
                continue

            ser.write((line + "\n").encode("ascii", errors="ignore"))
            ser.flush()
            _wait_for_ok(ser, timeout_s=line_timeout_s)
            sent_lines += 1

    return sent_lines


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ports', methods=['GET'])
def ports():
    return jsonify({
        "status": "success",
        "ports": _available_ports(),
        "pyserial_installed": serial is not None
    })


@app.route('/preview', methods=['POST'])
def preview():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()

    if not text:
        return jsonify({
            "status": "success",
            "arrangement": []
        })

    arrangement = assemble_words(text)

    return jsonify({
        "status": "success",
        "arrangement": arrangement
    })


@app.route('/process', methods=['POST'])
def process():
    if strokes_to_gcode is None:
        return jsonify({
            "status": "error",
            "message": "gcode_generator import failed."
        }), 500

    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()

    if not text:
        return jsonify({
            "status": "error",
            "message": "Please enter text before starting."
        }), 400

    filename = (data.get("filename") or "web_handwriting").strip() or "web_handwriting"
    filename = "".join(c for c in filename if c.isalnum() or c in ("_", "-"))
    if not filename:
        filename = "web_handwriting"

    strokes = assemble_words(text)
    if not strokes:
        return jsonify({
            "status": "error",
            "message": "No drawable strokes generated for this input."
        }), 400

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            gcode_lines = strokes_to_gcode(strokes, filename=filename)
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"G-code generation failed: {exc}"
        }), 500

    gcode_path = os.path.abspath(os.path.join("output_gcode", f"{filename}.gcode"))

    dry_run = _parse_bool(data.get("dry_run"), default=_parse_bool(os.getenv("ROBOT_DRY_RUN"), default=False))
    if dry_run:
        return jsonify({
            "status": "success",
            "message": "G-code generated (dry run only, not sent to robot).",
            "gcode_file": gcode_path,
            "strokes": len(strokes),
            "dry_run": True
        })

    if serial is None:
        return jsonify({
            "status": "error",
            "message": "pyserial not installed. Run: pip install pyserial"
        }), 500

    port = _resolve_port(data.get("port"))
    baudrate = int(data.get("baudrate") or os.getenv("ROBOT_BAUDRATE", "115200"))

    if not port:
        ports = _available_ports()
        return jsonify({
            "status": "error",
            "message": "No serial port selected. Set ROBOT_SERIAL_PORT or send port in /process.",
            "available_ports": ports
        }), 400

    try:
        sent = _stream_gcode(
            gcode_lines=gcode_lines,
            port=port,
            baudrate=baudrate,
            line_timeout_s=float(data.get("line_timeout_s") or os.getenv("ROBOT_LINE_TIMEOUT_S", "8"))
        )
    except Exception as exc:
        return jsonify({
            "status": "error",
            "message": f"Hardware write failed: {exc}",
            "port": port,
            "baudrate": baudrate,
            "gcode_file": gcode_path
        }), 500

    return jsonify({
        "status": "success",
        "message": f"Robot writing complete. Sent {sent} G-code lines on {port} @ {baudrate}.",
        "gcode_file": gcode_path,
        "strokes": len(strokes),
        "port": port,
        "baudrate": baudrate,
        "dry_run": False
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
