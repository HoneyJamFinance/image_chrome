"""Shortcut recording dialog."""

import tkinter as tk
from tkinter import ttk
from pynput import keyboard

from config import get_shortcut, set_shortcut, shortcut_to_string


class ShortcutDialog:
    """Dialog for recording a new keyboard shortcut."""

    def __init__(self, on_shortcut_changed: callable = None):
        self.on_shortcut_changed = on_shortcut_changed
        self.recording = False
        self.modifiers = set()
        self.key = None
        self.listener = None

    def show(self):
        """Show the shortcut dialog."""
        self.root = tk.Tk()
        self.root.title("Set Shortcut")
        self.root.geometry("350x180")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)

        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 350) // 2
        y = (self.root.winfo_screenheight() - 180) // 2
        self.root.geometry(f"+{x}+{y}")

        # Current shortcut
        current = get_shortcut()
        current_str = shortcut_to_string(current)

        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Current shortcut:").pack()
        self.current_label = ttk.Label(frame, text=current_str, font=('Segoe UI', 12, 'bold'))
        self.current_label.pack(pady=(0, 15))

        ttk.Label(frame, text="Press your new shortcut:").pack()
        self.shortcut_label = ttk.Label(frame, text="Click 'Record' then press keys",
                                         font=('Segoe UI', 11))
        self.shortcut_label.pack(pady=(5, 15))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()

        self.record_btn = ttk.Button(btn_frame, text="Record", command=self.toggle_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = ttk.Button(btn_frame, text="Save", command=self.save_shortcut, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Cancel", command=self.close).pack(side=tk.LEFT, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

    def toggle_recording(self):
        """Start or stop recording."""
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Start listening for key presses."""
        self.recording = True
        self.modifiers = set()
        self.key = None
        self.record_btn.config(text="Stop")
        self.shortcut_label.config(text="Press keys now...")
        self.save_btn.config(state=tk.DISABLED)

        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()

    def stop_recording(self):
        """Stop listening for key presses."""
        self.recording = False
        self.record_btn.config(text="Record")
        if self.listener:
            self.listener.stop()
            self.listener = None

    def _on_key_press(self, key):
        """Handle key press during recording."""
        if not self.recording:
            return

        # Check for modifier keys
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.modifiers.add('ctrl')
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or key == keyboard.Key.alt_gr:
            self.modifiers.add('alt')
        elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.modifiers.add('shift')
        else:
            # This is the trigger key
            if hasattr(key, 'char') and key.char:
                self.key = key.char.lower()
            elif hasattr(key, 'name') and key.name:
                self.key = key.name.lower()
            elif hasattr(key, 'vk'):
                # Try to convert vk code to character
                vk = key.vk
                if 0x41 <= vk <= 0x5A:  # A-Z
                    self.key = chr(vk).lower()
                elif 0x30 <= vk <= 0x39:  # 0-9
                    self.key = chr(vk)
                elif 0x70 <= vk <= 0x7B:  # F1-F12
                    self.key = f"f{vk - 0x6F}"

        self._update_display()

    def _on_key_release(self, key):
        """Handle key release during recording."""
        if not self.recording:
            return

        # If we have modifiers and a key, we're done
        if self.modifiers and self.key:
            self.stop_recording()
            self.save_btn.config(state=tk.NORMAL)

    def _update_display(self):
        """Update the shortcut display."""
        parts = [mod.capitalize() for mod in sorted(self.modifiers)]
        if self.key:
            parts.append(self.key.upper())

        if parts:
            self.shortcut_label.config(text='+'.join(parts))
            self.root.update()

    def save_shortcut(self):
        """Save the recorded shortcut."""
        if self.modifiers and self.key:
            set_shortcut(list(self.modifiers), self.key)
            if self.on_shortcut_changed:
                self.on_shortcut_changed()
            self.close()

    def close(self):
        """Close the dialog."""
        self.stop_recording()
        self.root.destroy()


def show_shortcut_dialog(on_shortcut_changed: callable = None):
    """Show the shortcut dialog in a thread-safe way."""
    dialog = ShortcutDialog(on_shortcut_changed)
    dialog.show()
