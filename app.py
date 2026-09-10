

from __future__ import annotations

import ast
import json
import math
import os
import random
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QPointF, QRectF, QThread, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QDoubleValidator, QFont, QIntValidator, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# -----------------------------
# Theme / design tokens
# -----------------------------
BG = "#070B12"
HEADER = "#0B111B"
PANEL = "#101722"
PANEL_ALT = "#0D141F"
CARD = "#121B28"
CARD_SOFT = "#141E2D"
BORDER = "#263244"
BORDER_SOFT = "#202A39"
TEXT = "#F3F6FB"
MUTED = "#9AA7B7"
MUTED_2 = "#6F7C8E"
ACCENT = "#8B6DFF"
ACCENT_SOFT = "#6F5DE6"
ACCENT_DARK = "#2A2450"
TEAL = "#5CC7D8"
TEAL_SOFT = "#3EA4B2"
TRACK = "#252E3C"
EVE_ACCENT = "#9A3B4A"
EVE_ACCENT_SOFT = "#6E2B38"
EVE_CARD = "#17121A"
EVE_BORDER = "#4A2A34"
WARN = "#D89C5C"

FONT = "Segoe UI"

ATTACKS = {
    "None": None,
    "Intercept-resend": "INTERCEPT_AND_RESENT",
    "PNS": "PNS",
    "Trojan Horse": "TROJAN_HORSE",
    "Double Click Event": "DOUBLE_CLICK_EVENT",
    "Time Correlation": "TIME_CORRELATION",
}

ATTACK_LABELS = {v: k for k, v in ATTACKS.items()}


# Fallbacks aligned with the current backend settings.py.
# In normal use, the UI reads settings.py directly; these are only used if the
# backend folder is not found yet.
FALLBACK_MAIN_SETTINGS = {
    "message_size": 200,
    "protocol": "bb84",
    "average_emitted_photon": -1.0,
    "quantum_canal_bit_loss": 0.00,
    "quantum_canal_bit_flip": 2.00,
    "qber_percent": 20,
    "qber_tolerance": 11,
    "attack_label": "Trojan Horse",
}

FALLBACK_ADVANCED_SETTINGS = {
    "message_interval": 5.0,
    "tolerance_message_not_receive": 4.9,
    "progress_bar": True,
    "perfect_apd_bob": True,
    "perfect_apd_eve": True,
    "breakdown_voltage": 7.0,
    "dead_time_min": 2.0,
    "dead_time_max": 6.0,
    "bias_voltage": 5.0,
    "gate_off_duration": 2.5,
    "gate_on_duration": 2.5,
    "many_clicks_gestion": "NONE",
    "after_pulsing": 0.0,
    "emission_click_event": 10,
    "timing_attack": 300.0,
}


def _load_settings_module() -> Any | None:
    """Load backend settings.py to reuse the real default values chosen by the backend."""
    backend_root = find_backend_root()
    if backend_root is None:
        return None
    settings_path = backend_root / "settings.py"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_qkd_backend_settings_defaults", settings_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None


