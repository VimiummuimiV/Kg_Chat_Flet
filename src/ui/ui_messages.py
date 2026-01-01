"""Messages display UI for the chat."""
import flet as ft
from datetime import datetime
import json
from pathlib import Path
from helpers.color_contrast import optimize_color_contrast


def build_messages_ui(page):
    """Build and return the messages view and send handler.
    
    Returns:
        (messages_container, input_field, send_button, messages_view)
    """
    messages_view = ft.ListView(
        expand=True,
        spacing=2,
        padding=ft.padding.all(5),
        auto_scroll=True
    )
    
    # Calculate initial font size based on scale
    scale = page.data.get('font_size', 100) / 100.0
    base_text_size = 12
    
    input_field = ft.TextField(
        multiline=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        expand=True,
        text_size=base_text_size * scale
    )
    # Opt into font size scaling system
    input_field._base_text_size = base_text_size
    
    send_button = ft.IconButton(
        icon=ft.Icons.SEND,
        tooltip="Send message",
        width=48,
        height=48,
    )

    
    input_row = ft.Row(
        [input_field, send_button],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )
    
    # Container for messages + input
    messages_container = ft.Column(
        [messages_view, input_row],
        expand=True,
        spacing=8
    )
    
    return messages_container, input_field, send_button, messages_view


def add_message_to_view(messages_view, msg, page, input_field=None):
    """Add a message to the messages view - compact inline format.

    Args:
        messages_view: ListView for messages
        msg: Message object with login, body, timestamp, etc.
        page: Page object for scaling
        input_field: Optional TextField to insert usernames into when clicked
    """
    scale = page.data.get('font_size', 100) / 100.0
    base_size = 11
    scaled_size = base_size * scale

    # Format timestamp as HH:MM:SS (no brackets)
    timestamp = msg.timestamp if hasattr(msg, 'timestamp') and msg.timestamp else datetime.now()
    time_str = timestamp.strftime("%H:%M:%S")

    # Get login and background color
    login = msg.login if msg.login else "Unknown"
    bg_color = msg.background if hasattr(msg, 'background') and msg.background else None
    
    # Optimize color for contrast on dark background
    if bg_color:
        try:
            with open(Path(__file__).parent.parent / "config.json", 'r') as f:
                ui_cfg = json.load(f).get('ui', {})
            bg_color = optimize_color_contrast(
                bg_color, 
                ui_cfg.get('background_color', '#1E1E1E'), 
                target_ratio=ui_cfg.get('contrast_ratio', 4.5)
            )
        except:
            bg_color = optimize_color_contrast(bg_color, '#1E1E1E', target_ratio=4.5)

    # Create time part (store base size so apply_font_size is consistent)
    time_text = ft.Text(
        f"{time_str} ",
        color=ft.Colors.GREY_500
    )
    time_text._base_size = base_size
    time_text.size = base_size * scale

    # Create username part with color
    username_text = ft.Text(
        f"{login}: ",
        weight=ft.FontWeight.BOLD,
        color=bg_color if bg_color else None
    )
    username_text._base_size = base_size
    username_text.size = base_size * scale

    # Create message part
    message_text = ft.Text(
        msg.body,
        selectable=True
    )
    message_text._base_size = base_size
    message_text.size = base_size * scale

    # Unified handler for single and double click actions
    def _handle_username_click(name, double=False):
        if not input_field:
            return
        cur = (input_field.value or "").strip()
        # Build current username list from comma-separated values
        existing = [t.strip() for t in cur.split(',') if t.strip()]

        if double:
            # Special case: if field currently contains exactly one username (whatever it is), clear it
            if len(existing) == 1:
                input_field.value = ""
                input_field.focus = True
                page.update()
                return
            # Otherwise, replace entire field with the clicked username
            input_field.value = f"{name}, "
            input_field.focus = True
            page.update()
            return

        # Single click: add username if not present; prevent duplicates
        if name in existing:
            input_field.focus = True
            page.update()
            return

        new_list = existing + [name]
        input_field.value = ", ".join(new_list) + ", "
        input_field.focus = True
        page.update()

    # Wrap the username in an interactive gesture if available
    username_control = username_text
    try:
        # GestureDetector supports single and double tap
        username_control = ft.GestureDetector(
            content=username_text,
            on_tap=lambda e, n=login: _handle_username_click(n, False),
            on_double_tap=lambda e, n=login: _handle_username_click(n, True)
        )
    except Exception:
        # Fallback: attach a single-click handler if possible
        try:
            username_text.on_click = lambda e, n=login: _handle_username_click(n, False)
            username_control = username_text
        except Exception:
            # Nothing we can do — leave it non-interactive
            username_control = username_text

    # Combine in a row that wraps
    msg_row = ft.Row(
        [time_text, username_control, message_text],
        spacing=0,
        wrap=True
    )

    messages_view.controls.append(msg_row)

    # Auto-scroll and limit messages
    if len(messages_view.controls) > 100:
        messages_view.controls.pop(0)

    # Always scroll to bottom on new messages
    page.run_task(messages_view.scroll_to, offset=10**9, duration=100)