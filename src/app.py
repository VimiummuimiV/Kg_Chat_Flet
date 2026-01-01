"""KG Chat - Main entry point."""
from pathlib import Path
import threading
import flet as ft
from ui.accounts_manager import build_welcome
from ui.ui_messages import build_messages_ui
from ui.ui_userlist import build_userlist_ui, rebuild_userlist
from settings.ui_scale import build_scale_controls, load_scale, apply_scale
from core.xmpp import XMPPClient


def main(page: ft.Page):
    page.title = "KG Chat"
    page.padding = 10
    xmpp_client = None
    
    # Initialize scale in page.data
    if page.data is None:
        page.data = {}
    page.data['scale'] = load_scale()
    
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
            
            # Build scale controls
            def on_scale_change(value):
                page.data['scale'] = value
                apply_scale(page, value)
                page.update()
            
            scale_slider, scale_label, initial_scale = build_scale_controls(on_scale_change)
            apply_scale(page, initial_scale)
            
            # Create toggle button for userlist
            userlist_visible = [True]  # Use list to make it mutable in closure
            def on_toggle_userlist(e):
                userlist_visible[0] = not userlist_visible[0]
                users_container.visible = userlist_visible[0]
                page.update()
            
            toggle_users_btn = ft.ElevatedButton(
                "👥",
                on_click=on_toggle_userlist,
                tooltip="Toggle user list",
                width=50
            )
            
            # Header with controls
            header = ft.Row(
                [
                    toggle_users_btn,
                    ft.VerticalDivider(width=1),
                    ft.Text("Scale:", size=11),
                    scale_slider,
                    scale_label
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            
            # Set up callbacks for messages and presence
            def on_message(msg):
                from ui.ui_messages import add_message_to_view
                add_message_to_view(messages_view, msg, page)
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


if __name__ == "__main__":
    ft.app(target=main)