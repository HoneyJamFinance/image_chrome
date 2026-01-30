"""Clipboard monitoring and image extraction."""

import threading
import time
from typing import Callable, Optional

from PIL import Image, ImageGrab
from pynput import keyboard


class ClipboardMonitor:
    """Monitors for Ctrl+V and extracts clipboard images."""

    def __init__(self, on_image_callback: Callable[[Image.Image], None]):
        """
        Initialize the clipboard monitor.

        Args:
            on_image_callback: Function to call when an image is detected.
        """
        self.on_image_callback = on_image_callback
        self.ctrl_pressed = False
        self.listener: Optional[keyboard.Listener] = None
        self.running = False
        self._last_paste_time = 0
        self._debounce_interval = 0.5  # Minimum seconds between paste detections

    def _get_clipboard_image(self) -> Optional[Image.Image]:
        """Extract image from clipboard if available."""
        try:
            # Use PIL's ImageGrab which handles Windows clipboard reliably
            print("[DEBUG] Checking clipboard with ImageGrab...")
            image = ImageGrab.grabclipboard()

            if image is None:
                print("[DEBUG] No image in clipboard")
                return None

            if isinstance(image, Image.Image):
                print(f"[DEBUG] Got image: {image.size}, mode={image.mode}")
                # Convert to RGB if needed (removes alpha issues)
                if image.mode == 'RGBA':
                    # Keep RGBA for transparency support
                    return image
                elif image.mode != 'RGB':
                    return image.convert('RGB')
                return image
            elif isinstance(image, list):
                # ImageGrab returns list of file paths if files were copied
                print(f"[DEBUG] Clipboard contains files, not image: {image}")
                return None
            else:
                print(f"[DEBUG] Unexpected clipboard content type: {type(image)}")
                return None

        except Exception as e:
            print(f"[DEBUG] Clipboard access error: {e}")
            return None

    def _on_press(self, key):
        """Handle key press events."""
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
                print("[DEBUG] Ctrl pressed")
            else:
                # Debug: show what key we got
                if self.ctrl_pressed:
                    key_char = getattr(key, 'char', None)
                    key_vk = getattr(key, 'vk', None)
                    print(f"[DEBUG] Key while Ctrl held: char={key_char}, vk={key_vk}, key={key}")

                # Check for 'V' key - can be char or vk code
                is_v = False
                if hasattr(key, 'char') and key.char and key.char.lower() == 'v':
                    is_v = True
                elif hasattr(key, 'vk') and key.vk == 0x56:  # 0x56 is 'V'
                    is_v = True

                if is_v and self.ctrl_pressed:
                    print("[DEBUG] Ctrl+V detected!")
                    self._handle_paste()
        except AttributeError as e:
            print(f"[DEBUG] Key error: {e}")

    def _on_release(self, key):
        """Handle key release events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False

    def _handle_paste(self):
        """Handle a paste event (Ctrl+V detected)."""
        # Debounce to prevent multiple triggers
        current_time = time.time()
        if current_time - self._last_paste_time < self._debounce_interval:
            print("[DEBUG] Debounced - too soon after last paste")
            return
        self._last_paste_time = current_time

        # Check clipboard in a separate thread to not block the keyboard listener
        def check_clipboard():
            # Small delay to let the clipboard settle
            time.sleep(0.1)
            print("[DEBUG] Checking clipboard for image...")
            image = self._get_clipboard_image()
            if image:
                print(f"[DEBUG] Image found! Size: {image.size}")
                self.on_image_callback(image)
            else:
                print("[DEBUG] No image in clipboard")

        thread = threading.Thread(target=check_clipboard, daemon=True)
        thread.start()

    def start(self):
        """Start monitoring for clipboard images."""
        if self.running:
            return

        self.running = True
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.listener:
            self.listener.stop()
            self.listener = None
