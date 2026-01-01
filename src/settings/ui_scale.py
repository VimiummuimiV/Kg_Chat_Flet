"""Font size management and UI controls for message & userlist text only."""
from pathlib import Path
import json
import flet as ft


# Primary config file in repository
CONFIG_FILE = Path(__file__).parent.parent / "config.json"
# Backwards-compatible fallback
SCALE_FILE = Path.home() / ".kg_chat_scale"


def _read_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def load_font_size() -> int:
    """Load saved font size percentage from config.json or fallback to old file or 100."""
    try:
        cfg = _read_config()
        ui = cfg.get("ui", {})
        value = int(ui.get("font_size", ui.get("ui_scale", 100)))
        return max(50, min(200, value))
    except Exception:
        # Fallback to old file
        try:
            with open(SCALE_FILE, "r") as f:
                value = int(f.read().strip())
                return max(50, min(200, value))
        except Exception:
            return 100


def save_font_size(value: int):
    """Save font size percentage into config.json (under ui.font_size)."""
    try:
        cfg = _read_config()
        if "ui" not in cfg or not isinstance(cfg["ui"], dict):
            cfg["ui"] = {}
        cfg["ui"]["font_size"] = int(value)
        _write_config(cfg)
    except Exception:
        # Fallback to old file
        try:
            with open(SCALE_FILE, "w") as f:
                f.write(str(int(value)))
        except Exception:
            pass


def apply_font_size(page, font_percent: int):
    """Apply font size to Text controls that have '_base_size' attribute.

    Only Text controls which explicitly set '_base_size' will be changed
    — this keeps UI elements (buttons, containers, images) at static sizes.
    Args:
        page: Flet Page object
        font_percent: Percentage (50-200)
    """
    scale = font_percent / 100.0

    def update_controls(control):
        try:
            if isinstance(control, ft.Text) and hasattr(control, "_base_size"):
                control.size = control._base_size * scale

            # Support TextField text size scaling for controls that opt-in
            if isinstance(control, ft.TextField) and hasattr(control, "_base_text_size"):
                control.text_size = control._base_text_size * scale
        except Exception:
            pass

        if hasattr(control, "controls") and control.controls:
            for child in list(control.controls):
                update_controls(child)
        if hasattr(control, "content") and control.content:
            update_controls(control.content)

    for control in list(page.controls):
        update_controls(control)


def load_userlist_visible(default: bool = True) -> bool:
    try:
        cfg = _read_config()
        ui = cfg.get("ui", {})
        return bool(ui.get("userlist_visible", default))
    except Exception:
        return default


def save_userlist_visible(value: bool):
    try:
        cfg = _read_config()
        if "ui" not in cfg or not isinstance(cfg["ui"], dict):
            cfg["ui"] = {}
        cfg["ui"]["userlist_visible"] = bool(value)
        _write_config(cfg)
    except Exception:
        pass


def build_font_controls(on_font_change_callback=None) -> tuple:
    """Build font size slider and label.

    Args:
        on_font_change_callback: callable(font_percent) when slider changes

    Returns:
        (slider, label, initial_font_percent)
    """
    initial_font = load_font_size()

    label = ft.Text(f"{initial_font}%", size=11, width=50)

    def on_change(e):
        value = int(e.control.value)
        label.value = f"{value}%"
        save_font_size(value)
        if on_font_change_callback:
            on_font_change_callback(value)

    slider = ft.Slider(
        min=50,
        max=200,
        value=initial_font,
        divisions=150,
        on_change=on_change,
        width=120,
    )

    return slider, label, initial_font