"""KG Chat - Main entry point."""
from pathlib import Path
import threading
import flet as ft

from ui.accounts_manager import build_welcome
from ui.ui_messages import build_messages_ui
from ui.ui_userlist import build_userlist_ui, rebuild_userlist
from settings.ui_scale import (
    build_font_controls,
    load_font_size,
    apply_font_size,
    load_userlist_visible,
    save_userlist_visible,
)
from core.xmpp import XMPPClient


def main(page: ft.Page):
    page.title = "KG Chat"
    page.padding = 10
    xmpp_client = None
    
    # Initialize scale and other UI settings in page.data
    if page.data is None:
        page.data = {}
    page.data['font_size'] = load_font_size()
    # remember whether userlist should be visible
    page.data['userlist_visible'] = load_userlist_visible()
    
    def on_connect(login, account):
        """Called when user clicks Connect in welcome screen."""
        nonlocal xmpp_client
        
        try:
            # Initialize XMPP client
            cfg_path = str(Path(__file__).parent / "config.json")
            xmpp_client = XMPPClient(cfg_path)
            
            # Connect
            if not xmpp_client.connect(account):
                page.snack_bar = ft.SnackBar(ft.Text("Failed to connect"), open=True)
                page.update()
                return
            
            # Build chat interface
            messages_container, input_field, send_button, messages_view = build_messages_ui(page)
            users_container, users_view = build_userlist_ui(page)
            
            # Build font size controls (affects only message & userlist text)
            def on_font_change(value):
                page.data['font_size'] = value
                apply_font_size(page, value)
                page.update()

            scale_slider, scale_label, initial_size = build_font_controls(on_font_change)
            apply_font_size(page, initial_size)
            
            # Create toggle button for userlist
            userlist_visible = [bool(page.data.get('userlist_visible', True))]  # Use list to make it mutable in closure
            users_container.visible = userlist_visible[0]

            def on_toggle_userlist(e):
                userlist_visible[0] = not userlist_visible[0]
                users_container.visible = userlist_visible[0]
                page.data['userlist_visible'] = userlist_visible[0]
                from settings.ui_scale import save_userlist_visible
                save_userlist_visible(userlist_visible[0])
                page.update()
            
            toggle_users_btn = ft.ElevatedButton(
                icon=ft.Icons.PEOPLE,
                tooltip="Toggle user list",
                width=48,
                height=48,
                on_click=on_toggle_userlist,
            )

            # Header
            header = ft.Row(
                [
                    toggle_users_btn,
                    ft.VerticalDivider(width=1),
                    scale_slider,
                    scale_label
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            
            # Set up callbacks for messages and presence
            # Import the local desktop notification wrapper (notifications.py) if available
            try:
                from notifications import send_chat_notification
            except Exception:
                def send_chat_notification(msg, timeout=10):
                    print("🔕 notifications.py not available; install pynput")
                    return False

            def on_message(msg):
                from ui.ui_messages import add_message_to_view
                add_message_to_view(messages_view, msg, page, input_field)

                # Show desktop notification for messages from others
                try:
                    if not getattr(msg, 'initial', False) and msg.login and msg.login != account.get('login'):
                        send_chat_notification(msg)
                except Exception as e:
                    print(f"desktop notify error: {e}")
                page.update()
            
            def on_presence(pres):
                # Rebuild user list when presence changes
                rebuild_userlist(users_view, xmpp_client.user_list.get_all(), page)
                page.update()
            
            xmpp_client.set_message_callback(on_message)
            xmpp_client.set_presence_callback(on_presence)
            
            # Join auto-join rooms
            rooms = xmpp_client.account_manager.get_rooms()
            for room in rooms:
                if room.get('auto_join'):
                    xmpp_client.join_room(room['jid'])
            
            # Initial user list
            rebuild_userlist(users_view, xmpp_client.user_list.get_all(), page)
            
            # Wire send button
            def on_send(e):
                text = input_field.value.strip()
                if text and xmpp_client:
                    xmpp_client.send_message(text)
                    input_field.value = ""
                    page.update()
            
            send_button.on_click = on_send
            
            # Handle Enter key in input field
            def on_input_submit(e):
                on_send(e)
            
            input_field.on_submit = on_input_submit
            
            # Build main chat layout with userlist on the right
            main_content = ft.Row(
                [messages_container, users_container],
                expand=True,
                spacing=10
            )
            
            # Clear and show chat UI with header
            page.controls.clear()
            page.add(header)
            page.add(main_content)
            page.update()
            
            # Start XMPP listener in background thread
            def listen_thread():
                xmpp_client.listen()
            
            threading.Thread(target=listen_thread, daemon=True).start()
        
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), open=True)
            page.update()
            import traceback
            traceback.print_exc()
    
    # Start with welcome screen
    build_welcome(page, on_connect_callback=on_connect)
    # Apply initial font size to the welcome screen so sizes reflect saved preference
    apply_font_size(page, page.data.get('font_size', 100))


if __name__ == "__main__":
    ft.app(target=main)