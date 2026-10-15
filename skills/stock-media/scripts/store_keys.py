"""Read API keys from a text file, test them, store them, delete the file.

Never prints a key. Usage:
  python store_keys.py --template FILE
      Write a blank key file for the user to fill in.
  python store_keys.py --file FILE --store keyring|env|aihsm
      keyring: save to the OS credential store (service "stock-media")
      env:     save as user environment variables
      aihsm:   record that aihsm holds the keys (the user stores them with
               `aihsm put`); the file is not used and need not exist
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stock_media_keys import CONFIG_PATH, KEYRING_SERVICE, SERVICES  # noqa: E402

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
PLACEHOLDER = 'paste-your-key-here'
TEMPLATE = f"""# Paste each API key after the = sign, save this file, and close it.
# Get a Pexels key at  https://www.pexels.com/api/
# Get a Pixabay key at https://pixabay.com/api/docs/  (shown once you log in)
# This file is deleted as soon as the keys are stored.

PEXELS_API_KEY={PLACEHOLDER}
PIXABAY_API_KEY={PLACEHOLDER}
"""


def parse_file(path):
    keys = {}
    with open(path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'([A-Za-z_ ]+?)\s*[=:]\s*(.+)', line)
            if not m:
                continue
            name, value = m.group(1).lower(), m.group(2).strip().strip('"\'')
            for service in SERVICES:
                if service in name and value and value != PLACEHOLDER:
                    keys[service] = value
    return keys


def test_key(service, key):
    try:
        if service == 'pexels':
            req = urllib.request.Request(
                'https://api.pexels.com/v1/search?query=nature&per_page=1',
                headers={'Authorization': key, 'User-Agent': UA})
        else:
            q = urllib.parse.urlencode({'key': key, 'q': 'nature', 'per_page': 3})
            req = urllib.request.Request('https://pixabay.com/api/?' + q,
                                         headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200, f'HTTP {resp.status}'
    except urllib.error.HTTPError as e:
        return False, f'HTTP {e.code} (key rejected)'
    except Exception as e:
        return False, f'{type(e).__name__} (network problem)'


def store_keyring(keys):
    import keyring
    for service, key in keys.items():
        keyring.set_password(KEYRING_SERVICE, service, key)


def store_env(keys):
    if os.name == 'nt':
        import ctypes
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0,
                            winreg.KEY_SET_VALUE) as reg:
            for service, key in keys.items():
                winreg.SetValueEx(reg, SERVICES[service], 0, winreg.REG_SZ, key)
        # Tell running programs the environment changed.
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, 'Environment',
                                                 2, 5000, None)
        return 'user environment variables (Windows registry)'
    shell = os.path.basename(os.environ.get('SHELL', 'bash'))
    profile = os.path.expanduser('~/.zshrc' if shell == 'zsh' else '~/.bashrc')
    with open(profile, 'a', encoding='utf-8') as f:
        f.write('\n# stock-media skill API keys\n')
        for service, key in keys.items():
            f.write(f"export {SERVICES[service]}='{key}'\n")
    os.chmod(profile, 0o600)
    return profile


def shred(path):
    try:
        size = os.path.getsize(path)
        with open(path, 'r+b') as f:
            f.write(b'\0' * size)
            f.flush()
            os.fsync(f.fileno())
        os.remove(path)
        return True
    except OSError:
        return False


def write_config(store, aihsm_names=None):
    config = {'store': store}
    if aihsm_names:
        config['aihsm_names'] = aihsm_names
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template')
    ap.add_argument('--file')
    ap.add_argument('--store', choices=['keyring', 'env', 'aihsm'])
    ap.add_argument('--aihsm-pexels', default='pexels')
    ap.add_argument('--aihsm-pixabay', default='pixabay')
    args = ap.parse_args()

    if args.template:
        with open(args.template, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE)
        print(f'Blank key file written: {args.template}')
        return

    if args.store == 'aihsm':
        write_config('aihsm', {'pexels': args.aihsm_pexels,
                               'pixabay': args.aihsm_pixabay})
        print('Recorded aihsm as the key store.')
        return

    if not (args.file and args.store):
        ap.error('--file and --store are required')
    if not os.path.exists(args.file):
        sys.exit(f'Key file not found: {args.file}')

    keys = parse_file(args.file)
    missing = [s for s in SERVICES if s not in keys]
    if missing:
        sys.exit(f'No key filled in for: {", ".join(missing)}. '
                 'Edit the file, save it, and run this again.')

    ok_all = True
    for service, key in keys.items():
        ok, detail = test_key(service, key)
        print(f'{service}: {"OK" if ok else "FAILED"} ({detail})')
        ok_all &= ok
    if not ok_all:
        sys.exit('Nothing stored. Fix the failed key in the file and run this again.')

    if args.store == 'keyring':
        store_keyring(keys)
        where = 'the OS credential store (service "stock-media")'
    else:
        where = store_env(keys)
    write_config(args.store)
    print(f'Stored both keys in {where}.')
    print('Key file deleted.' if shred(args.file)
          else f'Could not delete {args.file}. Delete it by hand.')


if __name__ == '__main__':
    main()
