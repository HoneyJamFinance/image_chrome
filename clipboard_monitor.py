"""Clipboard monitoring and image extraction."""

import threading
import time
from typing import Callable, Optional

from PIL import Image, ImageGrab
from pynput import keyboard

from config import get_shortcut

# Virtual key codes for common keys
VK_CODES = {
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
    'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
    'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
    's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
    'y': 0x59, 'z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B,
}


class ClipboardMonitor:
    """Monitors for configurable hotkey and extracts clipboard images."""

    def __init__(self, on_image_callback: Callable[[Image.Image], None]):
        """
        Initialize the clipboard monitor.

        Args:
            on_image_callback: Function to call when an image is detected.
        """
        self.on_image_callback = on_image_callback
        self.listener: Optional[keyboard.Listener] = None
        self.running = False
        self._last_paste_time = 0
        self._debounce_interval = 0.5  # Minimum seconds between paste detections

        # Track modifier states
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.shift_pressed = False

        # Load shortcut config
        self.reload_shortcut()

    def reload_shortcut(self):
        """Reload shortcut configuration."""
        shortcut = get_shortcut()
        self.required_modifiers = set(shortcut.get('modifiers', ['ctrl']))
        self.trigger_key = shortcut.get('key', 'v').lower()
        self.trigger_vk = VK_CODES.get(self.trigger_key)
        print(f"[DEBUG] Shortcut loaded: {'+'.join(self.required_modifiers)}+{self.trigger_key.upper()}")

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

    def _check_modifiers_match(self) -> bool:
        """Check if current modifier state matches required modifiers."""
        current_modifiers = set()
        if self.ctrl_pressed:
            current_modifiers.add('ctrl')
        if self.alt_pressed:
            current_modifiers.add('alt')
        if self.shift_pressed:
            current_modifiers.add('shift')

        return current_modifiers == self.required_modifiers

    def _is_trigger_key(self, key) -> bool:
        """Check if the pressed key is the trigger key."""
        # Check by character
        if hasattr(key, 'char') and key.char:
            if key.char.lower() == self.trigger_key:
                return True

        # Check by virtual key code
        if hasattr(key, 'vk') and self.trigger_vk:
            if key.vk == self.trigger_vk:
                return True

        # Check for function keys
        if hasattr(key, 'name'):
            if key.name and key.name.lower() == self.trigger_key:
                return True

        return False

    def _on_press(self, key):
        """Handle key press events."""
        try:
            # Track modifier keys
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
                return
            elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr:
                self.alt_pressed = True
                return
            elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                self.shift_pressed = True
                return

            # Check if modifiers match and this is the trigger key
            if self._check_modifiers_match() and self._is_trigger_key(key):
                print(f"[DEBUG] Hotkey detected!")
                self._handle_paste()

        except AttributeError as e:
            print(f"[DEBUG] Key error: {e}")

    def _on_release(self, key):
        """Handle key release events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr:
            self.alt_pressed = False
        elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = False

    def _handle_paste(self):
        """Handle a hotkey event."""
        # Debounce to prevent multiple triggers
        current_time = time.time()
        if current_time - self._last_paste_time < self._debounce_interval:
            print("[DEBUG] Debounced - too soon after last trigger")
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
