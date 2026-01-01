"""Theme management for KG Chat."""
from pathlib import Path
import json
import flet as ft


# Primary config file in repository
CONFIG_FILE = Path(__file__).parent.parent / "config.json"


def _read_config() -> dict:
    """Read configuration from config.json."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_config(cfg: dict):
    """Write configuration to config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def load_theme_mode() -> str:
    """Load saved theme mode from config.json.
    
    Returns:
        'dark' or 'light' (defaults to 'dark')
    """
    try:
        cfg = _read_config()
        ui = cfg.get("ui", {})
        theme = ui.get("theme_mode", "dark")
        return theme if theme in ["dark", "light"] else "dark"
    except Exception:
        return "dark"


def save_theme_mode(mode: str):
    """Save theme mode to config.json.
    
    Args:
        mode: 'dark' or 'light'
    """
    try:
        if mode not in ["dark", "light"]:
            return
        cfg = _read_config()
        if "ui" not in cfg or not isinstance(cfg["ui"], dict):
            cfg["ui"] = {}
        cfg["ui"]["theme_mode"] = mode
        _write_config(cfg)
    except Exception:
        pass


def get_theme_mode_enum(mode: str) -> ft.ThemeMode:
    """Convert string theme mode to Flet ThemeMode enum.
    
    Args:
        mode: 'dark' or 'light'
    
    Returns:
        ft.ThemeMode.DARK or ft.ThemeMode.LIGHT
    """
    return ft.ThemeMode.DARK if mode == "dark" else ft.ThemeMode.LIGHT


def create_theme_toggle_button(page: ft.Page, icon_size: int = 20, btn_size: int = 48) -> ft.IconButton:
    """Create a theme toggle button with sun/moon icons.
    
    Args:
        page: Flet Page object
        icon_size: Size of the icon in pixels
        btn_size: Size of the button in pixels
    
    Returns:
        IconButton configured for theme toggling
    """
    # Load current theme from config
    current_theme = load_theme_mode()
    page.theme_mode = get_theme_mode_enum(current_theme)
    
    # Set initial icon based on current theme
    initial_icon = ft.Icons.LIGHT_MODE if current_theme == "dark" else ft.Icons.DARK_MODE
    initial_tooltip = "Switch to light theme" if current_theme == "dark" else "Switch to dark theme"
    
    def on_toggle_theme(e):
        """Toggle between light and dark themes."""
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_btn.icon = ft.Icon(ft.Icons.DARK_MODE, size=icon_size)
            theme_btn.tooltip = "Switch to dark theme"
            save_theme_mode("light")
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_btn.icon = ft.Icon(ft.Icons.LIGHT_MODE, size=icon_size)
            theme_btn.tooltip = "Switch to light theme"
            save_theme_mode("dark")
        page.update()
    
    theme_btn = ft.IconButton(
        icon=ft.Icon(initial_icon, size=icon_size),
        tooltip=initial_tooltip,
        width=btn_size,
        height=btn_size,
        on_click=on_toggle_theme,
    )
    
    return theme_btn