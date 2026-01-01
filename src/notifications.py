"""Custom desktop notification system with cursor/keyboard detection.

Provides `send_chat_notification(msg, reply_callback=None, timeout=10)`.
Works on Windows, Linux, and macOS with native notification APIs.
"""

from typing import Optional, Callable
import threading
import time
import sys
import platform

try:
    from pynput import mouse, keyboard
    _PYNPUT_AVAILABLE = True
except Exception:
    _PYNPUT_AVAILABLE = False


def send_chat_notification(msg, timeout: int = 10, wait_for_input: bool = True) -> bool:
    """Send a chat notification for a Message-like object.
    
    msg: object with .login and .body attributes
    timeout: seconds to keep notification visible after user input (default: 10)
    wait_for_input: if True, timer only starts when mouse/keyboard activity detected
    """
    login = getattr(msg, 'login', 'Unknown')
    body = getattr(msg, 'body', '')
    
    def notification_thread():
        system = platform.system()
        
        # Show notification immediately with input detection
        if system == "Windows":
            _show_windows_notification(login, body, timeout, wait_for_input)
        elif system == "Linux":
            _show_linux_notification(login, body, timeout, wait_for_input)
        elif system == "Darwin":  # macOS
            _show_macos_notification(login, body, timeout, wait_for_input)
        else:
            print(f"⚠️ Notifications not supported on {system}")
            return False
    
    threading.Thread(target=notification_thread, daemon=True).start()
    return True


def _show_windows_notification(title, message, timeout, wait_for_input):
    """Show Windows 10/11 toast notification"""
    try:
        from winotify import Notification
        
        toast = Notification(
            app_id="KG Chat",
            title=title,
            msg=message,
            duration="long",
            icon=""
        )
        
        toast.show()
        
        # Wait for input before starting hide timer
        if wait_for_input and _PYNPUT_AVAILABLE:
            input_detected = threading.Event()
            
            def on_move(x, y):
                input_detected.set()
                return False
            
            def on_key(key):
                input_detected.set()
                return False
            
            mouse_listener = mouse.Listener(on_move=on_move)
            keyboard_listener = keyboard.Listener(on_press=on_key)
            
            mouse_listener.start()
            keyboard_listener.start()
            
            input_detected.wait()
            
            mouse_listener.stop()
            keyboard_listener.stop()
        
        # Now sleep for the timeout duration
        time.sleep(timeout)
        
    except ImportError:
        # Fallback to win10toast
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            
            # win10toast blocks until dismissed, so we handle timing differently
            if wait_for_input and _PYNPUT_AVAILABLE:
                # Start notification in background
                notification_thread = threading.Thread(
                    target=lambda: toaster.show_toast(title, message, duration=999, threaded=False),
                    daemon=True
                )
                notification_thread.start()
                
                # Wait for input
                input_detected = threading.Event()
                
                def on_move(x, y):
                    input_detected.set()
                    return False
                
                def on_key(key):
                    input_detected.set()
                    return False
                
                mouse_listener = mouse.Listener(on_move=on_move)
                keyboard_listener = keyboard.Listener(on_press=on_key)
                
                mouse_listener.start()
                keyboard_listener.start()
                
                input_detected.wait()
                
                mouse_listener.stop()
                keyboard_listener.stop()
                
                time.sleep(timeout)
            else:
                toaster.show_toast(title, message, duration=timeout, threaded=False)
                
        except ImportError:
            print("⚠️ Install winotify or win10toast: pip install winotify")


def _show_linux_notification(title, message, timeout, wait_for_input):
    """Show Linux notification using notify-send or dbus"""
    import subprocess
    
    timeout_ms = 999999 if wait_for_input else (timeout * 1000)
    notification_id = None
    
    # Try dbus first for better control
    try:
        import dbus
        bus = dbus.SessionBus()
        notify_obj = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        notify_interface = dbus.Interface(notify_obj, 'org.freedesktop.Notifications')
        
        notification_id = notify_interface.Notify(
            'KG Chat',           # app_name
            0,                   # replaces_id
            '',                  # app_icon
            title,               # summary
            message,             # body
            [],                  # actions
            {'urgency': 1},      # hints
            timeout_ms           # timeout
        )
        
        # Wait for input before starting hide timer
        if wait_for_input and _PYNPUT_AVAILABLE:
            input_detected = threading.Event()
            
            def on_move(x, y):
                input_detected.set()
                return False
            
            def on_key(key):
                input_detected.set()
                return False
            
            mouse_listener = mouse.Listener(on_move=on_move)
            keyboard_listener = keyboard.Listener(on_press=on_key)
            
            mouse_listener.start()
            keyboard_listener.start()
            
            input_detected.wait()
            
            mouse_listener.stop()
            keyboard_listener.stop()
        
        time.sleep(timeout)
        
        # Clear notification
        try:
            notify_interface.CloseNotification(notification_id)
        except:
            pass
            
    except ImportError:
        # Fallback to notify-send
        try:
            subprocess.run([
                'notify-send',
                '-a', 'KG Chat',
                '-t', str(timeout_ms),
                '-u', 'normal',
                title,
                message
            ], check=True, timeout=1)
            
            # Wait for input if needed
            if wait_for_input and _PYNPUT_AVAILABLE:
                input_detected = threading.Event()
                
                def on_move(x, y):
                    input_detected.set()
                    return False
                
                def on_key(key):
                    input_detected.set()
                    return False
                
                mouse_listener = mouse.Listener(on_move=on_move)
                keyboard_listener = keyboard.Listener(on_press=on_key)
                
                mouse_listener.start()
                keyboard_listener.start()
                
                input_detected.wait()
                
                mouse_listener.stop()
                keyboard_listener.stop()
            
            time.sleep(timeout)
            
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️ Install dbus-python: pip install dbus-python")
    except Exception as e:
        print(f"⚠️ Notification error: {e}")


def _show_macos_notification(title, message, timeout, wait_for_input):
    """Show macOS notification using osascript"""
    import subprocess
    
    script = f'''
        display notification "{message}" with title "{title}" sound name "default"
    '''
    
    try:
        subprocess.run(['osascript', '-e', script], check=True, timeout=1)
        
        # Wait for input before starting hide timer
        if wait_for_input and _PYNPUT_AVAILABLE:
            input_detected = threading.Event()
            
            def on_move(x, y):
                input_detected.set()
                return False
            
            def on_key(key):
                input_detected.set()
                return False
            
            mouse_listener = mouse.Listener(on_move=on_move)
            keyboard_listener = keyboard.Listener(on_press=on_key)
            
            mouse_listener.start()
            keyboard_listener.start()
            
            input_detected.wait()
            
            mouse_listener.stop()
            keyboard_listener.stop()
        
        time.sleep(timeout)
        
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"⚠️ macOS notification error: {e}")