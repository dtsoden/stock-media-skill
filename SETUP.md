# Setting up the stock-media skill

These are instructions for Claude Code. A user pasted a request to install this
skill and pointed you at this file. Walk them through it in plain language.
Assume they are not technical: tell them exactly what to click or type, one
step at a time, and do the work yourself wherever you can.

The rule that matters most: API keys must never enter this conversation.
Never ask the user to paste a key into the chat, never read the key file with
a file-reading tool, never `cat` or print it, and never echo a key in a
command. The scripts in this skill test and store the keys without printing
them. If a user pastes a key into the chat anyway, tell them to
regenerate it on the provider's site (Pexels or Pixabay) and continue with the
new one.

## 1. Check the basics

- Python 3.8 or newer must be on the PATH (`python --version`, or `python3` on
  macOS and Linux). If it's missing, tell the user how to install it for their
  OS (`winget install Python.Python.3.12` on Windows, `brew install python` on
  macOS) and wait for them.
- Install the Python packages: `python -m pip install --user Pillow keyring`.
- Ask whether they want stock video as well as images. If yes, check for
  ffmpeg (`ffmpeg -version`). If it's missing, offer to install it
  (`winget install ffmpeg`, `brew install ffmpeg`, or `sudo apt install
  ffmpeg`). Images work without it.

## 2. Install the skill

Copy the `stock-media` folder from https://github.com/dtsoden/stock-media-skill
into the user's personal skills folder, `~/.claude/skills/stock-media`
(`%USERPROFILE%\.claude\skills\stock-media` on Windows). Use `git clone` into a
temporary folder if git is available. Otherwise download
https://github.com/dtsoden/stock-media-skill/archive/refs/heads/main.zip and
extract it. If `~/.claude/skills/stock-media` already exists, this is an
update: replace the files but keep its `config.json`.

From here on, `SCRIPTS` means `~/.claude/skills/stock-media/scripts`.

## 3. Get the two free API keys

If they don't have keys yet, tell them:

- Pexels: sign up at https://www.pexels.com/api/ and request a key. It is
  instant and free.
- Pixabay: sign up at https://pixabay.com/, then open
  https://pixabay.com/api/docs/ while logged in. The key is shown in the
  "Parameters" section next to `key`.

## 4. Choose where to keep the keys

Check whether aihsm is installed (`aihsm --version`). Then ask the user which
option they want, recommending the first one that applies:

1. **aihsm** (only offer if installed): keys go in the OS vault and are
   injected only when the skill runs.
2. **The OS credential store** (Windows Credential Manager, macOS Keychain, or
   Linux Secret Service): keys are encrypted by the OS and the skill reads them
   when it runs. This is the right choice for most people.
3. **Environment variables**: simplest, but the keys sit in plain text in the
   user's environment (and in their shell profile on macOS and Linux).

### If they chose aihsm

They store each key themselves through a hidden prompt, so no file is needed.
Tell them to type these in the Claude Code prompt one at a time and paste the
key when asked (nothing shows as they paste):

```
! aihsm put pexels
! aihsm put pixabay
```

If they already have keys stored under other names, use those names instead.
Then record the choice:

```
python SCRIPTS/store_keys.py --store aihsm --aihsm-pexels pexels --aihsm-pixabay pixabay
```

Test with:

```
aihsm run --set PEXELS_API_KEY=pexels --set PIXABAY_API_KEY=pixabay -- python SCRIPTS/check_keys.py
```

### If they chose the credential store or environment variables

1. Create the blank key file in their home folder:
   `python SCRIPTS/store_keys.py --template ~/stock-media-keys.txt`
2. Open it for them in a text editor: `notepad "$HOME\stock-media-keys.txt"`
   on Windows, `open -e ~/stock-media-keys.txt` on macOS, `xdg-open
   ~/stock-media-keys.txt` on Linux.
3. Tell them to paste each key after its `=` sign, save, close the editor, and
   then tell you they're done. Do not open or read the file yourself.
4. Store the keys (`keyring` for the credential store, `env` for environment
   variables):
   `python SCRIPTS/store_keys.py --file ~/stock-media-keys.txt --store keyring`
   The script tests both keys first and stores nothing if either fails. If one
   fails, tell them which, have them fix it in the file, and run it again. On
   success it deletes the file.
5. Test with `python SCRIPTS/check_keys.py`. With environment variables,
   this only works after Claude Code is restarted, so skip the test and tell
   them it will work in their next session.

## 5. Finish

Tell the user setup is done, and that they need to start a new Claude Code
session before the skill shows up. After that they can ask for images or video
in plain words ("find a hero photo for this page", "get a short background
video of city traffic") or type `/stock-media`.
