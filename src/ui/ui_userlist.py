"""User list display UI for the chat."""
import flet as ft


def build_userlist_ui(page):
    """Build and return the user list view.
    
    Returns:
        (users_container, users_view)
    """
    scale = page.data.get('scale', 100) / 100.0
    
    users_view = ft.ListView(
        expand=True,
        spacing=4,
        padding=ft.padding.all(5)
    )
    
    header = ft.Text(
        "Online Users",
        size=int(12 * scale),
        weight=ft.FontWeight.BOLD
    )
    
    users_container = ft.Column(
        [header, ft.Divider(height=1), users_view],
        width=int(220 * scale),
        spacing=4
    )
    
    return users_container, users_view


def rebuild_userlist(users_view, users_list, page):
    """Rebuild the entire user list from a ChatUser list.
    
    Args:
        users_view: ListView for users
        users_list: list of core.userlist.ChatUser objects
        page: Page object for scaling
    """
    scale = page.data.get('scale', 100) / 100.0
    base_size = 11
    scaled_size = base_size * scale
    
    users_view.controls.clear()
    
    # Filter only online users
    online_users = [u for u in users_list if u.status == 'available']
    
    # Sort by login
    sorted_users = sorted(online_users, key=lambda u: u.login.lower())
    
    for user in sorted_users:
        user_widgets = []
        
        # Add avatar if available
        if hasattr(user, 'get_avatar_url') and user.get_avatar_url():
            try:
                avatar = ft.Image(
                    src=user.get_avatar_url(),
                    width=int(24 * scale),
                    height=int(24 * scale),
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(4)
                )
                user_widgets.append(avatar)
            except:
                pass
        
        # Username with game status
        if user.game_id:
            username_text = ft.Text(
                f"{user.login} 🎮#{user.game_id}",
                size=scaled_size,
                italic=True,
                color=ft.colors.BLUE_400
            )
        else:
            username_text = ft.Text(
                user.login,
                size=scaled_size
            )
        
        user_widgets.append(username_text)
        
        user_row = ft.Row(
            user_widgets,
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        users_view.controls.append(user_row)