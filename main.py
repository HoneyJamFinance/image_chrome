"""
Clipboard Image Viewer - Main Entry Point

A Windows application that monitors Ctrl+V, displays clipboard images in Chrome,
and saves them to a user-configured folder.
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from PIL import Image
import pystray

from clipboard_monitor import ClipboardMonitor
from image_handler import handle_clipboard_image
from config import (
    load_config, get_save_folder, set_save_folder,
    is_auto_start_enabled, set_auto_start_enabled,
    get_shortcut, shortcut_to_string
)
from autostart import enable_auto_start, disable_auto_start, is_auto_start_registered
from shortcut_dialog import show_shortcut_dialog


class ClipboardImageViewer:
    """Main application class."""

    def __init__(self):
        self.monitor: ClipboardMonitor = None
        self.tray_icon: pystray.Icon = None
        self.running = False

    def on_clipboard_image(self, image: Image.Image):
        """Callback when a clipboard image is detected."""
        try:
            saved_path = handle_clipboard_image(image)
            print(f"Image saved: {saved_path}")
        except Exception as e:
            print(f"Error handling image: {e}")

    def change_save_folder(self, icon=None, item=None):
        """Open folder picker to change save location."""
        # Need to run tkinter in the main thread context
        def pick_folder():
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)  # Bring dialog to front

            current_folder = str(get_save_folder())
            folder = filedialog.askdirectory(
                initialdir=current_folder,
                title="Select Save Folder for Clipboard Images"
            )

            root.destroy()

            if folder:
                set_save_folder(folder)
                print(f"Save folder changed to: {folder}")

        # Run in a thread to avoid blocking
        thread = threading.Thread(target=pick_folder)
        thread.start()

    def open_save_folder(self, icon=None, item=None):
        """Open the save folder in Windows Explorer."""
        folder = get_save_folder()
        os.startfile(str(folder))

    def change_shortcut(self, icon=None, item=None):
        """Open dialog to change the keyboard shortcut."""
        def on_shortcut_changed():
            # Reload shortcut in the monitor
            if self.monitor:
                self.monitor.reload_shortcut()
            # Update menu to show new shortcut
            self.update_menu()
            print(f"Shortcut changed to: {shortcut_to_string(get_shortcut())}")

        # Run in a thread to avoid blocking
        thread = threading.Thread(target=lambda: show_shortcut_dialog(on_shortcut_changed))
        thread.start()

    def get_shortcut_text(self):
        """Get the text for the shortcut menu item."""
        shortcut = get_shortcut()
        return f"Shortcut: {shortcut_to_string(shortcut)}"

    def toggle_auto_start(self, icon=None, item=None):
        """Toggle Windows auto-start."""
        if is_auto_start_registered():
            disable_auto_start()
            set_auto_start_enabled(False)
            print("Auto-start disabled")
        else:
            enable_auto_start()
            set_auto_start_enabled(True)
            print("Auto-start enabled")

        # Update the menu to reflect new state
        self.update_menu()

    def get_auto_start_text(self):
        """Get the text for the auto-start menu item."""
        if is_auto_start_registered():
            return "Auto-start: On"
        return "Auto-start: Off"

    def update_menu(self):
        """Update the system tray menu."""
        if self.tray_icon:
            self.tray_icon.menu = self.create_menu()

    def create_menu(self):
        """Create the system tray menu."""
        return pystray.Menu(
            pystray.MenuItem(self.get_shortcut_text(), self.change_shortcut),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Change Save Folder", self.change_save_folder),
            pystray.MenuItem("Open Save Folder", self.open_save_folder),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                self.get_auto_start_text(),
                self.toggle_auto_start
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.exit_app)
        )

    def exit_app(self, icon=None, item=None):
        """Exit the application."""
        print("Exiting Clipboard Image Viewer...")
        self.running = False

        if self.monitor:
            self.monitor.stop()

        if self.tray_icon:
            self.tray_icon.stop()

    def create_default_icon(self) -> Image.Image:
        """Create a simple default icon."""
        # Create a 64x64 icon with a simple clipboard/image design
        size = 64
        icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))

        # Draw a simple clipboard shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(icon)

        # Background rounded rectangle (clipboard)
        draw.rounded_rectangle(
            [8, 4, 56, 60],
            radius=6,
            fill=(70, 130, 180),  # Steel blue
            outline=(50, 100, 150),
            width=2
        )

        # Clipboard clip at top
        draw.rounded_rectangle(
            [22, 0, 42, 12],
            radius=3,
            fill=(100, 160, 210),
            outline=(50, 100, 150),
            width=2
        )

        # Image icon in center (simple mountain/sun)
        draw.rectangle([16, 20, 48, 48], fill=(255, 255, 255), outline=(200, 200, 200))

        # Sun
        draw.ellipse([36, 24, 44, 32], fill=(255, 200, 50))

        # Mountains
        draw.polygon([(18, 46), (28, 32), (38, 46)], fill=(100, 180, 100))
        draw.polygon([(30, 46), (40, 36), (46, 46)], fill=(80, 150, 80))

        return icon

    def load_icon(self) -> Image.Image:
        """Load the system tray icon."""
        # Try to load custom icon
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            try:
                return Image.open(icon_path)
            except Exception:
                pass

        # Fall back to generated icon
        return self.create_default_icon()

    def check_first_run(self):
        """Check if this is the first run and prompt for folder selection."""
        config = load_config()
        config_path = Path(os.environ.get('APPDATA', os.path.expanduser('~'))) / 'ClipboardImageViewer' / 'config.json'

        # If config file doesn't exist, this is first run
        if not config_path.exists():
            print("First run detected - prompting for save folder...")
            # Show folder picker
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            folder = filedialog.askdirectory(
                initialdir=str(Path.home() / "Documents"),
                title="Select Save Folder for Clipboard Images (First Run Setup)"
            )

            root.destroy()

            if folder:
                set_save_folder(folder)
                print(f"Save folder set to: {folder}")
            else:
                # Use default
                default = get_save_folder()
                print(f"Using default save folder: {default}")

    def run(self):
        """Run the application."""
        print("Starting Clipboard Image Viewer...")

        # Check first run
        self.check_first_run()

        # Ensure save folder exists
        folder = get_save_folder()
        print(f"Save folder: {folder}")

        # Start clipboard monitor
        self.monitor = ClipboardMonitor(self.on_clipboard_image)
        self.monitor.start()
        print("Clipboard monitor started")

        # Create and run system tray icon
        self.running = True
        icon_image = self.load_icon()

        self.tray_icon = pystray.Icon(
            "ClipboardImageViewer",
            icon_image,
            "Clipboard Image Viewer",
            menu=self.create_menu()
        )

        print("System tray icon created - right-click to access menu")
        shortcut_str = shortcut_to_string(get_shortcut())
        print(f"Press {shortcut_str} with an image in clipboard to save and view it")

        # This blocks until the icon is stopped
        self.tray_icon.run()


def main():
    """Main entry point."""
    app = ClipboardImageViewer()
    try:
        app.run()
    except KeyboardInterrupt:
        app.exit_app()
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
