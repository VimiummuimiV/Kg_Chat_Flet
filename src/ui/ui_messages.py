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
    
    # Format timestamp
    timestamp = msg.timestamp if hasattr(msg, 'timestamp') and msg.timestamp else datetime.now()
    time_str = timestamp.strftime("%H:%M")
    
    # Get login
    login = msg.login if msg.login else "Unknown"
    
    # Create inline message: [HH:MM] username: message
    message_text = ft.Text(
        f"[{time_str}] {login}: {msg.body}",
        size=scaled_size,
        selectable=True,
        no_wrap=False
    )
    
    # Add avatar if available
    widgets = []
    if hasattr(msg, 'get_avatar_url') and msg.get_avatar_url():
        try:
            avatar = ft.Image(
                src=msg.get_avatar_url(),
                width=int(20 * scale),
                height=int(20 * scale),
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(3)
            )
            widgets.append(avatar)
        except:
            pass
    
    widgets.append(message_text)
    
    msg_row = ft.Row(
        widgets,
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.START
    )
    
    messages_view.controls.append(msg_row)
    
    # Auto-scroll to bottom
    if len(messages_view.controls) > 100:
        messages_view.controls.pop(0)