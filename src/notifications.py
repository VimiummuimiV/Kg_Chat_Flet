"""Desktop notification wrapper using the `desktop-notifier` package.

Provides `send_chat_notification(msg, reply_callback=None, timeout=60)`.
If `desktop-notifier` is not available, functions will print a hint and return False.
Reply support uses `ReplyField` when available; callbacks run in a background thread
and should be non-blocking.
"""
from typing import Optional, Callable
import threading
import asyncio

try:
    from desktop_notifier import DesktopNotifier, ReplyField
    _DN_AVAILABLE = True
except Exception:
    DesktopNotifier = None
    ReplyField = None
    _DN_AVAILABLE = False


def send_chat_notification(msg, reply_callback: Optional[Callable[[str], None]] = None, timeout: int = 5) -> bool:
    """Send a chat notification for a Message-like object.

    msg: object with .login and .body attributes
    reply_callback: function(text) to call when user replies from the notification
    timeout: seconds to keep the notifier loop alive to process reply
    """
    if not _DN_AVAILABLE:
        print("🔕 desktop-notifier not available; install with: pip install desktop-notifier")
        return False

    login = getattr(msg, 'login', 'Unknown')
    body = getattr(msg, 'body', '')

    async def _send_and_wait():
        try:
            notifier = DesktopNotifier(app_name='KG Chat')
        except Exception as e:
            print(f"desktop-notifier init failed: {e}")
            return

        kwargs = {
            'title': login,
            'message': body,
        }

        if ReplyField is not None and reply_callback is not None:
            def _on_replied(text: str):
                try:
                    threading.Thread(target=lambda: reply_callback(text), daemon=True).start()
                except Exception as e:
                    print(f"reply callback error: {e}")

            kwargs['reply_field'] = ReplyField(on_replied=_on_replied)

        try:
            await notifier.send(**kwargs)
        except Exception as e:
            print(f"desktop-notifier send failed: {e}")
            return

        # Keep loop alive to handle reply callbacks for a short while
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            pass

    def _runner():
        try:
            asyncio.run(_send_and_wait())
        except Exception as e:
            print(f"desktop-notifier runner error: {e}")

    threading.Thread(target=_runner, daemon=True).start()
    return True
