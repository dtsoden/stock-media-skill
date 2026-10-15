"""Load the Pexels and Pixabay API keys without ever printing them.

Lookup order for each key:
  1. Environment variable (PEXELS_API_KEY / PIXABAY_API_KEY). This also covers
     keys injected by a vault runner such as `aihsm run`.
  2. The OS credential store through the `keyring` package (Windows Credential
     Manager, macOS Keychain, Linux Secret Service), service "stock-media",
     usernames "pexels" and "pixabay".
"""
import json
import os
import sys

SERVICES = {'pexels': 'PEXELS_API_KEY', 'pixabay': 'PIXABAY_API_KEY'}
KEYRING_SERVICE = 'stock-media'
# Kept outside the skill folder so it survives reinstalls and is shared by
# every agent that has the skill installed.
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.config', 'stock-media', 'config.json')


def load_config():
    try:
        with open(CONFIG_PATH, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def get_key(service):
    env_name = SERVICES[service]
    value = os.environ.get(env_name)
    if value:
        return value.strip()
    try:
        import keyring
        value = keyring.get_password(KEYRING_SERVICE, service)
        if value:
            return value.strip()
    except Exception:
        pass
    store = load_config().get('store', 'not set up')
    sys.exit(f'No {service} key found (key store: {store}). '
             f'Set {env_name}, or run the stock-media setup again.')
