# Setting up the stock-media Agent Skill

These are instructions for an AI coding agent (Claude Code, Codex, Gemini CLI,
Cursor, GitHub Copilot, or any other tool that supports Agent Skills). A user
asked you to set up this skill and pointed you here. Walk them through it in
plain language. Assume they are not technical. Give one step at a time, say exactly what to
type, and do the work yourself wherever you can.

The rule that matters most: API keys must never enter this conversation.
Never ask the user to paste a key into the chat, never open or read the key
file, never `cat` or print it, and never put a key in a command. The scripts in
this skill test and store the keys without printing them. If a user pastes a
key into the chat anyway, tell them to regenerate it on the provider's site
(Pexels or Pixabay) and continue with the new one.

If your sandbox blocks network access, package installs, or the OS credential
store, ask the user to approve those steps when they come up.

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

If Node.js is installed (`npx --version`), use the `skills` installer. It
detects which AI tools are on the machine and installs the skill for each of
them:

```
npx skills add dtsoden/stock-media-skill -g -y
```

Set the environment variable `DISABLE_TELEMETRY=1` for that command so it
sends no usage data.

Without Node.js, copy the `skills/stock-media` folder from
https://github.com/dtsoden/stock-media-skill into your own user-level skills
folder. Use `git clone` into a temporary folder if git is available, or
download https://github.com/dtsoden/stock-media-skill/archive/refs/heads/main.zip
and extract it. Known locations:

- Claude Code: `~/.claude/skills/stock-media`
- Codex: `~/.agents/skills/stock-media`
- Gemini CLI: `~/.gemini/skills/stock-media` (it also reads `~/.agents/skills`)
- Cursor: `~/.cursor/skills/stock-media`
- OpenCode: `~/.config/opencode/skills/stock-media`
- Anything else: check your own documentation for where user skills go.

On Windows, `~` is `%USERPROFILE%`. From here on, `SCRIPTS` means the
`scripts` folder inside the installed skill.

## 3. Get the two free API keys

If they don't have keys yet, tell them:

- Pexels: sign up at https://www.pexels.com/api/ and request a key. It is
  instant and free.
- Pixabay: sign up at https://pixabay.com/, then open
  https://pixabay.com/api/docs/ while logged in. Their key is shown in the
  "Parameters" section next to `key`.

## 4. Choose where to keep the keys

Check whether aihsm is installed (`aihsm --version`). Then ask the user which
option they want, recommending the first one that applies:

1. **aihsm** (only offer if installed): keys go in the OS vault and are
   injected only when the skill runs. See https://github.com/dtsoden/aihsm.
2. **The OS credential store** (Windows Credential Manager, macOS Keychain, or
   Linux Secret Service): keys are encrypted by the OS and the skill reads them
   when it runs. This is the right choice for most people.
3. **Environment variables**: simplest, but the keys sit in plain text in the
   user's environment (and in their shell profile on macOS and Linux).

### If they chose aihsm

They store each key themselves through a hidden prompt, so no file is needed.
Tell them to run these in their own terminal one at a time and paste the key
when asked (nothing shows as they paste). In Claude Code they can type them in
the prompt with a `!` in front.

```
aihsm put pexels
aihsm put pixabay
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
5. Test with `python SCRIPTS/check_keys.py`. With environment variables, this
   only works after the AI tool is restarted, so skip the test and tell them it
   will work in their next session.

The choice is saved in `~/.config/stock-media/config.json`, which every AI tool
with this skill installed reads, so setup only has to happen once per machine.

## 5. Finish

Tell the user setup is done and that they need to start a new session of their
AI tool before the skill shows up. After that they can ask for images or video
in plain words ("find a hero photo for this page", "get a short background
video of city traffic"). Tools that list skills as commands also accept
`/stock-media`.
