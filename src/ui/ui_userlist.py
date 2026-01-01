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

    # Prepare per-user counters so sorting is deterministic
    s = page.data.setdefault('user_game_state', {}) if page is not None else {}
    for u in in_game:
        st = s.get(u.login)
        if not st or st.get('last_game_id') != u.game_id:
            new_counter = 1 if not st else (st.get('counter', 0) + 1)
            if page is not None:
                s[u.login] = {'last_game_id': u.game_id, 'counter': new_counter}

    # Sort: chat alphabetically, game by counter desc then login
    in_chat = sorted(in_chat, key=lambda u: u.login.lower())
    in_game = sorted(in_game, key=lambda u: (-(s.get(u.login, {}).get('counter', 0)), u.login.lower()))
    
    # Add in-chat users first
    for user in in_chat:
        user_row = _create_user_row(user, scale, scaled_size, in_game=False, page=page)
        users_view.controls.append(user_row)
    
    # Add "Chat" label if there are in-chat users
    if in_chat:
        chat_label = ft.Text(
            "🗯️ Chat",
            size=16,
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.BOLD
        )
        users_view.controls.insert(0, chat_label)
    
    # Add gap and "Game" label before in-game users
    if in_game:
        if in_chat:
            users_view.controls.append(ft.Container(height=12))
        game_label = ft.Text(
            "🏁 Game",
            size=16,
            color=ft.Colors.GREY_700,
            weight=ft.FontWeight.BOLD
        )
        users_view.controls.append(game_label)
    
    # Add in-game users
    for user in in_game:
        user_row = _create_user_row(user, scale, scaled_size, in_game=True, page=page)
        users_view.controls.append(user_row)


def _create_user_row(user, scale, scaled_size, in_game=False, page=None):
    """Create a row for a single user with avatar and username."""
    user_widgets = []

    # Add avatar if available - use the existing get_avatar_url() method
    avatar_url = None
    if hasattr(user, 'get_avatar_url'):
        try:
            avatar_url = user.get_avatar_url()
        except Exception as e:
            print(f"Error getting avatar URL for {user.login}: {e}")
    
    if avatar_url:
        try:
            # Create image without ImageFit (compatible with older Flet)
            avatar = ft.Image(
                src=avatar_url,
                width=int(20 * scale),
                height=int(20 * scale),
                border_radius=ft.border_radius.all(4)
            )
            user_widgets.append(avatar)
        except Exception as e:
            print(f"Error creating avatar image for {user.login}: {e}")
            # Fallback to person icon - same size as avatar
            fallback = ft.Icon(ft.Icons.PERSON, size=int(20 * scale), color=ft.Colors.GREY_500)
            user_widgets.append(fallback)
    else:
        # No avatar, show person icon - same size as avatar
        fallback = ft.Icon(ft.Icons.PERSON, size=int(20 * scale), color=ft.Colors.GREY_500)
        user_widgets.append(fallback)

    # Get and optimize username color
    bg_color = user.background if hasattr(user, 'background') and user.background else None

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

    # Build display name with game counter if applicable
    display_name = user.login
    if in_game and getattr(user, 'game_id', None):
        s = page.data.setdefault('user_game_state', {}) if page is not None else {}
        st = s.get(user.login)
        if not st or st.get('last_game_id') != user.game_id:
            new_counter = 1 if not st else (st.get('counter', 0) + 1)
            if page is not None:
                s[user.login] = {'last_game_id': user.game_id, 'counter': new_counter}
        else:
            new_counter = st.get('counter', 1)
        display_name = f"{user.login} 🚦{new_counter}"
    else:
        # Clear game state when user returns to chat
        if page is not None and 'user_game_state' in page.data and user.login in page.data['user_game_state']:
            page.data['user_game_state'].pop(user.login, None)

    # Create username text with color
    username_text = ft.Text(display_name, color=bg_color if bg_color else None)
    username_text._base_size = 11
    username_text.size = scaled_size
    user_widgets.append(username_text)

    # Combine in a row
    user_row = ft.Row(
        user_widgets, 
        spacing=6,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    return user_row