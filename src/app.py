"""KG Chat - Main entry point."""
from pathlib import Path
import threading
import flet as ft
from screeninfo import get_monitors

from ui.accounts_manager import build_welcome
from ui.ui_messages import build_messages_ui
from ui.ui_userlist import build_userlist_ui, rebuild_userlist
from settings.ui_scale import (
    build_font_controls,
    load_font_size,
    apply_font_size,
    load_userlist_visible,
    save_userlist_visible,
    load_icon_settings,
)
from settings.themes import create_theme_toggle_button, load_theme_mode, get_theme_mode_enum
from core.xmpp import XMPPClient
from notifications import send_chat_notification


def main(page: ft.Page):
    page.title = "KG Chat"
    page.padding = 10

    window_width = 1100
    window_height = 750

    page.window.width = window_width
    page.window.height = window_height
    page.window.min_width = 900
    page.window.min_height = 600
    page.window.resizable = True

    # Manual centering - works more smoothly
    try:
        monitor = get_monitors()[0]  # primary monitor
        screen_width = monitor.width
        screen_height = monitor.height

        page.window.left = (screen_width - window_width) // 2
        page.window.top = (screen_height - window_height) // 2
    except Exception:
        page.window.center()  # fallback if screeninfo fails

    page.update()

    xmpp_client = None
    
    if page.data is None:
        page.data = {}
    page.data['font_size'] = load_font_size()
    page.data['userlist_visible'] = load_userlist_visible()
    
    saved_theme = load_theme_mode()
    page.theme_mode = get_theme_mode_enum(saved_theme)
    
    def on_connect(login, account):
        nonlocal xmpp_client
        
        try:
            cfg_path = str(Path(__file__).parent / "config.json")
            xmpp_client = XMPPClient(cfg_path)
            
            if not xmpp_client.connect(account):
                page.snack_bar = ft.SnackBar(ft.Text("Failed to connect"), open=True)
                page.update()
                return
            
            messages_container, input_field, send_button, messages_view = build_messages_ui(page)
            users_container, users_view = build_userlist_ui(page)
            
            def on_font_change(value):
                page.data['font_size'] = value
                apply_font_size(page, value)
                if xmpp_client:
                    rebuild_userlist(users_view, xmpp_client.user_list.get_all(), page)
                page.update()

            scale_slider, scale_label, initial_size = build_font_controls(on_font_change)
            apply_font_size(page, initial_size)
            
            userlist_visible = [bool(page.data.get('userlist_visible', True))]
            users_container.visible = userlist_visible[0]

            def on_toggle_userlist(e):
                userlist_visible[0] = not userlist_visible[0]
                users_container.visible = userlist_visible[0]
                page.data['userlist_visible'] = userlist_visible[0]
                save_userlist_visible(userlist_visible[0])
                page.update()
            
            btn_size, icon_size = load_icon_settings()
            
            toggle_users_btn = ft.IconButton(
                icon=ft.Icon(ft.Icons.PEOPLE, size=icon_size),
                tooltip="Toggle user list",
                width=btn_size,
                height=btn_size,
                on_click=on_toggle_userlist,
            )

            theme_btn = create_theme_toggle_button(page, icon_size=icon_size, btn_size=btn_size)

            header = ft.Row(
                [
                    toggle_users_btn,
                    theme_btn,
                    ft.VerticalDivider(width=1),
                    scale_slider,
                    scale_label
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

            def on_message(msg):
                from ui.ui_messages import add_message_to_view
                add_message_to_view(messages_view, msg, page, input_field)

                try:
                    is_from_other = not getattr(msg, 'initial', False) and msg.login and msg.login != account.get('login')
                    if is_from_other:
                        send_chat_notification(msg)
                except Exception as e:
                    print(f"❌ Notification error: {e}")
                page.update()
            
            def on_presence(pres):
                rebuild_userlist(users_view, xmpp_client.user_list.get_all(), page)
                page.update()
            
            xmpp_client.set_message_callback(on_message)
            xmpp_client.set_presence_callback(on_presence)
            
            rooms = xmpp_client.account_manager.get_rooms()
            for room in rooms:
                if room.get('auto_join'):
                    xmpp_client.join_room(room['jid'])
            
            rebuild_userlist(users_view, xmpp_client.user_list.get_all(), page)
            
            def on_send(e):
                text = input_field.value.strip()
                if text and xmpp_client:
                    xmpp_client.send_message(text)
                    input_field.value = ""
                    page.update()
            
            send_button.on_click = on_send
            
            def on_input_submit(e):
                on_send(e)
            
            input_field.on_submit = on_input_submit
            
            main_content = ft.Row(
                [messages_container, users_container],
                expand=True,
                spacing=10
            )
            
            page.controls.clear()
            page.add(header)
            page.add(main_content)
            page.update()
            
            def listen_thread():
                xmpp_client.listen()
            
            threading.Thread(target=listen_thread, daemon=True).start()
        
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), open=True)
            page.update()
            import traceback
            traceback.print_exc()
    
    build_welcome(page, on_connect_callback=on_connect)
    apply_font_size(page, page.data.get('font_size', 100))


if __name__ == "__main__":
    ft.app(target=main)