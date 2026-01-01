"""Desktop notifications using pure Python - no external dependencies."""
import threading
import platform
import subprocess
import ctypes
from ctypes import wintypes


def send_chat_notification(msg, timeout: int = 5) -> bool:
    login = getattr(msg, 'login', 'Unknown')
    body = getattr(msg, 'body', '')
    if len(body) > 200:
        body = body[:200] + "..."
    
    def send():
        system = platform.system()
        
        if system == "Windows":
            _windows_notification(login, body, timeout)
        elif system == "Linux":
            _linux_notification(login, body, timeout)
        elif system == "Darwin":
            _macos_notification(login, body, timeout)
    
    threading.Thread(target=send, daemon=True).start()
    return True


def _windows_notification(login, body, timeout):
    """Windows notification using PowerShell."""
    try:
        script = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)

        $toastXml = [xml] $template.GetXml()
        $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("💬 {login}")) > $null
        $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{body}")) > $null

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($toastXml.OuterXml)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        $toast.Tag = "KGChat"
        $toast.Group = "KGChat"

        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("KG Chat Notification")
        $notifier.Show($toast)
        """
        subprocess.run(
            ["powershell", "-Command", script],
            capture_output=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
    except Exception as e:
        print(f"⚠️ Windows notification error: {e}")


def _linux_notification(login, body, timeout):
    """Linux notification using notify-send."""
    try:
        subprocess.run([
            'notify-send',
            '-a', 'KG Chat Notification',
            '-t', str(timeout * 1000),
            '-u', 'normal',
            f'💬 {login}',
            body
        ], timeout=1)
    except Exception as e:
        print(f"⚠️ Linux notification error: {e}")


def _macos_notification(login, body, timeout):
    """macOS notification using osascript."""
    try:
        body_escaped = body.replace('"', '\\"').replace("'", "\\'")
        script = f'display notification "{body_escaped}" with title "💬 {login}" subtitle "KG Chat Notification"'
        subprocess.run(['osascript', '-e', script], timeout=1)
    except Exception as e:
        print(f"⚠️ macOS notification error: {e}")