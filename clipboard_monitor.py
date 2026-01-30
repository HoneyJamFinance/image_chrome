"""Clipboard monitoring and image extraction."""

import io
import threading
import time
from typing import Callable, Optional

import win32clipboard
import win32con
from PIL import Image
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
            win32clipboard.OpenClipboard()
            try:
                # Check for DIB format (Device Independent Bitmap)
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                    data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                    # Parse DIB data
                    image = self._dib_to_image(data)
                    if image:
                        return image

                # Check for standard bitmap format
                if win32clipboard.IsClipboardFormatAvailable(win32con.CF_BITMAP):
                    # CF_BITMAP is harder to work with, DIB is preferred
                    pass

                # Check for PNG format (some applications use this)
                png_format = win32clipboard.RegisterClipboardFormat("PNG")
                if win32clipboard.IsClipboardFormatAvailable(png_format):
                    data = win32clipboard.GetClipboardData(png_format)
                    return Image.open(io.BytesIO(data))

            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            # Clipboard might be locked by another application
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            print(f"Clipboard access error: {e}")

        return None

    def _dib_to_image(self, dib_data: bytes) -> Optional[Image.Image]:
        """Convert DIB (Device Independent Bitmap) data to PIL Image."""
        try:
            # DIB header structure
            # BITMAPINFOHEADER is 40 bytes
            if len(dib_data) < 40:
                return None

            # Parse BITMAPINFOHEADER
            import struct
            header = dib_data[:40]
            (
                header_size, width, height, planes, bit_count,
                compression, image_size, x_ppm, y_ppm,
                colors_used, colors_important
            ) = struct.unpack('<IiiHHIIiiII', header)

            # Handle negative height (top-down bitmap)
            top_down = height < 0
            height = abs(height)

            # Calculate color table size
            if bit_count <= 8:
                if colors_used == 0:
                    colors_used = 1 << bit_count
                color_table_size = colors_used * 4
            else:
                color_table_size = 0

            # Get pixel data
            pixel_offset = header_size + color_table_size
            pixel_data = dib_data[pixel_offset:]

            # Create BMP file in memory
            # BMP file header (14 bytes) + DIB data
            file_size = 14 + len(dib_data)
            pixel_offset_in_file = 14 + header_size + color_table_size

            bmp_header = struct.pack(
                '<2sIHHI',
                b'BM',
                file_size,
                0,
                0,
                pixel_offset_in_file
            )

            bmp_data = bmp_header + dib_data

            # Open with PIL
            image = Image.open(io.BytesIO(bmp_data))

            # Convert to RGBA for consistency
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            return image

        except Exception as e:
            print(f"DIB conversion error: {e}")
            return None

    def _on_press(self, key):
        """Handle key press events."""
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            elif hasattr(key, 'char') and key.char == 'v' and self.ctrl_pressed:
                self._handle_paste()
        except AttributeError:
            pass

    def _on_release(self, key):
        """Handle key release events."""
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False

    def _handle_paste(self):
        """Handle a paste event (Ctrl+V detected)."""
        # Debounce to prevent multiple triggers
        current_time = time.time()
        if current_time - self._last_paste_time < self._debounce_interval:
            return
        self._last_paste_time = current_time

        # Check clipboard in a separate thread to not block the keyboard listener
        def check_clipboard():
            # Small delay to let the clipboard settle
            time.sleep(0.1)
            image = self._get_clipboard_image()
            if image:
                self.on_image_callback(image)

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
