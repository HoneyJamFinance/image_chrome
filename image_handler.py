"""Image saving and Chrome display handling."""

import base64
import io
import os
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from PIL import Image

from config import get_save_folder


def generate_filename() -> str:
    """Generate a timestamp-based filename."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S") + ".png"


def save_image(image: Image.Image) -> Path:
    """Save the image to a date-based subfolder and return the path."""
    base_folder = get_save_folder()

    # Create date-based subfolder (YYYY-MM-DD)
    today = datetime.now().strftime("%Y-%m-%d")
    folder = base_folder / today
    folder.mkdir(parents=True, exist_ok=True)

    filename = generate_filename()
    filepath = folder / filename

    # Handle filename collision (unlikely but possible)
    counter = 1
    while filepath.exists():
        base = filename.rsplit('.', 1)[0]
        filepath = folder / f"{base}_{counter}.png"
        counter += 1

    image.save(filepath, 'PNG')
    return filepath


def create_html_viewer(image_path: Path) -> Path:
    """Create a temporary HTML file to display the image."""
    # Read image and convert to base64 for embedding
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Clipboard Image - {image_path.name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background-color: #1a1a1a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 40px 20px 20px 20px;
        }}
        img {{
            max-width: 100%;
            max-height: 95vh;
            object-fit: contain;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        }}
        .info {{
            position: fixed;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            color: #888;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 12px;
            background: rgba(0, 0, 0, 0.7);
            padding: 5px 15px;
            border-radius: 15px;
        }}
    </style>
</head>
<body>
    <img src="data:image/png;base64,{image_data}" alt="Clipboard Image">
    <div class="info">Saved: {image_path}</div>
</body>
</html>'''

    # Create temp file that won't be auto-deleted
    temp_dir = tempfile.gettempdir()
    html_path = Path(temp_dir) / f"clipboard_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return html_path


def open_in_chrome(html_path: Path) -> None:
    """Open the HTML file in Chrome."""
    # Common Chrome installation paths on Windows
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]

    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break

    if chrome_exe:
        # Open in new tab (no --new-window flag)
        subprocess.Popen([chrome_exe, str(html_path)])
    else:
        # Fall back to default browser
        os.startfile(str(html_path))


def cleanup_temp_html(html_path: Path, delay: float = 30.0) -> None:
    """Clean up the temporary HTML file after a delay."""
    def delete_file():
        time.sleep(delay)
        try:
            if html_path.exists():
                html_path.unlink()
        except Exception:
            pass  # Ignore cleanup errors

    thread = threading.Thread(target=delete_file, daemon=True)
    thread.start()


def handle_clipboard_image(image: Image.Image) -> Path:
    """
    Handle a clipboard image: save it and open in Chrome.
    Returns the path where the image was saved.
    """
    # Save the image
    saved_path = save_image(image)

    # Create HTML viewer and open in Chrome
    html_path = create_html_viewer(saved_path)
    open_in_chrome(html_path)

    # Schedule cleanup of temp HTML
    cleanup_temp_html(html_path, delay=60.0)

    return saved_path
