"""User list display UI for the chat."""
import flet as ft
import json
from pathlib import Path
from helpers.color_contrast import optimize_color_contrast


def build_userlist_ui(page):
    """Build and return the user list view.
    
    Returns:
        (users_container, users_view)
    """
    scale = page.data.get('font_size', 100) / 100.0

    users_view = ft.ListView(
        expand=True,
        spacing=4,
        padding=ft.padding.all(5)
    )
    # Keep container width static (do not scale UI elements)
    users_container = ft.Column(
        [users_view],
        width=220,
        spacing=0
    )

    return users_container, users_view


def rebuild_userlist(users_view, users_list, page):
    """Rebuild the entire user list from a ChatUser list.
    Separates users in chat from users in game.
    
    Args:
        users_view: ListView for users
        users_list: list of core.userlist.ChatUser objects
        page: Page object for scaling
    """
    scale = page.data.get('font_size', 100) / 100.0
    base_size = 11
    scaled_size = base_size * scale
    
    users_view.controls.clear()
    
    # Filter only online users
    online_users = [u for u in users_list if u.status == 'available']
    
    # Separate into in-chat and in-game
    in_chat = [u for u in online_users if not u.game_id]
    in_game = [u for u in online_users if u.game_id]
    
    # Sort both lists by login
    in_chat = sorted(in_chat, key=lambda u: u.login.lower())
    in_game = sorted(in_game, key=lambda u: u.login.lower())
    
    # Add in-chat users first
    for user in in_chat:
        user_row = _create_user_row(user, scale, scaled_size, in_game=False)
        users_view.controls.append(user_row)
    
    # Add "Chat" label if there are in-chat users
    if in_chat:
        chat_label = ft.Text(
            "Chat",
            size=10,
            color=ft.Colors.GREY_400,
            weight=ft.FontWeight.BOLD
        )
        users_view.controls.insert(0, chat_label)
    
    # Add "Game" label before in-game users
    if in_game:
        game_label = ft.Text(
            "Game",
            size=10,
            color=ft.Colors.GREY_400,
            weight=ft.FontWeight.BOLD
        )
        users_view.controls.append(game_label)
    
    # Add in-game users
    for user in in_game:
        user_row = _create_user_row(user, scale, scaled_size, in_game=True)
        users_view.controls.append(user_row)


def _create_user_row(user, scale, scaled_size, in_game=False):
    """Create a user row widget."""
    user_widgets = []
    
    # Add avatar if available
    if hasattr(user, 'get_avatar_url') and user.get_avatar_url():
        try:
            avatar = ft.Image(
                src=user.get_avatar_url(),
                width=int(20 * scale),
                height=int(20 * scale),
                fit=ft.ImageFit.COVER,
                border_radius=ft.border_radius.all(3)
            )
            user_widgets.append(avatar)
        except:
            pass
    
    # Username with color from background
    bg_color = user.background if hasattr(user, 'background') and user.background else None
    
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
    
    if in_game and user.game_id:
        username_text = ft.Text(
            f"{user.login} 🎮#{user.game_id}",
            color=bg_color if bg_color else ft.Colors.BLUE_400
        )
    else:
        username_text = ft.Text(
            user.login,
            color=bg_color if bg_color else None
        )
    username_text._base_size = 11
    username_text.size = scaled_size
    
    user_widgets.append(username_text)
    
    user_row = ft.Row(
        user_widgets,
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    return user_row