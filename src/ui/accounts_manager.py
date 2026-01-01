"""Welcome screen UI for account selection and management."""
from pathlib import Path
from typing import List

import flet as ft
from flet import Page, Text, Row, Column, Dropdown, TextField, ElevatedButton, SnackBar

from core.accounts import AccountManager


LAST_ACCOUNT_FILE = Path.home() / ".kg_chat_last_account"


def load_last_account() -> str:
    """Load last selected account login."""
    try:
        with open(LAST_ACCOUNT_FILE, "r") as f:
            return f.read().strip()
    except:
        return None


def save_last_account(login: str):
    """Save last selected account login."""
    try:
        with open(LAST_ACCOUNT_FILE, "w") as f:
            f.write(login)
    except:
        pass


def build_welcome(page: Page, on_connect_callback=None):
    """Build and display the welcome/account management screen."""
    page.title = "KG Chat - Welcome"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 20

    cfg_path = str(Path(__file__).parent.parent / "config.json")
    acct_mgr = AccountManager(cfg_path)

    # Helper: show a SnackBar notification
    def notify(msg: str, duration: int = 2000):
        page.snack_bar = SnackBar(Text(msg), open=True, duration=duration)
        page.update()

    # Build dropdown options from accounts
    def make_options() -> List[ft.dropdown.Option]:
        opts = []
        for acc in acct_mgr.list_accounts():
            label = acc['login']
            opts.append(ft.dropdown.Option(key=acc['login'], text=label))
        return opts

    account_dd = Dropdown(
        options=make_options(),
        value=None,
        width=280,
        label="Select Account"
    )

    connect_btn = ElevatedButton("Connect")
    remove_btn = ElevatedButton("Remove")

    userid_field = TextField(label="User ID", width=120)
    login_field = TextField(label="Username", width=150)
    password_field = TextField(label="Password", password=True, width=150)
    add_btn = ElevatedButton("Add")

    # Refresh dropdown and restore last selection
    def refresh_dd():
        opts = make_options()
        account_dd.options = opts
        
        if opts:
            # Try to restore last selected account
            last_account = load_last_account()
            if last_account and any(opt.key == last_account for opt in opts):
                account_dd.value = last_account
            else:
                # Default to first account
                account_dd.value = opts[0].key
        else:
            account_dd.value = None
        
        page.update()

    refresh_dd()

    def on_add(e):
        userid = (userid_field.value or "").strip()
        login = (login_field.value or "").strip()
        pwd = (password_field.value or "").strip()
        if not login or not pwd:
            notify("Provide username and password")
            return
        if not userid:
            userid = login
        ok = acct_mgr.add_account(user_id=userid, login=login, password=pwd)
        notify("Account added" if ok else "Account already exists")
        if ok:
            userid_field.value = ""
            login_field.value = ""
            password_field.value = ""
        refresh_dd()

    def on_remove(e):
        val = account_dd.value
        if not val:
            notify("No account selected")
            return
        ok = acct_mgr.remove_account(val)
        notify("Account removed" if ok else "Account not found")
        refresh_dd()

    def on_connect(e):
        val = account_dd.value
        if not val:
            notify("Select an account to connect")
            return
        account = acct_mgr.get_account_by_login(val)
        if not account:
            notify("Account not found")
            return
        
        # Save last selected account
        save_last_account(val)
        
        notify(f"Connecting as {val}...", duration=1000)
        if on_connect_callback:
            on_connect_callback(val, account)

    add_btn.on_click = on_add
    remove_btn.on_click = on_remove
    connect_btn.on_click = on_connect

    header = Text("Welcome to KG Chat", size=28, weight=ft.FontWeight.BOLD)

    controls = Column(
        [
            header,
            ft.Divider(height=20),
            ft.Text("Select or Add Account", size=16, weight=ft.FontWeight.W_500),
            Row(
                [account_dd, connect_btn, remove_btn],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            ),
            ft.Divider(height=20),
            ft.Text("Add New Account", size=16, weight=ft.FontWeight.W_500),
            Row(
                [userid_field, login_field, password_field, add_btn],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            ),
        ],
        spacing=10,
        expand=False,
    )

    page.controls.clear()
    page.add(controls)
    page.update()