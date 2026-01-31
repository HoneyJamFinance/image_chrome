"""Configuration management for Clipboard Image Viewer."""

import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    """Get the application config directory."""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    config_dir = Path(appdata) / 'ClipboardImageViewer'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_config_dir() / 'config.json'


def get_default_save_folder() -> Path:
    """Get the default save folder path."""
    documents = Path.home() / 'Documents' / 'ClipboardImages'
    return documents


def get_default_shortcut() -> dict:
    """Get the default shortcut configuration."""
    return {
        'modifiers': ['ctrl'],  # ctrl, alt, shift
        'key': 'v'
    }


def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    default_config = {
        'save_folder': str(get_default_save_folder()),
        'auto_start_enabled': False,
        'shortcut': get_default_shortcut()
    }

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (json.JSONDecodeError, IOError):
            pass

    return default_config


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def get_save_folder() -> Path:
    """Get the configured save folder, creating it if necessary."""
    config = load_config()
    folder = Path(config['save_folder'])
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def set_save_folder(folder: str) -> None:
    """Set the save folder in configuration."""
    config = load_config()
    config['save_folder'] = folder
    save_config(config)


def is_auto_start_enabled() -> bool:
    """Check if auto-start is enabled in config."""
    config = load_config()
    return config.get('auto_start_enabled', False)


def set_auto_start_enabled(enabled: bool) -> None:
    """Set auto-start enabled state in config."""
    config = load_config()
    config['auto_start_enabled'] = enabled
    save_config(config)


def get_shortcut() -> dict:
    """Get the configured shortcut."""
    config = load_config()
    return config.get('shortcut', get_default_shortcut())


def set_shortcut(modifiers: list, key: str) -> None:
    """Set the shortcut in configuration."""
    config = load_config()
    config['shortcut'] = {
        'modifiers': modifiers,
        'key': key
    }
    save_config(config)


def shortcut_to_string(shortcut: dict) -> str:
    """Convert shortcut dict to display string."""
    parts = [mod.capitalize() for mod in shortcut.get('modifiers', [])]
    key = shortcut.get('key', '').upper()
    if key:
        parts.append(key)
    return '+'.join(parts)
