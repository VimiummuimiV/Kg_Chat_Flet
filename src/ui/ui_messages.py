"""Messages display UI for the chat."""
import flet as ft
from datetime import datetime


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
    
    input_field = ft.TextField(
        label="Type a message...",
        multiline=True,
        shift_enter=True,
        min_lines=1,
        max_lines=3,
        expand=True,
        text_size=12
    )
    
    send_button = ft.Button("Send", height=40)
    
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


def add_message_to_view(messages_view, msg, page):
    """Add a message to the messages view - compact inline format.
    
    Args:
        messages_view: ListView for messages
        msg: Message object with login, body, timestamp, etc.
        page: Page object for scaling
    """
    scale = page.data.get('scale', 100) / 100.0
    base_size = 11
    scaled_size = base_size * scale
    
    # Format timestamp as HH:MM:SS (no brackets)
    timestamp = msg.timestamp if hasattr(msg, 'timestamp') and msg.timestamp else datetime.now()
    time_str = timestamp.strftime("%H:%M:%S")
    
    # Get login and background color
    login = msg.login if msg.login else "Unknown"
    bg_color = msg.background if hasattr(msg, 'background') and msg.background else None
    
    # Create time part
    time_text = ft.Text(
        f"{time_str} ",
        size=scaled_size,
        color=ft.Colors.GREY_500
    )
    
    # Create username part with color
    username_text = ft.Text(
        f"{login}: ",
        size=scaled_size,
        weight=ft.FontWeight.BOLD,
        color=bg_color if bg_color else None
    )
    
    # Create message part
    message_text = ft.Text(
        msg.body,
        size=scaled_size,
        selectable=True
    )
    
    # Combine in a row that wraps
    msg_row = ft.Row(
        [time_text, username_text, message_text],
        spacing=0,
        wrap=True
    )
    
    messages_view.controls.append(msg_row)
    
    # Auto-scroll and limit messages
    if len(messages_view.controls) > 100:
        messages_view.controls.pop(0)