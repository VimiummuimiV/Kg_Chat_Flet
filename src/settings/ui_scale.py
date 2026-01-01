"""Scale management and UI controls."""
from pathlib import Path
import flet as ft


SCALE_FILE = Path.home() / ".kg_chat_scale"


def load_scale() -> int:
    """Load saved scale value or default to 100."""
    try:
        with open(SCALE_FILE, "r") as f:
            value = int(f.read().strip())
            return max(70, min(150, value))  # Clamp to valid range
    except:
        return 100


def save_scale(value: int):
    """Save scale value to home directory."""
    try:
        with open(SCALE_FILE, "w") as f:
            f.write(str(int(value)))
    except:
        pass


def apply_scale(page, scale_value: int):
    """Apply scale to the entire page.
    
    Args:
        page: Flet Page object
        scale_value: Scale percentage (70-150)
    """
    scale = scale_value / 100.0
    
    # Update text size for all Text controls recursively
    def update_controls(control):
        if isinstance(control, ft.Text):
            if hasattr(control, '_base_size'):
                control.size = control._base_size * scale
            elif control.size:
                control._base_size = control.size
                control.size = control.size * scale
        
        if isinstance(control, ft.TextField):
            if hasattr(control, '_base_text_size'):
                control.text_size = control._base_text_size * scale
            elif control.text_size:
                control._base_text_size = control.text_size
                control.text_size = control.text_size * scale
        
        if isinstance(control, ft.Image):
            if hasattr(control, '_base_width'):
                control.width = control._base_width * scale
                control.height = control._base_height * scale
            elif control.width:
                control._base_width = control.width
                control._base_height = control.height
                control.width = control.width * scale
                control.height = control.height * scale
        
        # Recurse into containers
        if hasattr(control, 'controls'):
            for child in control.controls:
                update_controls(child)
        if hasattr(control, 'content'):
            update_controls(control.content)
    
    for control in page.controls:
        update_controls(control)


def build_scale_controls(on_scale_change_callback=None) -> tuple:
    """Build scale slider and label.
    
    Args:
        on_scale_change_callback: callable(scale_value) when slider changes
    
    Returns:
        (scale_slider, scale_label, initial_scale_value)
    """
    initial_scale = load_scale()
    
    scale_label = ft.Text(f"{initial_scale}%", size=11, width=50)
    
    def on_scale_change(e):
        value = int(e.control.value)
        scale_label.value = f"{value}%"
        save_scale(value)
        if on_scale_change_callback:
            on_scale_change_callback(value)
    
    scale_slider = ft.Slider(
        min=70,
        max=150,
        value=initial_scale,
        divisions=80,
        on_change=on_scale_change,
        width=120
    )
    
    return scale_slider, scale_label, initial_scale