def _num(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_num(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_frontend_defaults() -> tuple[dict[str, Any], dict[str, Any]]:
    """Return UI presets from backend settings.py, with safe fallback values only if needed."""
    main = dict(FALLBACK_MAIN_SETTINGS)
    advanced = dict(FALLBACK_ADVANCED_SETTINGS)
    module = _load_settings_module()
    if module is None:
        return main, advanced

    main["message_size"] = _int_num(getattr(module, "message_size", main["message_size"]), main["message_size"])
    main["protocol"] = str(getattr(module, "protocol", main["protocol"]))
    main["average_emitted_photon"] = _num(getattr(module, "average_emitted_photon", main["average_emitted_photon"]), main["average_emitted_photon"])
    main["quantum_canal_bit_loss"] = _num(getattr(module, "quantum_canal_bit_loss", main["quantum_canal_bit_loss"]), main["quantum_canal_bit_loss"])
    main["quantum_canal_bit_flip"] = _num(getattr(module, "quantum_canal_bit_flip", main["quantum_canal_bit_flip"]), main["quantum_canal_bit_flip"])
    main["qber_percent"] = _int_num(getattr(module, "qber_percent", main["qber_percent"]), main["qber_percent"])
    main["qber_tolerance"] = _int_num(getattr(module, "qber_tolerance", main["qber_tolerance"]), main["qber_tolerance"])

    selected_attack = "None"
    for label, flag in ATTACKS.items():
        if flag and bool(getattr(module, flag, False)):
            selected_attack = label
            break
    main["attack_label"] = selected_attack

    for key, default in advanced.items():
        if hasattr(module, key):
            value = getattr(module, key)
            if isinstance(default, bool):
                advanced[key] = bool(value)
            elif isinstance(default, int) and not isinstance(default, bool):
                advanced[key] = _int_num(value, default)
            elif isinstance(default, float):
                advanced[key] = _num(value, default)
            else:
                advanced[key] = str(value)

    return main, advanced


def backend_cancelled_result(config: SimulationConfig) -> SimulationResult:
    return SimulationResult(
        qber=0.0,
        final_key_size=0,
        eve_knowledge=0.0,
        key_agreement=0.0,
        communication_status="Stopped",
        attack_detected="—",
        sifted_bits=0.0,
        discarded_bits=0.0,
        lost=config.quantum_canal_bit_loss,
        flipped=config.quantum_canal_bit_flip,
        mode="Stopped",
        logs=[
            ("stop", "warn", "Backend process stopped by user."),
            ("debug", "muted", "No final simulation result was returned."),
        ],
    )


@dataclass
class SimulationConfig:
    message_size: int
    protocol: str
    average_emitted_photon: float
    quantum_canal_bit_loss: float
    quantum_canal_bit_flip: float
    qber_percent: int
    qber_tolerance: int
    attack_label: str
    attack_flag: str | None
    advanced: dict[str, Any]
    scenario_name: str | None = None


@dataclass
class SimulationResult:
    qber: float
    final_key_size: int
    eve_knowledge: float
    key_agreement: float
    communication_status: str
    attack_detected: str
    sifted_bits: float
    discarded_bits: float
    lost: float
    flipped: float
    mode: str
    logs: list[tuple[str, str, str]]


def default_result() -> SimulationResult:
    return SimulationResult(
        qber=4.8,
        final_key_size=76,
        eve_knowledge=0.0,
        key_agreement=96.0,
        communication_status="Ready",
        attack_detected="No",
        sifted_bits=48.0,
        discarded_bits=52.0,
        lost=2.0,
        flipped=2.0,
        mode="Waiting",
        logs=[
            ("--:--:--", "muted", "Frontend ready. Click Run Simulation to start."),
            ("--:--:--", "violet", "Real backend mode: the Run button calls manager.run_communication()."),
        ],
    )


def _percent_similarity(a: list[int], b: list[int]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return sum(1 for i in range(n) if a[i] == b[i]) / n * 100.0



def backend_error_result(config: SimulationConfig, reason: str, detail: str | None = None) -> SimulationResult:
    """Affiche une vraie erreur backend au lieu de fabriquer un faux résultat."""
    logs = [
        ("error", "warn", reason),
        ("hint", "muted", "Place frontend/app.py inside the repository root, next to manager.py/settings.py, or install backend dependencies."),
    ]
    if detail:
        short_detail = detail.strip().replace("\r", "")
        if len(short_detail) > 900:
            short_detail = short_detail[-900:]
        for line in short_detail.split("\n")[-8:]:
            if line.strip():
                logs.append(("trace", "muted", line.strip()))

    return SimulationResult(
        qber=0.0,
        final_key_size=0,
        eve_knowledge=0.0,
        key_agreement=0.0,
        communication_status="Backend error",
        attack_detected="—",
        sifted_bits=0.0,
        discarded_bits=0.0,
        lost=config.quantum_canal_bit_loss,
        flipped=config.quantum_canal_bit_flip,
        mode="Backend error",
        logs=logs,
    )

def _repo_root_candidates() -> list[Path]:
    here = Path(__file__).resolve()
    cwd = Path.cwd().resolve()
    candidates: list[Path] = []

    env_root = os.environ.get("QKD_BACKEND_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser().resolve())

    for base in (here.parent, cwd):
        candidates.append(base)
        candidates.extend(base.parents)
        candidates.append(base / "qkdSimulator")
        for parent in base.parents:
            candidates.append(parent / "qkdSimulator")

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            unique.append(candidate)
            seen.add(key)
    return unique


def find_backend_root() -> Path | None:
    for candidate in _repo_root_candidates():
        if (candidate / "manager.py").exists() and (candidate / "settings.py").exists():
            return candidate
    return None


def backend_search_report(max_paths: int = 24) -> str:
    paths = _repo_root_candidates()[:max_paths]
    lines = ["Backend search paths tried:"]
    lines.extend(f"- {path}" for path in paths)
    lines.append("Expected files in the same folder: manager.py and settings.py")
    lines.append("Tip: put app.py in qkdSimulator/frontend/app.py, or launch with QKD_BACKEND_ROOT=/path/to/qkdSimulator.")
    return "\n".join(lines)



@dataclass
class ScenarioPreset:
    """One clickable preset from the backend scenarios folder."""

    group: str
    name: str
    description: str
    attack_flag: str | None
    values: dict[str, Any]
    forced_values: dict[str, Any]

    @property
    def label(self) -> str:
        return f"{self.group} — {self.name}"


def _eval_scenario_node(node: ast.AST, settings_module: Any | None = None) -> Any:
    """Evaluate only the small literal subset used by scenarios/*.py."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        value = _eval_scenario_node(node.operand, settings_module)
        return -value
    if isinstance(node, ast.List):
        return [_eval_scenario_node(item, settings_module) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval_scenario_node(item, settings_module) for item in node.elts)
    if isinstance(node, ast.Dict):
        return {
            _eval_scenario_node(key, settings_module): _eval_scenario_node(value, settings_module)
            for key, value in zip(node.keys, node.values)
        }
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "settings":
        if settings_module is not None and hasattr(settings_module, node.attr):
            return getattr(settings_module, node.attr)
        return None
    raise ValueError(f"Unsupported scenario expression: {ast.dump(node)}")


def _read_scenario_constants(path: Path, settings_module: Any | None = None) -> dict[str, Any]:
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    constants: dict[str, Any] = {}
    wanted = {"TITRE", "DESCRIPTION", "ATTAQUE", "COMMUN", "VARIANTES"}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    constants[target.id] = _eval_scenario_node(node.value, settings_module)
                except Exception:
                    pass
    return constants


def _run_qkd_defaults() -> dict[str, Any]:
    """Read defaults from scenarios/manager_scenario.py without importing qutip/backend code."""
    backend_root = find_backend_root()
    main_defaults, advanced_defaults = load_frontend_defaults()
    fallback = {
        "attack": None,
        "message_size": main_defaults.get("message_size", 200),
        "message_interval": advanced_defaults.get("message_interval", 5.0),
        "average_emitted_photon": -1.0,
        "perfect_apd": True,
        "gate_off_duration": 0.0,
        "dead_time_min": 2.0,
        "dead_time_max": 6.0,
        "gate_on_duration": 20.0,
        "bit_loss": 0.0,
        "bit_flip": 0.0,
        "many_clicks_gestion": "THROWS",
        "perfect_apd_eve": advanced_defaults.get("perfect_apd_eve", True),
        "emission_click_event": advanced_defaults.get("emission_click_event", 10),
        "timing_attack": advanced_defaults.get("timing_attack", 300.0),
        "qber_percent": main_defaults.get("qber_percent", 20),
        "after_pulsing": advanced_defaults.get("after_pulsing", 0.0),
        "progress_bar": False,
    }
    if backend_root is None:
        return fallback

    settings_module = _load_settings_module()
    manager_scenario = backend_root / "scenarios" / "manager_scenario.py"
    if not manager_scenario.exists():
        return fallback

    try:
        module = ast.parse(manager_scenario.read_text(encoding="utf-8"))
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name == "run_qkd":
                defaults = dict(fallback)
                for arg, default_node in zip(node.args.kwonlyargs, node.args.kw_defaults):
                    if default_node is None:
                        continue
                    try:
                        value = _eval_scenario_node(default_node, settings_module)
                        if value is not None:
                            defaults[arg.arg] = value
                    except Exception:
                        pass
                return defaults
    except Exception:
        return fallback
    return fallback


def _clean_scenario_group(title: str, attack_flag: str | None) -> str:
    if attack_flag is None:
        return "No attack"
    if attack_flag in ATTACK_LABELS:
        return ATTACK_LABELS[attack_flag]
    title = title.replace("SCENARIO", "").replace("—", " ").strip(" -")
    return title or str(attack_flag)


def _format_for_preview(values: dict[str, Any], max_items: int = 5) -> str:
    priority = [
        "attack", "message_size", "message_interval", "average_emitted_photon",
        "bit_loss", "bit_flip", "perfect_apd", "gate_on_duration", "gate_off_duration",
        "dead_time_min", "dead_time_max", "many_clicks_gestion", "emission_click_event",
        "timing_attack", "after_pulsing",
    ]
    items: list[str] = []
    for key in priority:
        if key in values:
            val = values[key]
            if key == "attack":
                val = ATTACK_LABELS.get(val, "None" if val is None else str(val))
            items.append(f"{key}={val}")
    if not items:
        return "Backend defaults"
    if len(items) > max_items:
        return ", ".join(items[:max_items]) + "…"
    return ", ".join(items)


def load_scenario_presets() -> dict[str, list[ScenarioPreset]]:
    """Load every backend scenario variant as one UI preset.

    Reference variants embedded inside attack scenario files are intentionally skipped,
    because the UI already exposes one clean No attack section.
    """
    backend_root = find_backend_root()
    if backend_root is None:
        return {}
    scenarios_dir = backend_root / "scenarios"
    if not scenarios_dir.exists():
        return {}

    settings_module = _load_settings_module()
    run_defaults = _run_qkd_defaults()
    grouped: dict[str, list[ScenarioPreset]] = {}

    for path in sorted(scenarios_dir.glob("scenarios_*.py")):
        constants = _read_scenario_constants(path, settings_module)
        if not constants:
            continue
        title = str(constants.get("TITRE", path.stem))
        description = str(constants.get("DESCRIPTION", "")).strip()
        scenario_attack = constants.get("ATTAQUE")
        common = constants.get("COMMUN") or {}
        variants = constants.get("VARIANTES") or []
        if not isinstance(common, dict) or not isinstance(variants, list):
            continue

        group = _clean_scenario_group(title, scenario_attack)
        for variant in variants:
            if not (isinstance(variant, (tuple, list)) and len(variant) == 2 and isinstance(variant[1], dict)):
                continue
            name = str(variant[0])
            variant_params = dict(variant[1])
            effective_attack = variant_params.get("attack", common.get("attack", scenario_attack))

            # Avoid duplicate reference presets under every attack group.
            if effective_attack is None and group != "No attack":
                continue

            effective_values = dict(run_defaults)
            effective_values.update(common)
            effective_values.update(variant_params)
            effective_values.pop("attack", None)

            forced_values = dict(common)
            forced_values.update(variant_params)
            forced_values["attack"] = effective_attack

            preset = ScenarioPreset(
                group=group,
                name=name,
                description=description,
                attack_flag=effective_attack,
                values=effective_values,
                forced_values=forced_values,
            )
            grouped.setdefault(group, []).append(preset)

    # Stable display order matching the main attack dropdown.
    ordered: dict[str, list[ScenarioPreset]] = {}
    for group in ["No attack", "Intercept-resend", "PNS", "Trojan Horse", "Double Click Event", "Time Correlation"]:
        if group in grouped:
            ordered[group] = grouped[group]
    for group, presets in grouped.items():
        if group not in ordered:
            ordered[group] = presets
    return ordered


BACKEND_RUNNER = r'''
import contextlib
import io
import json
import os
import re
import sys
import traceback

MARK_START = "<<<QKD_JSON_START>>>"
MARK_END = "<<<QKD_JSON_END>>>"
ATTACK_FLAGS = ["INTERCEPT_AND_RESENT", "PNS", "TROJAN_HORSE", "DOUBLE_CLICK_EVENT", "TIME_CORRELATION"]
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

def similarity(a, b):
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    return sum(1 for i in range(n) if a[i] == b[i]) / n * 100.0

def strip_console(text):
    return ANSI_RE.sub("", text).replace("\r", "")

def emit(payload, code=0):
    sys.stdout.write("\n" + MARK_START + "\n")
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n" + MARK_END + "\n")
    sys.stdout.flush()
    os._exit(code)

def build_print_result_logs(result, scenario_name, config):
    # Reuse scenarios/print_results.py and mirror its detailed output in the GUI logs.
    try:
        try:
            from scenarios.print_results import print_result
        except Exception:
            # Allows running from the scenarios/ folder if the repository layout changes.
            from print_results import print_result

        forced_params = {
            "message_size": config.get("message_size"),
            "message_interval": config.get("advanced", {}).get("message_interval"),
            "average_emitted_photon": config.get("average_emitted_photon"),
            "bit_loss": config.get("quantum_canal_bit_loss"),
            "bit_flip": config.get("quantum_canal_bit_flip"),
            "qber_percent": config.get("qber_percent"),
            "qber_tolerance": config.get("qber_tolerance"),
            "many_clicks_gestion": config.get("advanced", {}).get("many_clicks_gestion"),
            "perfect_apd_bob": config.get("advanced", {}).get("perfect_apd_bob"),
            "perfect_apd_eve": config.get("advanced", {}).get("perfect_apd_eve"),
            "gate_off_duration": config.get("advanced", {}).get("gate_off_duration"),
            "gate_on_duration": config.get("advanced", {}).get("gate_on_duration"),
            "dead_time_min": config.get("advanced", {}).get("dead_time_min"),
            "dead_time_max": config.get("advanced", {}).get("dead_time_max"),
            "after_pulsing": config.get("advanced", {}).get("after_pulsing"),
            "emission_click_event": config.get("advanced", {}).get("emission_click_event"),
            "timing_attack": config.get("advanced", {}).get("timing_attack"),
        }
        forced_params = {key: value for key, value in forced_params.items() if value is not None}
        variant_name = scenario_name or "Manual parameter run"

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            print_result([result], [(variant_name, forced_params)])

        logs = [["details", "violet", "Detailed backend result from scenarios/print_results.py:"]]
        for raw_line in strip_console(buffer.getvalue()).splitlines():
            line = raw_line.rstrip()
            if line.strip():
                logs.append(["details", "muted", line[:900]])
        return logs
    except Exception as exc:
        return [["details", "warn", f"Could not render scenarios/print_results.py details: {exc}"]]

try:
    config = json.loads(sys.stdin.read())
    sys.path.insert(0, os.getcwd())

    import settings

    message_interval = float(config["advanced"].get("message_interval", 5))
    receiver_timeout = float(config["advanced"].get("tolerance_message_not_receive", message_interval - 0.1))
    if receiver_timeout >= message_interval:
        receiver_timeout = max(0.0, message_interval - 0.2)

    settings.message_size = int(config.get("message_size", 200))
    settings.message_interval = message_interval
    settings.tolerance_message_not_receive = receiver_timeout
    settings.protocol = str(config.get("protocol", "bb84")).lower()
    settings.average_emitted_photon = float(config.get("average_emitted_photon", -1.0))
    settings.quantum_canal_bit_loss = float(config.get("quantum_canal_bit_loss", 0.0))
    settings.quantum_canal_bit_flip = float(config.get("quantum_canal_bit_flip", 2.0))
    settings.qber_percent = int(config.get("qber_percent", 20))
    settings.qber_tolerance = int(config.get("qber_tolerance", 11))

    settings.perfect_apd_bob = bool(config["advanced"].get("perfect_apd_bob", True))
    settings.perfect_apd_eve = bool(config["advanced"].get("perfect_apd_eve", True))
    settings.breakdown_voltage = float(config["advanced"].get("breakdown_voltage", 7))
    settings.dead_time_min = float(config["advanced"].get("dead_time_min", 2))
    settings.dead_time_max = float(config["advanced"].get("dead_time_max", 6))
    settings.bias_voltage = float(config["advanced"].get("bias_voltage", 5))
    settings.gate_off_duration = float(config["advanced"].get("gate_off_duration", message_interval / 2))
    settings.gate_on_duration = float(config["advanced"].get("gate_on_duration", message_interval / 2))
    settings.many_clicks_gestion = str(config["advanced"].get("many_clicks_gestion", "NONE"))
    settings.after_pulsing = float(config["advanced"].get("after_pulsing", 0))
    settings.emission_click_event = int(config["advanced"].get("emission_click_event", 10))
    settings.timing_attack = float(config["advanced"].get("timing_attack", 300))
    # Relié au backend : contrôle réellement la progress bar console du simulateur.
    # stdout est capturé par le front, donc cela ne casse pas l'interface.
    settings.progress_bar = bool(config["advanced"].get("progress_bar", True))

    attack_flag = config.get("attack_flag")
    for flag in ATTACK_FLAGS:
        setattr(settings, flag, flag == attack_flag)

    import manager

    result = manager.run_communication()

    eve_knowledge = 0.0
    if result.eve is not None and result.key_eve is not None:
        if attack_flag == "TIME_CORRELATION" and isinstance(result.key_eve, list):
            scores = []
            for candidate in result.key_eve:
                if isinstance(candidate, list):
                    scores.append(similarity(result.final_key, candidate))
            eve_knowledge = max(scores) if scores else 0.0
        else:
            eve_knowledge = similarity(result.final_key, result.key_eve)

    sifted_bits = len(result.key_alice) / max(1, int(settings.message_size)) * 100.0
    key_agreement = similarity(result.key_alice, result.key_bob)
    status = "Accepted" if float(result.qber) < float(settings.qber_tolerance) else "Aborted"
    detected = "Yes" if float(result.qber) >= float(settings.qber_tolerance) else "No"

    scenario_name = config.get("scenario_name")
    detailed_logs = build_print_result_logs(result, scenario_name, config)

    payload = {
        "ok": True,
        "qber": round(float(result.qber), 2),
        "final_key_size": len(result.final_key),
        "eve_knowledge": round(float(eve_knowledge), 2),
        "key_agreement": round(float(key_agreement), 2),
        "communication_status": status,
        "attack_detected": detected,
        "sifted_bits": round(float(sifted_bits), 2),
        "discarded_bits": round(100.0 - float(sifted_bits), 2),
        "lost": float(settings.quantum_canal_bit_loss),
        "flipped": float(settings.quantum_canal_bit_flip),
        "mode": "Backend",
        "logs": [
            ["backend", "violet", "Backend simulation completed through manager.run_communication()."],
            ["scenario", "teal", f"Scenario preset: {scenario_name}."] if scenario_name else ["scenario", "muted", "Manual parameter run."],
            ["backend", "violet", f"Config applied: {int(settings.message_size)} qubits, attack={attack_flag or 'None'}."],
            ["backend", "violet", "Sifting and QBER estimation returned by backend modules."],
            ["backend", "teal" if status == "Accepted" else "warn", f"Communication {status.lower()} with QBER={float(result.qber):.2f}%."]
        ] + detailed_logs
    }
    emit(payload, 0)
except Exception as exc:
    emit({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}, 1)
'''


class BackendWorker(QThread):
    finished = Signal(object)

    def __init__(self, config: SimulationConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.config = config
        self._process: subprocess.Popen[str] | None = None
        self._stop_requested = False

    def stop_process(self):
        """Ask the backend subprocess to stop, then force-kill only if it refuses."""
        self._stop_requested = True
        proc = self._process
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def run(self):
        backend_root = find_backend_root()
        if backend_root is None:
            self.finished.emit(
                backend_error_result(
                    self.config,
                    "Backend files not found near the frontend folder.",
                    backend_search_report(),
                )
            )
            return

        payload = {
            "message_size": self.config.message_size,
            "protocol": self.config.protocol,
            "average_emitted_photon": self.config.average_emitted_photon,
            "quantum_canal_bit_loss": self.config.quantum_canal_bit_loss,
            "quantum_canal_bit_flip": self.config.quantum_canal_bit_flip,
            "qber_percent": self.config.qber_percent,
            "qber_tolerance": self.config.qber_tolerance,
            "attack_flag": self.config.attack_flag,
            "advanced": self.config.advanced,
            "scenario_name": self.config.scenario_name,
        }

        try:
            self._process = subprocess.Popen(
                [sys.executable, "-c", BACKEND_RUNNER],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(backend_root),
            )
            if self._stop_requested and self._process.poll() is None:
                self._process.terminate()
            stdout, stderr = self._process.communicate(json.dumps(payload))

            if self._stop_requested:
                self.finished.emit(backend_cancelled_result(self.config))
                return

            stdout = stdout or ""
            stderr = stderr or ""
            start = stdout.rfind("<<<QKD_JSON_START>>>")
            end = stdout.rfind("<<<QKD_JSON_END>>>")
            if start == -1 or end == -1 or end <= start:
                reason = "Backend did not return a readable JSON result."
                detail = stderr + "\n" + (stdout[-1800:] if stdout else "")
                self.finished.emit(backend_error_result(self.config, reason, detail))
                return

            json_text = stdout[start + len("<<<QKD_JSON_START>>>"):end].strip()
            data = json.loads(json_text)
            if not data.get("ok", False):
                reason = f"Backend error: {data.get('error', 'unknown error')}"
                self.finished.emit(backend_error_result(self.config, reason, data.get("traceback", "")))
                return

            logs = [tuple(item) for item in data.get("logs", [])]
            debug_lines: list[tuple[str, str, str]] = []
            stdout_before_json = stdout[:start].strip()
            for line in stdout_before_json.splitlines()[-18:]:
                line = line.strip()
                if line:
                    debug_lines.append(("stdout", "muted", line[:220]))
            for line in stderr.strip().splitlines()[-10:]:
                line = line.strip()
                if line:
                    debug_lines.append(("stderr", "warn", line[:220]))
            if debug_lines:
                logs.append(("debug", "violet", "Backend console output captured for debugging."))
                logs.extend(debug_lines)

            self.finished.emit(
                SimulationResult(
                    qber=float(data["qber"]),
                    final_key_size=int(data["final_key_size"]),
                    eve_knowledge=float(data["eve_knowledge"]),
                    key_agreement=float(data["key_agreement"]),
                    communication_status=str(data["communication_status"]),
                    attack_detected=str(data["attack_detected"]),
                    sifted_bits=float(data["sifted_bits"]),
                    discarded_bits=float(data["discarded_bits"]),
                    lost=float(data["lost"]),
                    flipped=float(data["flipped"]),
                    mode=str(data.get("mode", "Backend")),
                    logs=logs,
                )
            )
        except Exception as exc:
            if self._stop_requested:
                self.finished.emit(backend_cancelled_result(self.config))
            else:
                self.finished.emit(backend_error_result(self.config, f"Backend launch error: {exc}"))


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QFrame.NoFrame)


class SectionTitle(QWidget):
    def __init__(self, icon: str, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setObjectName("SectionIcon")
        icon_label.setFixedWidth(22)
        title_label = QLabel(title)
        title_label.setObjectName("SectionTitle")

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()


class EditableValueBox(QLineEdit):
    """Small numeric value box used next to sliders.

    It behaves like a label by default, then becomes editable on double-click.
    Press Enter or click outside to validate and synchronize the slider.
    """

    def __init__(self, text: str, width: int, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("ValueBox")
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(width, 30)
        self._last_committed_text = text
        self.setToolTip("Double-click to type a value, then press Enter.")

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        self._last_committed_text = self.text()
        self.setReadOnly(False)
        self.setFocus(Qt.MouseFocusReason)
        self.selectAll()
        event.accept()

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clearFocus()
            return
        if event.key() == Qt.Key_Escape:
            self.setText(self._last_committed_text)
            self.setReadOnly(True)
            self.clearFocus()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):  # noqa: N802
        self.setReadOnly(True)
        super().focusOutEvent(event)


class LabeledSlider(QWidget):
    def __init__(self, label: str, value: int, minimum: int = 0, maximum: int = 100, suffix: str = "%"):
        super().__init__()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(value)
        self.value_label = EditableValueBox(str(value), 54)
        self.value_label.setValidator(QIntValidator(minimum, maximum, self.value_label))
        self.suffix = QLabel(suffix)
        self.suffix.setObjectName("MutedText")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        name = QLabel(label)
        name.setObjectName("FieldLabel")
        top.addWidget(name)
        top.addStretch()

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(10)
        bottom.addWidget(self.slider, 1)
        bottom.addWidget(self.value_label)
        bottom.addWidget(self.suffix)

        root.addLayout(top)
        root.addLayout(bottom)
        self.slider.valueChanged.connect(self._update_label_from_slider)
        self.value_label.editingFinished.connect(self._commit_label_to_slider)

    def _update_label_from_slider(self, value: int):
        # Do not overwrite text while the user is typing manually.
        if self.value_label.isReadOnly():
            self.value_label.setText(str(value))

    def _commit_label_to_slider(self):
        raw = self.value_label.text().strip().replace(",", ".")
        try:
            value = int(round(float(raw)))
        except ValueError:
            value = self.slider.value()
        value = max(self.slider.minimum(), min(self.slider.maximum(), value))
        self.value_label.setReadOnly(True)
        self.slider.setValue(value)
        self.value_label.setText(str(value))

    def value(self) -> int:
        return self.slider.value()

    def setValue(self, value: int):
        self.slider.setValue(value)
        self.value_label.setText(str(self.slider.value()))


class LabeledFloatSlider(QWidget):
    def __init__(self, label: str, value: float, minimum: float = 0.0, maximum: float = 100.0, decimals: int = 2, suffix: str = "%"):
        super().__init__()
        self.scale = 10 ** decimals
        self.decimals = decimals
        self.minimum = minimum
        self.maximum = maximum
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(int(minimum * self.scale), int(maximum * self.scale))
        self.slider.setValue(int(round(value * self.scale)))
        self.value_label = EditableValueBox(f"{value:.{decimals}f}", 68)
        self.suffix = QLabel(suffix)
        self.suffix.setObjectName("MutedText")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        name = QLabel(label)
        name.setObjectName("FieldLabel")
        top.addWidget(name)
        top.addStretch()

        bottom = QHBoxLayout()
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(10)
        bottom.addWidget(self.slider, 1)
        bottom.addWidget(self.value_label)
        bottom.addWidget(self.suffix)

        root.addLayout(top)
        root.addLayout(bottom)
        self.slider.valueChanged.connect(self._update_label_from_slider)
        self.value_label.editingFinished.connect(self._commit_label_to_slider)

    def _update_label_from_slider(self, raw: int):
        if self.value_label.isReadOnly():
            self.value_label.setText(f"{raw / self.scale:.{self.decimals}f}")

    def _commit_label_to_slider(self):
        raw = self.value_label.text().strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            value = self.value()
        value = max(self.minimum, min(self.maximum, value))
        self.value_label.setReadOnly(True)
        self.slider.setValue(int(round(value * self.scale)))
        self.value_label.setText(f"{self.value():.{self.decimals}f}")

    def value(self) -> float:
        return self.slider.value() / self.scale

    def setValue(self, value: float):
        value = max(self.minimum, min(self.maximum, value))
        self.slider.setValue(int(round(value * self.scale)))
        self.value_label.setText(f"{self.value():.{self.decimals}f}")


class Field(QWidget):
    def __init__(self, label: str, widget: QWidget, hint: str | None = None, detail: str | None = None):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(5)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        name = QLabel(label)
        name.setObjectName("FieldLabel")
        top.addWidget(name)
        if hint:
            info = QLabel("ⓘ")
            info.setObjectName("InfoIcon")
            info.setToolTip(hint)
            top.addWidget(info)
        top.addStretch()
        root.addLayout(top)
        root.addWidget(widget)
        if detail:
            help_label = QLabel(detail)
            help_label.setObjectName("FieldDetail")
            help_label.setWordWrap(True)
            root.addWidget(help_label)


class AdvancedSettingsDialog(QDialog):
    def __init__(self, settings: dict[str, Any], parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AdvancedDialog")
        self.setWindowTitle("Advanced settings")
        self.setModal(True)
        self.resize(560, 680)
        self.setMinimumSize(520, 600)
        self.settings = dict(settings)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("Advanced settings")
        title.setObjectName("AdvancedTitle")
        subtitle = QLabel("Technical parameters matching the current backend settings.py.")
        subtitle.setObjectName("AdvancedSubtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setObjectName("AdvancedScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("AdvancedContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        self.message_interval = self._number_edit(self.settings.get("message_interval", 5))
        self.receiver_timeout = self._number_edit(self.settings.get("tolerance_message_not_receive", 4.9))
        self.progress_bar = QCheckBox("Console progress bar")
        self.progress_bar.setObjectName("AdvancedCheck")
        self.progress_bar.setChecked(bool(self.settings.get("progress_bar", True)))

        general_box, general_layout = self._section("General / timing")
        general_layout.addWidget(Field("Message interval (ms)", self.message_interval))
        general_layout.addWidget(Field("Receiver timeout (ms)", self.receiver_timeout, "Must stay lower than message interval."))
        general_layout.addWidget(self.progress_bar)
        content_layout.addWidget(general_box)

        self.perfect_apd_bob = QCheckBox("Perfect APD for Bob")
        self.perfect_apd_bob.setObjectName("AdvancedCheck")
        self.perfect_apd_bob.setChecked(bool(self.settings.get("perfect_apd_bob", True)))
        self.perfect_apd_eve = QCheckBox("Perfect APD for Eve")
        self.perfect_apd_eve.setObjectName("AdvancedCheck")
        self.perfect_apd_eve.setChecked(bool(self.settings.get("perfect_apd_eve", True)))

        self.breakdown_voltage = self._number_edit(self.settings.get("breakdown_voltage", 7))
        self.dead_time_min = self._number_edit(self.settings.get("dead_time_min", 2))
        self.dead_time_max = self._number_edit(self.settings.get("dead_time_max", 6))
        self.bias_voltage = self._number_edit(self.settings.get("bias_voltage", 5))
        message_interval_default = self._safe_float(str(self.settings.get("message_interval", 5.0)), 5.0)
        self.gate_off_duration = self._number_edit(self.settings.get("gate_off_duration", message_interval_default / 2))
        self.gate_on_duration = self._number_edit(self.settings.get("gate_on_duration", message_interval_default / 2))

        apd_box, apd_layout = self._section("APD settings")
        apd_layout.addWidget(self.perfect_apd_bob)
        apd_layout.addWidget(self.perfect_apd_eve)
        apd_layout.addWidget(Field("Breakdown voltage", self.breakdown_voltage))
        apd_layout.addWidget(Field("Dead time min (ms)", self.dead_time_min))
        apd_layout.addWidget(Field("Dead time max (ms)", self.dead_time_max))
        apd_layout.addWidget(Field("Bias voltage", self.bias_voltage))
        apd_layout.addWidget(Field("Gate off duration (ms)", self.gate_off_duration, detail="Should be equal to message interval / 2."))
        apd_layout.addWidget(Field("Gate on duration (ms)", self.gate_on_duration, detail="Should be equal to message interval / 2."))
        content_layout.addWidget(apd_box)

        self.many_clicks = QComboBox()
        self.many_clicks.setObjectName("Input")
        self.many_clicks.addItems(["NONE", "RANDOM", "THROWS"])
        self.many_clicks.setCurrentText(str(self.settings.get("many_clicks_gestion", "NONE")))
        self.after_pulsing = self._number_edit(self.settings.get("after_pulsing", 0))
        self.emission_click_event = self._int_edit(self.settings.get("emission_click_event", 10))
        self.timing_attack = self._number_edit(self.settings.get("timing_attack", 300))

        attacks_box, attacks_layout = self._section("Attack-specific settings")
        attacks_layout.addWidget(Field("Double click handling", self.many_clicks))
        attacks_layout.addWidget(Field("After pulsing probability (%)", self.after_pulsing))
        attacks_layout.addWidget(Field("Photons sent in double click attack", self.emission_click_event))
        attacks_layout.addWidget(Field("Time correlation max time (s)", self.timing_attack))
        content_layout.addWidget(attacks_box)
        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("CancelButton")
        cancel.setFixedHeight(38)
        cancel.clicked.connect(self.reject)
        apply = QPushButton("Apply")
        apply.setObjectName("ApplyButton")
        apply.setFixedHeight(38)
        apply.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(apply)
        root.addLayout(buttons)

    def _number_edit(self, value: Any) -> QLineEdit:
        field = QLineEdit(str(value))
        field.setObjectName("Input")
        validator = QDoubleValidator(0.0, 1000000.0, 4, field)
        validator.setNotation(QDoubleValidator.StandardNotation)
        field.setValidator(validator)
        return field

    def _int_edit(self, value: Any) -> QLineEdit:
        field = QLineEdit(str(value))
        field.setObjectName("Input")
        field.setValidator(QIntValidator(0, 1000000, field))
        return field

    def _section(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        box = QFrame()
        box.setObjectName("AdvancedCard")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        section_title = QLabel(title)
        section_title.setObjectName("AdvancedSectionTitle")
        layout.addWidget(section_title)
        return box, layout

    def values(self) -> dict[str, Any]:
        message_interval = self._safe_float(self.message_interval.text(), 5.0)
        receiver_timeout = self._safe_float(self.receiver_timeout.text(), message_interval - 0.2)
        if receiver_timeout >= message_interval:
            receiver_timeout = max(0.0, message_interval - 0.2)
        return {
            "message_interval": message_interval,
            "tolerance_message_not_receive": receiver_timeout,
            "progress_bar": self.progress_bar.isChecked(),
            "perfect_apd_bob": self.perfect_apd_bob.isChecked(),
            "perfect_apd_eve": self.perfect_apd_eve.isChecked(),
            "breakdown_voltage": self._safe_float(self.breakdown_voltage.text(), 7.0),
            "dead_time_min": self._safe_float(self.dead_time_min.text(), 20.0),
            "dead_time_max": self._safe_float(self.dead_time_max.text(), 60.0),
            "bias_voltage": self._safe_float(self.bias_voltage.text(), 5.0),
            "gate_off_duration": self._safe_float(self.gate_off_duration.text(), message_interval / 2),
            "gate_on_duration": self._safe_float(self.gate_on_duration.text(), message_interval / 2),
            "many_clicks_gestion": self.many_clicks.currentText(),
            "after_pulsing": self._safe_float(self.after_pulsing.text(), 0.0),
            "emission_click_event": self._safe_int(self.emission_click_event.text(), 10),
            "timing_attack": self._safe_float(self.timing_attack.text(), 300.0),
        }

    @staticmethod
    def _safe_float(value: str, default: float) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return default

    @staticmethod
    def _safe_int(value: str, default: int) -> int:
        try:
            return int(value)
        except ValueError:
            return default


class ScenarioPresetsDialog(QDialog):
    """Window listing one-click backend scenario presets."""

    def __init__(self, presets: dict[str, list[ScenarioPreset]], parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AdvancedDialog")
        self.setWindowTitle("Scenario presets")
        self.setModal(True)
        self.resize(690, 700)
        self.setMinimumSize(620, 580)
        self.selected_preset: ScenarioPreset | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("Scenario presets")
        title.setObjectName("AdvancedTitle")
        subtitle = QLabel("Choose one preset: it fills the interface fields, then launches exactly one simulation.")
        subtitle.setObjectName("AdvancedSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setObjectName("AdvancedScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("AdvancedContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        if not presets:
            empty = QLabel("No scenario preset found. The frontend expects a backend scenarios/ folder next to manager.py.")
            empty.setObjectName("AdvancedSubtitle")
            empty.setWordWrap(True)
            content_layout.addWidget(empty)
        else:
            for group, group_presets in presets.items():
                box = QFrame()
                box.setObjectName("AdvancedCard")
                box_layout = QVBoxLayout(box)
                box_layout.setContentsMargins(16, 14, 16, 16)
                box_layout.setSpacing(9)

                section_title = QLabel(group)
                section_title.setObjectName("AdvancedSectionTitle")
                box_layout.addWidget(section_title)

                for preset in group_presets:
                    button = QPushButton()
                    button.setObjectName("PresetButton")
                    button.setFixedHeight(68)
                    button.setText(f"{preset.name}\n{_format_for_preview(preset.forced_values)}")
                    button.setToolTip(preset.description[:800] if preset.description else preset.label)
                    button.clicked.connect(lambda checked=False, p=preset: self._select(p))
                    box_layout.addWidget(button)
                content_layout.addWidget(box)
        content_layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_button = QPushButton("Cancel")
        close_button.setObjectName("CancelButton")
        close_button.setFixedHeight(38)
        close_button.clicked.connect(self.reject)
        buttons.addWidget(close_button)
        root.addLayout(buttons)

    def _select(self, preset: ScenarioPreset):
        self.selected_preset = preset
        self.accept()


class DiagramWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.bit_loss = 2.0
        self.bit_flip = 2.0
        self.attack = "Trojan Horse"
        self.animation_phase = 0.0
        self.animation_steps = 0
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(35)
        self.animation_timer.timeout.connect(self._advance_animation)
        self.setMinimumHeight(360)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_values(self, bit_loss: float, bit_flip: float, attack: str | None = None):
        self.bit_loss = bit_loss
        self.bit_flip = bit_flip
        if attack is not None:
            self.attack = attack
        self.update()

    def start_animation(self):
        self.animation_phase = 0.0
        # Keep bubbles visible for the whole backend process, not just a short preview.
        self.animation_steps = 1
        if not self.animation_timer.isActive():
            self.animation_timer.start()

    def stop_animation(self):
        self.animation_timer.stop()
        self.animation_phase = 0.0
        self.animation_steps = 0
        self.update()

    def _advance_animation(self):
        self.animation_phase = (self.animation_phase + 0.035) % 1.0
        self.animation_steps += 1
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), QColor(PANEL))

        w = max(self.width(), 700)
        h = max(self.height(), 360)

        side_card_w = min(195, max(168, w * 0.19))
        side_card_h = min(322, h - 40)
        side_margin = 30
        channel_w = min(272, max(236, w * 0.30))
        channel_h = 156
        eve_w = min(365, max(330, w * 0.40))
        eve_h = 158
        eve_y = min(318, h - eve_h - 8)

        alice = QRectF(side_margin, 18, side_card_w, side_card_h)
        bob = QRectF(w - side_margin - side_card_w, 18, side_card_w, side_card_h)
        channel = QRectF(w / 2 - channel_w / 2, 76, channel_w, channel_h)
        eve = QRectF(w / 2 - eve_w / 2, eve_y, eve_w, eve_h)

        self._rounded_rect(painter, alice, "#111A27", "#344258")
        self._rounded_rect(painter, bob, "#111A27", "#344258")
        self._rounded_rect(painter, channel, "#141629", ACCENT_SOFT)

        if self.attack != "None":
            self._rounded_rect(painter, eve, EVE_CARD, EVE_BORDER)

        self._node(painter, alice.center().x(), 92, "A", ACCENT, "Alice")
        self._list_item(painter, alice.left() + 42, 220, "Random bases")
        self._list_item(painter, alice.left() + 42, 266, "Qubits")
        self._list_item(painter, alice.left() + 42, 310, "Sifting")

        self._node(painter, bob.center().x(), 92, "B", TEAL, "Bob")
        self._list_item(painter, bob.left() + 42, 220, "Measurement")
        self._list_item(painter, bob.left() + 42, 266, "Sifting")
        self._list_item(painter, bob.left() + 42, 310, "QBER")

        self._channel(painter, channel)
        self._arrows(painter, alice, channel, bob)

        if self.attack == "None":
            self._no_attack_note(painter, channel)
        else:
            self._eve(painter, eve)
            self._eve_links(painter, alice, channel, bob, eve)

    def _rounded_rect(self, p: QPainter, rect: QRectF, fill: str, border: str, radius: int = 14):
        p.setPen(QPen(QColor(border), 1.2))
        p.setBrush(QBrush(QColor(fill)))
        p.drawRoundedRect(rect, radius, radius)

    def _font(self, size: int, weight: int = QFont.Normal) -> QFont:
        f = QFont(FONT, size)
        f.setWeight(weight)
        return f

    def _node(self, p: QPainter, x: float, y: float, letter: str, accent: str, name: str):
        p.setPen(QPen(QColor("#354258"), 1.2))
        p.setBrush(QColor("#151F2D"))
        p.drawEllipse(QPointF(x, y), 39, 39)
        p.setPen(QPen(QColor(accent), 2.0))
        p.setBrush(QColor("#101722"))
        p.drawEllipse(QPointF(x, y), 30, 30)
        p.setPen(QColor(TEXT))
        p.setFont(self._font(19, QFont.Bold))
        p.drawText(QRectF(x - 26, y - 19, 52, 38), Qt.AlignCenter, letter)
        p.setPen(QColor(accent))
        p.setFont(self._font(18, QFont.Bold))
        p.drawText(QRectF(x - 75, y + 66, 150, 32), Qt.AlignCenter, name)

    def _list_item(self, p: QPainter, x: float, y: float, text: str, accent: str = MUTED_2):
        p.setPen(QPen(QColor(accent), 1.4))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(x + 4, y), 4, 4)
        p.setPen(QColor(TEXT))
        p.setFont(self._font(11))
        p.drawText(QRectF(x + 24, y - 16, 138, 30), Qt.AlignVCenter | Qt.AlignLeft, text)

    def _channel(self, p: QPainter, rect: QRectF):
        p.setPen(QColor(ACCENT))
        p.setFont(self._font(14, QFont.Bold))
        p.drawText(QRectF(rect.left(), rect.top() + 16, rect.width(), 28), Qt.AlignCenter, "Quantum Channel")

        path = QPainterPath()
        start_x = rect.center().x() - 94
        base_y = rect.top() + 82
        path.moveTo(start_x, base_y)
        for i in range(1, 188):
            x = start_x + i
            y = base_y + 22 * math.sin(i / 14)
            path.lineTo(x, y)
        p.setPen(QPen(QColor(ACCENT), 2.4))
        p.drawPath(path)

        for i in range(0, 188, 20):
            x = start_x + i
            y = base_y + 22 * math.sin(i / 14)
            p.setBrush(QColor(ACCENT))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, y), 2.3, 2.3)

        p.setPen(QColor(TEXT))
        p.setFont(self._font(10))
        p.drawText(QRectF(rect.left(), rect.bottom() - 32, rect.width(), 22), Qt.AlignCenter, f"Loss: {self.bit_loss:.2f}%    |    Flip: {self.bit_flip:.2f}%")

    def _arrows(self, p: QPainter, alice: QRectF, channel: QRectF, bob: QRectF):
        left_start = QPointF(alice.right() + 20, 160)
        left_end = QPointF(channel.left() - 12, 160)
        right_start = QPointF(channel.right() + 12, 160)
        right_end = QPointF(bob.left() - 20, 160)

        self._arrow(p, left_start, left_end, ACCENT)
        self._arrow(p, right_start, right_end, ACCENT)

        p.setPen(QPen(QColor(ACCENT), 1.8))
        p.setBrush(Qt.NoBrush)
        for i in range(4):
            p.drawEllipse(QPointF(alice.right() + 22 + i * 22, 194), 3.2, 3.2)
            p.drawEllipse(QPointF(channel.right() + 24 + i * 22, 194), 3.2, 3.2)

        self._moving_dots(p, left_start, left_end, ACCENT, y_offset=-13)
        self._moving_dots(p, right_start, right_end, ACCENT, y_offset=-13)

        p.setPen(QColor(MUTED))
        p.setFont(self._font(13))
        p.drawText(QPointF(alice.right() + 108, 199), "...")
        p.drawText(QPointF(channel.right() + 118, 199), "...")

    def _arrow(self, p: QPainter, start: QPointF, end: QPointF, color: str, dashed: bool = False):
        pen = QPen(QColor(color), 2.8)
        if dashed:
            pen.setDashPattern([5, 5])
        p.setPen(pen)
        p.drawLine(start, end)
        self._arrow_head(p, start, end, color, 10)

    def _polyline_arrow(self, p: QPainter, points: list[QPointF], color: str, dashed: bool = False):
        if len(points) < 2:
            return
        pen = QPen(QColor(color), 2.0)
        if dashed:
            pen.setDashPattern([6, 6])
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        for start, end in zip(points, points[1:]):
            p.drawLine(start, end)
        self._arrow_head(p, points[-2], points[-1], color, 9)

    def _arrow_head(self, p: QPainter, start: QPointF, end: QPointF, color: str, arrow_size: float):
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        p1 = QPointF(end.x() - arrow_size * math.cos(angle - math.pi / 6), end.y() - arrow_size * math.sin(angle - math.pi / 6))
        p2 = QPointF(end.x() - arrow_size * math.cos(angle + math.pi / 6), end.y() - arrow_size * math.sin(angle + math.pi / 6))
        path = QPainterPath(end)
        path.lineTo(p1)
        path.lineTo(p2)
        path.closeSubpath()
        p.setBrush(QColor(color))
        p.setPen(Qt.NoPen)
        p.drawPath(path)

    def _moving_dots(self, p: QPainter, start: QPointF, end: QPointF, color: str, y_offset: float = 0.0):
        if not self.animation_timer.isActive() or self.animation_steps == 0:
            return
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        p.setPen(Qt.NoPen)
        for i in range(3):
            t = (self.animation_phase + i * 0.22) % 1.0
            dot_color = QColor(color)
            dot_color.setAlpha(160 - i * 28)
            p.setBrush(dot_color)
            p.drawEllipse(QPointF(start.x() + dx * t, start.y() + dy * t + y_offset), 4.2, 4.2)

    def _moving_dots_polyline(self, p: QPainter, points: list[QPointF], color: str):
        if not self.animation_timer.isActive() or self.animation_steps == 0 or len(points) < 2:
            return
        segments: list[tuple[QPointF, QPointF, float]] = []
        total = 0.0
        for start, end in zip(points, points[1:]):
            length = math.hypot(end.x() - start.x(), end.y() - start.y())
            segments.append((start, end, length))
            total += length
        if total <= 0:
            return
        p.setPen(Qt.NoPen)
        for i in range(3):
            distance = ((self.animation_phase + i * 0.23) % 1.0) * total
            for start, end, length in segments:
                if distance <= length:
                    t = 0.0 if length == 0 else distance / length
                    dot_color = QColor(color)
                    dot_color.setAlpha(145 - i * 25)
                    p.setBrush(dot_color)
                    p.drawEllipse(QPointF(start.x() + (end.x() - start.x()) * t, start.y() + (end.y() - start.y()) * t), 4.0, 4.0)
                    break
                distance -= length

    def _eve(self, p: QPainter, rect: QRectF):
        x = rect.left() + 92
        y = rect.top() + 50
        p.setPen(QPen(QColor(EVE_BORDER), 1.2))
        p.setBrush(QColor("#21151D"))
        p.drawEllipse(QPointF(x, y), 35, 35)
        p.setPen(QPen(QColor(EVE_ACCENT), 2.0))
        p.setBrush(QColor("#120D14"))
        p.drawEllipse(QPointF(x, y), 27, 27)
        p.setPen(QColor(TEXT))
        p.setFont(self._font(18, QFont.Bold))
        p.drawText(QRectF(x - 24, y - 18, 48, 36), Qt.AlignCenter, "E")

        attack_title, actions = self._attack_description()
        p.setPen(QColor(EVE_ACCENT))
        p.setFont(self._font(15, QFont.Bold))
        p.drawText(QRectF(x - 55, y + 42, 110, 24), Qt.AlignCenter, "Eve")
        p.setPen(QColor(MUTED))
        p.setFont(self._font(10))
        p.drawText(QRectF(x - 78, y + 66, 156, 22), Qt.AlignCenter, attack_title)

        action_x = rect.left() + 178
        for idx, action in enumerate(actions):
            self._action_item(p, action_x, rect.top() + 36 + idx * 34, action)

    def _attack_description(self) -> tuple[str, list[str]]:
        if self.attack == "Intercept-resend":
            return "Measure + resend", ["Measure qubit", "Pick new basis", "Raises QBER"]
        if self.attack == "PNS":
            return "Photon splitting", ["Keep photon", "Forward copy", "Low disturbance"]
        if self.attack == "Trojan Horse":
            return "Source probe", ["Probe Alice", "Read reflection", "Infer basis"]
        if self.attack == "Double Click Event":
            return "Detector attack", ["Resend pulses", "Trigger APDs", "Exploit policy"]
        if self.attack == "Time Correlation":
            return "Timing side-channel", ["Observe times", "Infer dead time", "Build candidates"]
        return "No attacker", ["Direct exchange", "Public sifting", "QBER check"]

    def _action_item(self, p: QPainter, x: float, y: float, text: str):
        p.setPen(QPen(QColor(EVE_ACCENT), 1.4))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(x, y + 10), 3.8, 3.8)
        p.setPen(QColor(TEXT))
        p.setFont(self._font(10))
        p.drawText(QRectF(x + 16, y, 140, 22), Qt.AlignVCenter | Qt.AlignLeft, text)

    def _eve_links(self, p: QPainter, alice: QRectF, channel: QRectF, bob: QRectF, eve: QRectF):
        if self.attack == "Intercept-resend":
            down = [QPointF(channel.center().x() - 55, channel.bottom() + 8), QPointF(eve.center().x() - 55, eve.top() - 8)]
            up = [QPointF(eve.center().x() + 55, eve.top() - 8), QPointF(channel.center().x() + 55, channel.bottom() + 8)]
            self._arrow(p, down[0], down[1], EVE_ACCENT, dashed=True)
            self._arrow(p, up[0], up[1], EVE_ACCENT, dashed=True)
            self._moving_dots(p, down[0], down[1], EVE_ACCENT)
            self._moving_dots(p, up[0], up[1], EVE_ACCENT)
        elif self.attack == "PNS":
            tap = [QPointF(channel.center().x(), channel.bottom() + 8), QPointF(eve.center().x(), eve.top() - 8)]
            self._arrow(p, tap[0], tap[1], EVE_ACCENT, dashed=True)
            self._moving_dots(p, tap[0], tap[1], EVE_ACCENT)
        elif self.attack == "Trojan Horse":
            # Le backend actuel lit la base d'Alice via alice.chosen_bases : on représente donc une sonde côté source.
            probe_y = eve.center().y() - 18
            reflection_y = eve.center().y() + 18
            alice_probe_x = alice.left() + alice.width() * 0.62
            alice_return_x = alice.left() + alice.width() * 0.38
            probe_path = [QPointF(eve.left(), probe_y), QPointF(alice_probe_x, probe_y), QPointF(alice_probe_x, alice.bottom() + 8)]
            reflection_path = [QPointF(alice_return_x, alice.bottom() + 8), QPointF(alice_return_x, reflection_y), QPointF(eve.left(), reflection_y)]
            self._polyline_arrow(p, probe_path, EVE_ACCENT, dashed=True)
            self._polyline_arrow(p, reflection_path, EVE_ACCENT, dashed=True)
            self._moving_dots_polyline(p, probe_path, EVE_ACCENT)
            self._moving_dots_polyline(p, reflection_path, EVE_ACCENT)
        elif self.attack == "Double Click Event":
            y1 = eve.center().y() - 16
            y2 = eve.center().y() + 16
            paths = [
                [QPointF(eve.right(), y1), QPointF(bob.center().x() - 28, y1), QPointF(bob.center().x() - 28, bob.bottom() + 8)],
                [QPointF(eve.right(), y2), QPointF(bob.center().x() + 28, y2), QPointF(bob.center().x() + 28, bob.bottom() + 8)],
            ]
            for path in paths:
                self._polyline_arrow(p, path, EVE_ACCENT, dashed=True)
                self._moving_dots_polyline(p, path, EVE_ACCENT)
        elif self.attack == "Time Correlation":
            path = [QPointF(bob.center().x(), bob.bottom() + 8), QPointF(bob.center().x(), eve.center().y()), QPointF(eve.right(), eve.center().y())]
            self._polyline_arrow(p, path, EVE_ACCENT, dashed=True)
            self._moving_dots_polyline(p, path, EVE_ACCENT)

    def _no_attack_note(self, p: QPainter, channel: QRectF):
        note = QRectF(channel.center().x() - 135, channel.bottom() + 34, 270, 42)
        self._rounded_rect(p, note, "#0F1824", "#2C394D", radius=12)
        p.setPen(QColor(MUTED))
        p.setFont(self._font(10))
        p.drawText(note, Qt.AlignCenter, "No active attack: direct BB84 exchange")


class OverviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.result = default_result()
        self.display_sifted = self.result.sifted_bits
        self._start_sifted = self.result.sifted_bits
        self._target_sifted = self.result.sifted_bits
        self._animation_step = 0
        self._animation_steps = 24
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(24)
        self._animation_timer.timeout.connect(self._advance_animation)
        self.setMinimumSize(185, 185)

    def set_result(self, result: SimulationResult, animate: bool = False):
        self.result = result
        self._target_sifted = result.sifted_bits
        if animate:
            self._start_sifted = 0.0
            self.display_sifted = 0.0
            self._animation_step = 0
            self._animation_timer.start()
        else:
            self._animation_timer.stop()
            self.display_sifted = result.sifted_bits
        self.update()

    def _advance_animation(self):
        self._animation_step += 1
        t = min(1.0, self._animation_step / self._animation_steps)
        eased = 1.0 - (1.0 - t) ** 3
        self.display_sifted = self._start_sifted + (self._target_sifted - self._start_sifted) * eased
        if t >= 1.0:
            self.display_sifted = self._target_sifted
            self._animation_timer.stop()
        self.update()

    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        p.fillRect(self.rect(), QColor(PANEL))
        size = min(self.width(), self.height(), 195) - 22
        size = max(size, 90)
        rect = QRectF((self.width() - size) / 2, (self.height() - size) / 2, size, size)
        line_width = max(18, int(size * 0.15))

        p.setPen(QPen(QColor("#2A3445"), line_width, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 0, 360 * 16)
        p.setPen(QPen(QColor(ACCENT), line_width, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, int(-360 * self.display_sifted / 100.0 * 16))

        p.setPen(QColor(TEXT))
        p.setFont(QFont(FONT, 17, QFont.Bold))
        p.drawText(QRectF(0, self.height() / 2 - 28, self.width(), 32), Qt.AlignCenter, f"{self.display_sifted:.1f}%")
        p.setPen(QColor(MUTED))
        p.setFont(QFont(FONT, 10))
        p.drawText(QRectF(0, self.height() / 2 + 5, self.width(), 26), Qt.AlignCenter, "Sifted")


class ResultRow(QFrame):
    def __init__(self, icon: str, label: str, value: str):
        super().__init__()
        self.setObjectName("MetricRow")
        self.setFixedHeight(58)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 9, 18, 9)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setObjectName("MetricIcon")
        icon_label.setFixedSize(34, 34)
        icon_label.setAlignment(Qt.AlignCenter)

        name = QLabel(label)
        name.setObjectName("MetricLabel")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(icon_label)
        layout.addWidget(name, 1)
        layout.addWidget(self.value_label)

    def set_pending(self):
        self.value_label.setText("—")
        self.value_label.setStyleSheet(f"color: {MUTED_2};")

    def set_value(self, value: str):
        self.value_label.setStyleSheet("")
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.result = default_result()
        self.metric_rows: dict[str, ResultRow] = {}
        self.legend_values: dict[str, QLabel] = {}
        self.metric_animation_token = 0
        self.worker: BackendWorker | None = None
        self.selected_scenario: ScenarioPreset | None = None
        self.main_defaults, self.advanced_settings = load_frontend_defaults()

        self.setWindowTitle("QKD Simulator - PySide6 Frontend")
        self.resize(1420, 800)
        self.setMinimumSize(1180, 700)

        self.root = QWidget()
        self.root.setObjectName("Root")
        self.setCentralWidget(self.root)
        self._apply_stylesheet()
        self._build_layout()
        self.refresh_ui()

    def _build_layout(self):
        root_layout = QVBoxLayout(self.root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_header())
        root_layout.addWidget(self._build_body(), 1)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(72)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 12, 22, 12)
        layout.setSpacing(14)

        logo = QLabel("⚛")
        logo.setObjectName("Logo")
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignCenter)

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(0)
        title = QLabel("QKD Simulator")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("PySide6 interface for BB84 and side-channel attack simulation")
        subtitle.setObjectName("HeaderSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        layout.addWidget(logo)
        layout.addLayout(title_box)
        layout.addStretch()

        # Scenario shortcuts stay in the top bar, but grouped near the backend status
        # to keep the left side focused on the app title.
        self.scenario_button = QPushButton("▦  Scenario presets")
        self.scenario_button.setObjectName("ScenarioButton")
        self.scenario_button.setFixedSize(182, 34)
        self.scenario_button.clicked.connect(self.open_scenario_presets)
        layout.addWidget(self.scenario_button)

        self.scenario_label = QLabel("Preset: manual configuration")
        self.scenario_label.setObjectName("ScenarioTag")
        self.scenario_label.setFixedHeight(34)
        self.scenario_label.setMaximumWidth(300)
        self.scenario_label.setWordWrap(False)
        layout.addWidget(self.scenario_label)

        self.backend_status = QLabel("Backend: auto")
        self.backend_status.setObjectName("BackendPill")
        layout.addWidget(self.backend_status)

        for text in ["ⓘ", "⚙"]:
            button = QPushButton(text)
            button.setObjectName("HeaderButton")
            button.setFixedSize(34, 34)
            if text == "⚙":
                button.clicked.connect(self.open_advanced_settings)
            layout.addWidget(button)
        return header

    def _build_body(self) -> QWidget:
        body = QWidget()
        body.setObjectName("Body")
        layout = QGridLayout(body)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        layout.setColumnMinimumWidth(0, 295)
        layout.setColumnMinimumWidth(2, 370)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 0)
        layout.setRowStretch(0, 1)
        layout.setRowMinimumHeight(1, 285)

        layout.addWidget(self._build_left_panel(), 0, 0, 2, 1)
        layout.addWidget(self._build_diagram_panel(), 0, 1, 1, 1)
        layout.addWidget(self._build_results_panel(), 0, 2, 1, 1)
        layout.addWidget(self._build_logs_panel(), 1, 1, 1, 1)
        layout.addWidget(self._build_overview_panel(), 1, 2, 1, 1)
        return body

    def _build_left_panel(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(11)
        layout.addWidget(SectionTitle("☷", "Simulation Parameters"))

        self.protocol = QLineEdit(str(self.main_defaults.get("protocol", "bb84")))
        self.protocol.setObjectName("Input")
        self.protocol.setReadOnly(True)
        self.protocol.setToolTip("Only BB84 is currently supported by the backend.")

        self.message_size = QLineEdit(str(self.main_defaults.get("message_size", 200)))
        self.message_size.setObjectName("Input")
        self.message_size.setValidator(QIntValidator(1, 1000000, self.message_size))
        self.photons = QLineEdit(str(self.main_defaults.get("average_emitted_photon", 1.0)))
        self.photons.setObjectName("Input")
        self.photons.setValidator(QDoubleValidator(-1.0, 1000.0, 4, self.photons))
        self.photons.setToolTip("-1 = exactly one emitted photon; PNS becomes impossible.")

        self.bit_loss = LabeledFloatSlider("Quantum channel bit loss", float(self.main_defaults.get("quantum_canal_bit_loss", 2.00)), 0.0, 100.0, 2)
        self.bit_flip = LabeledFloatSlider("Quantum channel bit flip", float(self.main_defaults.get("quantum_canal_bit_flip", 2.00)), 0.0, 100.0, 2)
        self.qber_percent = LabeledSlider("QBER sample percentage", int(self.main_defaults.get("qber_percent", 20)), 1, 100)
        self.qber_threshold = LabeledSlider("QBER tolerance", int(self.main_defaults.get("qber_tolerance", 11)), 0, 100)
        self.attack = QComboBox()
        self.attack.setObjectName("Input")
        self.attack.addItems(list(ATTACKS.keys()))
        self.attack.setCurrentText(str(self.main_defaults.get("attack_label", "Trojan Horse")))

        self.channel_warning = QLabel("")
        self.channel_warning.setObjectName("WarningText")
        self.channel_warning.setWordWrap(True)

        layout.addWidget(Field("Protocol", self.protocol))
        layout.addWidget(Field("Message size (qubits)", self.message_size))
        layout.addWidget(Field("Average emitted photons", self.photons, "Backend setting: average_emitted_photon"))
        layout.addWidget(self.bit_loss)
        layout.addWidget(self.bit_flip)
        layout.addWidget(self.channel_warning)
        layout.addWidget(self.qber_percent)
        layout.addWidget(self.qber_threshold)
        layout.addWidget(Field("Attack type", self.attack))

        layout.addStretch()

        self.run_button = QPushButton("▷  Run Simulation")
        self.run_button.setObjectName("RunButton")
        self.run_button.setFixedHeight(48)
        self.run_button.clicked.connect(self.on_run)
        self.stop_button = QPushButton("■  Stop process")
        self.stop_button.setObjectName("StopButton")
        self.stop_button.setFixedHeight(42)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.on_stop_process)
        self.reset_button = QPushButton("↻  Reset")
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.setFixedHeight(42)
        self.reset_button.clicked.connect(self.on_reset)
        layout.addWidget(self.run_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.reset_button)

        self.attack.currentTextChanged.connect(lambda _: self.refresh_diagram_only())
        self.bit_loss.slider.valueChanged.connect(lambda _: self.refresh_diagram_only())
        self.bit_flip.slider.valueChanged.connect(lambda _: self.refresh_diagram_only())
        return card

    def _build_diagram_panel(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)
        layout.addWidget(SectionTitle("♢", "Communication Diagram"))
        self.diagram = DiagramWidget()
        layout.addWidget(self.diagram, 1)
        return card

    def _build_results_panel(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)
        layout.addWidget(SectionTitle("▥", "Simulation Results"))

        scroll = QScrollArea()
        scroll.setObjectName("ResultsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("ResultsContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        rows = [
            ("qber", "▥", "QBER", "4.8%"),
            ("key", "⚿", "Final key size", "76 bits"),
            ("eve", "◉", "Eve knowledge", "0.0%"),
            ("agreement", "◇", "Alice/Bob agreement", "96.0%"),
            ("status", "♢", "Communication status", "Ready"),
            ("attack", "△", "Attack detected", "No"),
            ("sifted", "▽", "Sifted bits", "48.0%"),
        ]
        for key, icon, label, value in rows:
            row = ResultRow(icon, label, value)
            self.metric_rows[key] = row
            content_layout.addWidget(row)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return card

    def _build_logs_panel(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(SectionTitle("▤", "Simulation Logs"))

        scroll = QScrollArea()
        scroll.setObjectName("LogsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.log_container = QWidget()
        self.log_container.setObjectName("LogsContent")
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(0)
        scroll.setWidget(self.log_container)
        layout.addWidget(scroll, 1)
        return card

    def _build_overview_panel(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)
        layout.addWidget(SectionTitle("", "Channel Overview"))

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(18)
        self.overview = OverviewWidget()
        content.addWidget(self.overview, 2)

        legend = QVBoxLayout()
        legend.setSpacing(8)
        legend.setContentsMargins(0, 8, 0, 8)
        self._legend_row(legend, "sifted", ACCENT, "Sifted bits", "48.0%")
        self._legend_row(legend, "discarded", "#62708A", "Discarded bits", "52.0%")
        sep = QFrame()
        sep.setObjectName("Separator")
        sep.setFixedHeight(1)
        legend.addWidget(sep)
        self._legend_row(legend, "lost", TEAL_SOFT, "Lost", "2.00%")
        self._legend_row(legend, "flipped", TEAL_SOFT, "Flipped", "2.00%")
        self._legend_row(legend, "mode", ACCENT_SOFT, "Mode", "Waiting")
        legend.addStretch()
        content.addLayout(legend, 1)
        layout.addLayout(content, 1)
        return card

    def _legend_row(self, layout: QVBoxLayout, key: str, color: str, label: str, value: str):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color};")
        name = QLabel(label)
        name.setObjectName("LegendLabel")
        val = QLabel(value)
        val.setObjectName("LegendValue")
        row.addWidget(dot)
        row.addWidget(name)
        row.addStretch()
        row.addWidget(val)
        layout.addLayout(row)
        self.legend_values[key] = val

    def open_advanced_settings(self):
        dialog = AdvancedSettingsDialog(self.advanced_settings, self)
        if dialog.exec() == QDialog.Accepted:
            self.advanced_settings = dialog.values()

    def open_scenario_presets(self):
        if self.worker is not None and self.worker.isRunning():
            return
        dialog = ScenarioPresetsDialog(load_scenario_presets(), self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_preset is not None:
            self.apply_scenario_preset(dialog.selected_preset)

    def apply_scenario_preset(self, preset: ScenarioPreset):
        """Fill visible fields from one preset, then launch one simulation."""
        self.selected_scenario = preset
        values = dict(preset.values)

        if "message_size" in values:
            self.message_size.setText(str(int(float(values["message_size"]))))
        if "average_emitted_photon" in values:
            self.photons.setText(str(values["average_emitted_photon"]))
        if "bit_loss" in values:
            self.bit_loss.setValue(float(values["bit_loss"]))
        if "bit_flip" in values:
            self.bit_flip.setValue(float(values["bit_flip"]))
        if "qber_percent" in values:
            self.qber_percent.setValue(int(float(values["qber_percent"])))

        self.attack.setCurrentText(ATTACK_LABELS.get(preset.attack_flag, "None" if preset.attack_flag is None else str(preset.attack_flag)))

        advanced = dict(self.advanced_settings)
        direct_advanced_keys = [
            "message_interval",
            "tolerance_message_not_receive",
            "progress_bar",
            "perfect_apd_eve",
            "breakdown_voltage",
            "dead_time_min",
            "dead_time_max",
            "bias_voltage",
            "gate_off_duration",
            "gate_on_duration",
            "many_clicks_gestion",
            "after_pulsing",
            "emission_click_event",
            "timing_attack",
        ]
        for key in direct_advanced_keys:
            if key in values:
                advanced[key] = values[key]
        if "perfect_apd" in values:
            advanced["perfect_apd_bob"] = bool(values["perfect_apd"])
        self.advanced_settings = advanced

        self.scenario_label.setText(f"Preset: {preset.group} / {preset.name}")
        self.refresh_ui()
        # Let Qt repaint the changed fields so the user sees the preset before the backend starts.
        QTimer.singleShot(450, self.on_run)

    def refresh_diagram_only(self):
        total = self.bit_loss.value() + self.bit_flip.value()
        if total > 100.0:
            self.channel_warning.setText("⚠ Bit loss + bit flip exceeds 100%. The backend treats them cumulatively.")
        else:
            self.channel_warning.setText("")
        self.diagram.update_values(self.bit_loss.value(), self.bit_flip.value(), self.attack.currentText())

    def _current_config(self) -> SimulationConfig:
        message_size = self._safe_int(self.message_size.text(), 200)
        photons = self._safe_float(self.photons.text(), 1.0)
        return SimulationConfig(
            message_size=max(1, message_size),
            protocol=self.protocol.text().lower(),
            average_emitted_photon=photons,
            quantum_canal_bit_loss=self.bit_loss.value(),
            quantum_canal_bit_flip=self.bit_flip.value(),
            qber_percent=self.qber_percent.value(),
            qber_tolerance=self.qber_threshold.value(),
            attack_label=self.attack.currentText(),
            attack_flag=ATTACKS[self.attack.currentText()],
            advanced=dict(self.advanced_settings),
            scenario_name=self.selected_scenario.label if self.selected_scenario is not None else None,
        )

    def on_run(self):
        if self.worker is not None and self.worker.isRunning():
            return
        config = self._current_config()
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        self.stop_button.setEnabled(True)
        self.stop_button.setText("■  Stop process")
        self.result = SimulationResult(
            qber=0.0,
            final_key_size=0,
            eve_knowledge=0.0,
            key_agreement=0.0,
            communication_status="Running",
            attack_detected="—",
            sifted_bits=0.0,
            discarded_bits=0.0,
            lost=config.quantum_canal_bit_loss,
            flipped=config.quantum_canal_bit_flip,
            mode="Running",
            logs=[
                ("now", "violet", "Simulation started."),
                ("now", "teal", f"Scenario preset: {config.scenario_name}") if config.scenario_name else ("now", "muted", "Manual parameter run."),
                ("now", "violet", f"Attack selected: {config.attack_label}"),
            ],
        )
        self.refresh_ui(animate=False, pending=True)
        self.diagram.start_animation()
        self.worker = BackendWorker(config, self)
        self.worker.finished.connect(self.on_backend_finished)
        self.worker.start()

    def on_stop_process(self):
        if self.worker is not None and self.worker.isRunning():
            self.stop_button.setEnabled(False)
            self.stop_button.setText("Stopping...")
            self.result.logs.append(("stop", "warn", "Stop requested. Waiting for backend process to close."))
            self._refresh_logs()
            self.worker.stop_process()

    def on_backend_finished(self, result: SimulationResult):
        self.result = result
        self.run_button.setEnabled(True)
        self.run_button.setText("▷  Run Simulation")
        self.stop_button.setEnabled(False)
        self.stop_button.setText("■  Stop process")
        self.diagram.stop_animation()
        self.refresh_ui(animate=True)
        self.worker = None

    def on_reset(self):
        if self.worker is not None and self.worker.isRunning():
            return
        self.selected_scenario = None
        self.main_defaults, self.advanced_settings = load_frontend_defaults()
        self.protocol.setText(str(self.main_defaults.get("protocol", "bb84")))
        self.message_size.setText(str(self.main_defaults.get("message_size", 200)))
        self.photons.setText(str(self.main_defaults.get("average_emitted_photon", 1.0)))
        self.bit_loss.setValue(float(self.main_defaults.get("quantum_canal_bit_loss", 2.00)))
        self.bit_flip.setValue(float(self.main_defaults.get("quantum_canal_bit_flip", 2.00)))
        self.qber_percent.setValue(int(self.main_defaults.get("qber_percent", 20)))
        self.qber_threshold.setValue(int(self.main_defaults.get("qber_tolerance", 11)))
        self.attack.setCurrentText(str(self.main_defaults.get("attack_label", "Trojan Horse")))
        self.scenario_label.setText("Preset: manual configuration")
        self.result = default_result()
        self.refresh_ui()

    def _metric_values(self) -> dict[str, str]:
        return {
            "qber": f"{self.result.qber:.2f}%",
            "key": f"{self.result.final_key_size} bits",
            "eve": f"{self.result.eve_knowledge:.2f}%",
            "agreement": f"{self.result.key_agreement:.2f}%",
            "status": self.result.communication_status,
            "attack": self.result.attack_detected,
            "sifted": f"{self.result.sifted_bits:.2f}%",
        }

    def _animate_metric_values(self, values: dict[str, str]):
        self.metric_animation_token += 1
        token = self.metric_animation_token
        order = ["qber", "key", "eve", "agreement", "status", "attack", "sifted"]
        for key in order:
            self.metric_rows[key].set_pending()
        for index, key in enumerate(order):
            def reveal(metric_key=key, expected_token=token):
                if expected_token == self.metric_animation_token:
                    self.metric_rows[metric_key].set_value(values[metric_key])
            QTimer.singleShot(70 + index * 75, reveal)

    def refresh_ui(self, animate: bool = False, pending: bool = False):
        values = self._metric_values()
        if pending:
            self.metric_animation_token += 1
            for key in self.metric_rows:
                self.metric_rows[key].set_pending()
            self.metric_rows["status"].set_value("Running")
        elif animate:
            self._animate_metric_values(values)
        else:
            self.metric_animation_token += 1
            for key, value in values.items():
                self.metric_rows[key].set_value(value)

        self.refresh_diagram_only()
        self.overview.set_result(self.result, animate=animate)
        self.legend_values["sifted"].setText(f"{self.result.sifted_bits:.2f}%")
        self.legend_values["discarded"].setText(f"{self.result.discarded_bits:.2f}%")
        self.legend_values["lost"].setText(f"{self.result.lost:.2f}%")
        self.legend_values["flipped"].setText(f"{self.result.flipped:.2f}%")
        self.legend_values["mode"].setText(self.result.mode)
        self.backend_status.setText(f"Mode: {self.result.mode}")
        self._refresh_logs()

    def _refresh_logs(self):
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for time_str, kind, message in self.result.logs:
            row = QFrame()
            row.setObjectName("LogRow")
            layout = QHBoxLayout(row)
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(10)
            time_label = QLabel(time_str)
            time_label.setObjectName("LogTime")
            dot = QLabel("●")
            dot.setObjectName("LogDot")
            dot_color = ACCENT if kind == "violet" else TEAL if kind == "teal" else WARN if kind == "warn" else MUTED_2
            dot.setStyleSheet(f"color: {dot_color};")
            msg = QLabel(message)
            if kind in {"details", "stdout", "stderr", "trace"}:
                msg.setObjectName("LogMessageMono")
            else:
                msg.setObjectName("LogMessage")
            msg.setWordWrap(True)
            msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(time_label)
            layout.addWidget(dot)
            layout.addWidget(msg, 1)
            self.log_layout.addWidget(row)
        self.log_layout.addStretch()

    @staticmethod
    def _safe_int(value: str, default: int) -> int:
        try:
            return int(value)
        except ValueError:
            return default

    @staticmethod
    def _safe_float(value: str, default: float) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return default

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget#Root {{
                background: {BG};
                color: {TEXT};
                font-family: '{FONT}';
            }}
            QWidget#Body {{
                background: {BG};
            }}
            QFrame#Header {{
                background: {HEADER};
            }}
            QLabel#Logo {{
                background: {ACCENT_DARK};
                border-radius: 10px;
                color: {TEXT};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#HeaderTitle {{
                color: {TEXT};
                font-size: 24px;
                font-weight: 700;
            }}
            QLabel#HeaderSubtitle {{
                color: {MUTED};
                font-size: 13px;
            }}
            QLabel#BackendPill {{
                background: {PANEL_ALT};
                border: 1px solid {BORDER};
                border-radius: 13px;
                color: {MUTED};
                padding: 5px 12px;
                font-size: 12px;
            }}
            QPushButton#HeaderButton {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 8px;
                color: {TEXT};
                font-size: 15px;
            }}
            QPushButton#HeaderButton:hover {{
                background: {CARD_SOFT};
            }}
            QFrame#Card {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel#SectionIcon {{
                color: {TEXT};
                font-size: 16px;
            }}
            QLabel#SectionTitle {{
                color: {TEXT};
                font-size: 15px;
                font-weight: 700;
            }}
            QLabel#FieldLabel {{
                color: {TEXT};
                font-size: 12px;
            }}
            QLabel#InfoIcon, QLabel#MutedText {{
                color: {MUTED_2};
                font-size: 12px;
            }}
            QLabel#FieldDetail {{
                color: {MUTED_2};
                font-size: 11px;
            }}
            QLabel#WarningText {{
                color: {WARN};
                font-size: 11px;
            }}
            QLineEdit#Input, QComboBox#Input {{
                background: {PANEL_ALT};
                border: 1px solid {BORDER};
                border-radius: 7px;
                color: {TEXT};
                min-height: 34px;
                padding: 0 10px;
                font-size: 13px;
            }}
            QLineEdit#Input:read-only {{
                color: {MUTED};
                background: #0B121C;
            }}
            QLineEdit#Input:disabled {{
                color: {MUTED_2};
                border: 1px solid #1C2635;
                background: #0A1018;
            }}
            QComboBox#Input::drop-down {{
                border: none;
                width: 26px;
            }}
            QComboBox QAbstractItemView {{
                background: {PANEL};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {CARD_SOFT};
            }}
            QSlider::groove:horizontal {{
                height: 8px;
                background: {TRACK};
                border-radius: 4px;
            }}
            QSlider::sub-page:horizontal {{
                background: {ACCENT};
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {ACCENT};
                width: 18px;
                height: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }}
            QLabel#ValueBox, QLineEdit#ValueBox {{
                background: {PANEL_ALT};
                border: 1px solid transparent;
                border-radius: 6px;
                color: {TEXT};
                font-size: 13px;
                qproperty-alignment: AlignCenter;
            }}
            QLineEdit#ValueBox:read-only {{
                background: {PANEL_ALT};
                color: {TEXT};
            }}
            QLineEdit#ValueBox:focus {{
                border: 1px solid {ACCENT};
                background: #0E1723;
            }}
            QPushButton#RunButton {{
                background: {ACCENT_SOFT};
                border: none;
                border-radius: 8px;
                color: {TEXT};
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton#RunButton:hover {{
                background: {ACCENT};
            }}
            QPushButton#RunButton:disabled {{
                background: {ACCENT_DARK};
                color: {MUTED};
            }}
            QPushButton#ScenarioButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {ACCENT_DARK}, stop:1 {CARD_SOFT});
                border: 1px solid {ACCENT_SOFT};
                border-radius: 8px;
                color: {TEXT};
                font-size: 13px;
                font-weight: 700;
                padding: 0 12px;
                text-align: left;
            }}
            QPushButton#ScenarioButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {ACCENT_SOFT}, stop:1 {ACCENT_DARK});
                border: 1px solid {ACCENT};
            }}
            QPushButton#ScenarioButton:pressed {{
                background: {ACCENT_DARK};
                border: 1px solid {ACCENT};
            }}
            QLabel#ScenarioTag {{
                background: {PANEL_ALT};
                border: 1px solid {BORDER_SOFT};
                border-left: 3px solid {ACCENT};
                border-radius: 8px;
                color: {MUTED};
                font-size: 12px;
                padding: 7px 9px;
            }}
            QPushButton#AdvancedButton {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 8px;
                color: {TEXT};
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#AdvancedButton:hover {{
                background: {CARD_SOFT};
            }}
            QPushButton#StopButton {{
                background: transparent;
                border: 1px solid {EVE_BORDER};
                border-radius: 8px;
                color: {TEXT};
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton#StopButton:hover {{
                background: {EVE_CARD};
            }}
            QPushButton#StopButton:disabled {{
                color: {MUTED_2};
                border: 1px solid {BORDER_SOFT};
            }}
            QPushButton#ResetButton {{
                background: transparent;
                border: 1px solid {BORDER_SOFT};
                border-radius: 8px;
                color: {TEXT};
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton#ResetButton:hover {{
                background: {CARD_SOFT};
            }}
            QFrame#MetricRow {{
                background: #111A27;
                border: 1px solid {BORDER_SOFT};
                border-radius: 10px;
            }}
            QLabel#MetricIcon {{
                background: #2B3448;
                border-radius: 17px;
                color: {TEXT};
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#MetricLabel {{
                color: {TEXT};
                font-size: 13px;
            }}
            QLabel#MetricValue {{
                color: {ACCENT};
                font-size: 17px;
                font-weight: 700;
            }}
            QScrollArea#ResultsScroll, QScrollArea#AdvancedScroll, QScrollArea#LogsScroll {{
                background: transparent;
                border: none;
            }}
            QScrollArea#ResultsScroll QWidget#ResultsContent {{
                background: {PANEL};
            }}
            QWidget#LogsContent {{
                background: {PANEL};
            }}
            QWidget#AdvancedContent {{
                background: {BG};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {BORDER};
                border-radius: 4px;
                min-height: 32px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ACCENT_SOFT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QFrame#LogRow {{
                border-bottom: 1px solid {BORDER_SOFT};
                background: transparent;
            }}
            QLabel#LogTime {{
                color: {MUTED};
                font-size: 12px;
                min-width: 72px;
            }}
            QLabel#LogMessage {{
                color: {TEXT};
                font-size: 12px;
            }}
            QLabel#LogMessageMono {{
                color: {TEXT};
                font-size: 11px;
                font-family: 'Consolas', 'Courier New', monospace;
            }}
            QLabel#LegendLabel {{
                color: {TEXT};
                font-size: 12px;
            }}
            QLabel#LegendValue {{
                color: {TEXT};
                font-size: 12px;
            }}
            QPushButton#PresetButton {{
                background: {PANEL_ALT};
                border: 1px solid {BORDER_SOFT};
                border-radius: 9px;
                color: {TEXT};
                font-size: 12px;
                font-weight: 600;
                padding: 8px 12px;
                text-align: left;
            }}
            QPushButton#PresetButton:hover {{
                background: {CARD_SOFT};
                border: 1px solid {ACCENT_SOFT};
            }}
            QDialog#AdvancedDialog {{
                background: {BG};
                color: {TEXT};
                font-family: '{FONT}';
            }}
            QLabel#AdvancedTitle {{
                color: {TEXT};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#AdvancedSubtitle {{
                color: {MUTED};
                font-size: 12px;
            }}
            QFrame#AdvancedCard {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QLabel#AdvancedSectionTitle {{
                color: {TEXT};
                font-size: 14px;
                font-weight: 700;
            }}
            QCheckBox#AdvancedCheck {{
                color: {TEXT};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox#AdvancedCheck::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid {BORDER};
                background: {PANEL_ALT};
            }}
            QCheckBox#AdvancedCheck::indicator:checked {{
                background: {ACCENT};
                border: 1px solid {ACCENT};
            }}
            QPushButton#ApplyButton {{
                background: {ACCENT_SOFT};
                border: none;
                border-radius: 8px;
                color: {TEXT};
                min-width: 95px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#ApplyButton:hover {{
                background: {ACCENT};
            }}
            QPushButton#CancelButton {{
                background: transparent;
                border: 1px solid {BORDER_SOFT};
                border-radius: 8px;
                color: {TEXT};
                min-width: 95px;
                font-size: 13px;
                font-weight: 700;
            }}
            QPushButton#CancelButton:hover {{
                background: {CARD_SOFT};
            }}
            QFrame#Separator {{
                background: {BORDER_SOFT};
                border: none;
            }}
        """)


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
