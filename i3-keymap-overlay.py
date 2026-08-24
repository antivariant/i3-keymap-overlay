#!/usr/bin/env python3
"""A searchable, Noctalia-inspired keymap overlay for i3, Kitty, Vim, tmux and Yazi."""

from __future__ import annotations

import argparse
import collections
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path


APP_ID = "io.github.antivariant.I3KeymapOverlay"
ANNOTATION = re.compile(
    r"^\s*##\s*(?P<section>.*?)\s*//\s*(?P<action>.*?)\s*//\s*(?P<keys>.*?)\s*##\s*$"
)
BINDING = re.compile(r"^\s*bindsym(?:\s+--\S+)*\s+(?P<keys>\S+)\s+(?P<command>.+?)\s*$")
VARIABLE = re.compile(r"^\s*set\s+(?P<name>\$\S+)\s+(?P<value>\S+)\s*$")


@dataclass
class Entry:
    section: str
    action: str
    chords: list[list[str]] = field(default_factory=list)


def shortcuts(section: str, *rows: tuple[str, str]) -> list[Entry]:
    return [Entry(section, action, [split_chord(keys, {})]) for keys, action in rows]


def commands(section: str, *rows: tuple[str, str]) -> list[Entry]:
    """Create entries whose command should be displayed as one exact keycap."""
    return [Entry(section, action, [[command]]) for command, action in rows]


def alternatives(section: str, keys: tuple[str, ...], action: str) -> list[Entry]:
    """Create one action with alternative chords rendered with an `or` separator."""
    return [Entry(section, action, [split_chord(key, {}) for key in keys])]


def static_keymaps(
    kitty_config: Path | None = None,
    vim_config: Path | None = None,
    tmux_config: Path | None = None,
    yazi_config: Path | None = None,
) -> collections.OrderedDict[str, list[Entry]]:
    """Built-in standard shortcuts; personal mappings are intentionally excluded."""
    kitty = [
        *shortcuts("Clipboard", ("<Ctrl><Shift> C", "Copy"), ("<Ctrl><Shift> V", "Paste"), ("<Ctrl><Shift> S", "Paste from selection")),
        *shortcuts("Windows and tabs", ("<Ctrl><Shift> Enter", "New window (split)"), ("<Ctrl><Shift> W", "Close window"), ("<Ctrl><Shift> T", "New tab"), ("<Ctrl><Shift> Q", "Close tab"), ("<Ctrl><Shift> Right", "Next tab"), ("<Ctrl><Shift> Left", "Previous tab"), ("<Ctrl><Shift> .", "Move tab forward"), ("<Ctrl><Shift> ,", "Move tab backward")),
        *shortcuts("Navigation and layout", ("<Ctrl><Shift> ]", "Next window"), ("<Ctrl><Shift> [", "Previous window"), ("<Ctrl><Shift> F", "Move window forward"), ("<Ctrl><Shift> B", "Move window backward"), ("<Ctrl><Shift> L", "Cycle layout")),
        *shortcuts("Scrolling", ("<Ctrl><Shift> Up", "One line up"), ("<Ctrl><Shift> Down", "One line down"), ("<Ctrl><Shift> Page_Up", "One page up"), ("<Ctrl><Shift> Page_Down", "One page down"), ("<Ctrl><Shift> Home", "Scroll to top"), ("<Ctrl><Shift> End", "Scroll to bottom")),
        *shortcuts("Font and help", ("<Ctrl><Shift> equal", "Increase font"), ("<Ctrl><Shift> minus", "Decrease font"), ("<Ctrl><Shift> BackSpace", "Reset font"), ("<Ctrl><Shift> F1", "Help"), ("<Ctrl><Shift> F2", "Edit kitty.conf"), ("<Ctrl><Shift> F3", "Command palette"), ("<Ctrl><Shift> F5", "Reload kitty.conf")),
    ]
    vim = [
        *shortcuts("Modes", ("i", "Insert before cursor"), ("a", "Insert after cursor"), ("I", "Insert at line start"), ("A", "Insert at line end"), ("o", "Open line below"), ("O", "Open line above"), ("Esc", "Normal mode"), ("v", "Visual mode"), ("V", "Visual Line mode"), ("<Ctrl> V", "Visual Block mode")),
        *shortcuts("Horizontal movement", ("h", "Left"), ("l", "Right"), ("0", "Start of line"), ("^", "First non-blank"), ("$", "End of line"), ("w", "Next word"), ("W", "Next WORD (space-delimited)"), ("b", "Previous word"), ("B", "Previous WORD"), ("e", "End of word"), ("f {char}", "Jump to next character"), ("F {char}", "Jump to previous character"), ("t {char}", "Before next character"), ("T {char}", "After previous character"), ("(", "Previous sentence"), (")", "Next sentence"), ("{", "Previous paragraph"), ("}", "Next paragraph")),
        *shortcuts("Vertical movement", ("j", "Down"), ("k", "Up"), ("g g", "First line"), ("G", "Last line"), ("<Ctrl> f", "Page down"), ("<Ctrl> b", "Page up"), ("<Ctrl> d", "Half-page down"), ("<Ctrl> u", "Half-page up"), ("H", "Top of screen"), ("M", "Middle of screen"), ("L", "Bottom of screen"), ("%", "Matching bracket")),
        *commands("Vertical movement", (":{number}", "Go to line number")),
        *shortcuts("Editing", ("x", "Delete character"), ("r {char}", "Replace one character"), ("d d", "Delete line"), ("d w", "Delete word"), ("D", "Delete to line end"), ("d G", "Delete to file end"), ("y y", "Yank line"), ("y w", "Yank word"), ("p", "Paste after"), ("P", "Paste before"), ("u", "Undo"), ("<Ctrl> r", "Redo"), (".", "Repeat last change"), ("> >", "Indent line"), ("< <", "Unindent line")),
        *shortcuts("Text objects", ('c i "', "Change inside quotes"), ('v i "', "Select inside quotes"), ('d i "', "Delete inside quotes"), ("v a p", "Select paragraph including whitespace"), ("v i p", "Select inner paragraph")),
        *shortcuts("Search", ("/ {pattern}", "Search forward"), ("? {pattern}", "Search backward"), ("n", "Next match"), ("N", "Previous match"), ("*", "Word under cursor forward"), ("#", "Word under cursor backward")),
        *commands("Search and replace", (":noh", "(nohlsearch) Clear search highlight"), (":s/old/new/", "(substitute) Replace first match in current line"), (":s/old/new/g", "(substitute) Replace all matches in current line"), (":%s/old/new/g", "(substitute) Replace all matches in file"), (":%s/old/new/gc", "(substitute) Replace in file with confirmation"), (r":%s/\<old\>/new/gc", "(substitute) Replace whole words with confirmation")),
        *commands("Files and buffers", (":w", "(write) Save"), (":q", "(quit) Quit"), (":wq", "(write + quit) Save and quit"), (":q!", "(quit!) Quit without saving"), (":w !sudo tee %", "(write) Save through sudo"), (":e", "(edit) Open file"), (":bn", "(bnext) Next buffer"), (":bp", "(bprevious) Previous buffer"), (":bd", "(bdelete) Delete buffer"), (":ls", "(buffers) List buffers"), (":b {number}", "(buffer) Load buffer in current window")),
        *commands("Line numbers", (":set nu", "(number) Enable line numbers"), (":set nonu", "(nonumber) Disable line numbers"), (":set nu!", "(number!) Toggle line numbers"), (":set rnu", "(relativenumber) Enable relative numbers"), (":set nornu", "(norelativenumber) Disable relative numbers"), (":set rnu!", "(relativenumber!) Toggle relative numbers")),
        *shortcuts("Visual mode", ("v", "Character selection"), ("V", "Line selection"), ("<Ctrl> v", "Block selection"), ("o", "Move to other end of selection"), ("y", "Yank selection"), ("d", "Delete selection"), ("c", "Change selection"), (">", "Indent selection"), ("<", "Unindent selection"), ("~", "Toggle case"), ("U", "Uppercase selection"), ("u", "Lowercase selection"), ("g v", "Reselect last selection"), ("p", "Replace selection with register")),
        *shortcuts("Visual Block: comment", ("<Ctrl> v", "1. Start block selection at first column")),
        *alternatives("Visual Block: comment", ("j", "k"), "2. Extend selection through the lines"),
        *shortcuts("Visual Block: comment", ("I", "3. Insert before the selected block"), ("#", "4a. Type Python/Shell comment prefix"), ("/ /", "4b. Type C/C++/JS comment prefix"), ("Esc", "5. Apply prefix to every selected line")),
        *shortcuts("Visual Block: uncomment", ("<Ctrl> v", "1. Start on the first comment character")),
        *alternatives("Visual Block: uncomment", ("j", "k"), "2. Select the prefix through all lines"),
        *shortcuts("Visual Block: uncomment", ("l", "3. Extend right for a multi-character prefix")),
        *alternatives("Visual Block: uncomment", ("d", "x"), "4. Delete the selected comment block"),
        *shortcuts("Insert mode", ("<Ctrl> w", "Delete previous word"), ("<Ctrl> u", "Delete to line start"), ("<Ctrl> t", "Increase indent"), ("<Ctrl> d", "Decrease indent")),
        *shortcuts("Windows", ("<Ctrl> w s", "Horizontal split"), ("<Ctrl> w v", "Vertical split"), ("<Ctrl> w h", "Focus left"), ("<Ctrl> w j", "Focus down"), ("<Ctrl> w k", "Focus up"), ("<Ctrl> w l", "Focus right"), ("<Ctrl> w q", "Close window"), ("<Ctrl> w =", "Equalize sizes"), ("<Ctrl> w <", "Decrease width"), ("<Ctrl> w >", "Increase width"), ("<Ctrl> w -", "Decrease height"), ("<Ctrl> w +", "Increase height"), ("<Ctrl> w x", "Exchange windows"), ("<Ctrl> w r", "Rotate windows"), ("<Ctrl> w H", "Move window left"), ("<Ctrl> w J", "Move window down"), ("<Ctrl> w K", "Move window up"), ("<Ctrl> w L", "Move window right")),
        *commands("Windows", (":new", "(new) New horizontal window"), (":vnew", "(vnew) New vertical window"), (":sp", "(split) Split current file horizontally"), (":vs", "(vsplit) Split current file vertically")),
        *shortcuts("Registers", ('<"> <+> y', "Yank selection to system clipboard"), ('<"> <+> y y', "Yank line to system clipboard"), ('<"> <+> p', "Paste from system clipboard"), ('<"> 0 p', "Paste last yank"), ('<"> {a-z} y', "Replace named register"), ('<"> {A-Z} y', "Append to named register"), ('<"> {register} p', "Paste named register")),
        *commands("Registers", (":reg", "(registers) Show registers")),
        *commands("Terminal", (":term", "(terminal) Open terminal")),
        *shortcuts("Terminal", ("<Ctrl> d", "Close terminal shell"), ("<Ctrl> backslash <Ctrl> n", "Terminal Normal mode"), ("i", "Return to Terminal mode")),
        *commands("File explorer", (":Ex", "(Explore) Explorer in current window"), (":Sex", "(Sexplore) Explorer in horizontal split"), (":Vex", "(Vexplore) Explorer in vertical split")),
        *commands("Help", (":h", "(help) Open help"), (":h index", "(help index) Command index")),
    ]
    tmux = [
        *shortcuts("Session", ("<Ctrl> b d", "Detach"), ("<Ctrl> b $", "Rename session"), ("<Ctrl> b s", "Choose session"), ("<Ctrl> b (", "Previous session"), ("<Ctrl> b )", "Next session")),
        *shortcuts("Windows", ("<Ctrl> b c", "Create window"), ("<Ctrl> b ,", "Rename window"), ("<Ctrl> b &", "Kill window"), ("<Ctrl> b n", "Next window"), ("<Ctrl> b p", "Previous window"), ("<Ctrl> b l", "Last window"), ("<Ctrl> b w", "Choose window"), ("<Ctrl> b 0…9", "Select window")),
        *shortcuts("Panes", ('<Ctrl> b "', "Split top/bottom"), ("<Ctrl> b %", "Split left/right"), ("<Ctrl> b Left", "Focus left"), ("<Ctrl> b Right", "Focus right"), ("<Ctrl> b Up", "Focus above"), ("<Ctrl> b Down", "Focus below"), ("<Ctrl> b o", "Next pane"), ("<Ctrl> b ;", "Last pane"), ("<Ctrl> b x", "Kill pane"), ("<Ctrl> b z", "Zoom pane"), ("<Ctrl> b !", "Pane to new window"), ("<Ctrl> b {", "Swap backward"), ("<Ctrl> b }", "Swap forward")),
        *shortcuts("Layout and resize", ("<Ctrl> b Space", "Cycle layouts"), ("<Ctrl> b <Alt> 1…5", "Preset layout"), ("<Ctrl> b <Ctrl> Left", "Resize left"), ("<Ctrl> b <Ctrl> Right", "Resize right"), ("<Ctrl> b <Ctrl> Up", "Resize up"), ("<Ctrl> b <Ctrl> Down", "Resize down")),
        *shortcuts("Copy mode", ("<Ctrl> b [", "Enter copy mode"), ("<Ctrl> b ]", "Paste buffer"), ("<Ctrl> b =", "Choose buffer"), ("<Ctrl> b #", "List buffers")),
        *shortcuts("Commands and help", ("<Ctrl> b :", "Command prompt"), ("<Ctrl> b ?", "List key bindings"), ("<Ctrl> b t", "Clock")),
    ]
    yazi = [
        *shortcuts("Navigation", ("h", "Parent directory"), ("j", "Move down"), ("k", "Move up"), ("l", "Open selected item"), ("Enter", "Open selected item"), ("g g", "Go to top"), ("G", "Go to bottom"), ("K", "Seek preview up"), ("J", "Seek preview down"), ("g Space", "Go to path"), ("z", "Jump with fzf"), ("Z", "Jump with zoxide")),
        *shortcuts("Selection", ("Space", "Toggle selection"), ("v", "Visual selection mode"), ("V", "Visual unset mode"), ("<Ctrl> a", "Select all"), ("<Ctrl> r", "Invert selection"), ("Esc", "Cancel selection")),
        *shortcuts("File operations", ("o", "Open"), ("O", "Open interactively"), ("Tab", "Show file information"), ("y", "Yank (copy)"), ("x", "Yank (cut)"), ("p", "Paste"), ("P", "Paste and overwrite"), ("Y", "Cancel yank"), ("X", "Cancel yank"), ("d", "Move to trash"), ("D", "Delete permanently"), ("a", "Create file or directory"), ("r", "Rename"), (".", "Toggle hidden files")),
        *shortcuts("Paths and shell", ("c c", "Copy file path"), ("c d", "Copy directory path"), ("c f", "Copy filename"), ("c n", "Copy filename without extension"), (";", "Run shell command"), (":", "Run blocking shell command"), ("-", "Create absolute symlink"), ("_", "Create relative symlink"), ("<Ctrl> -", "Create hardlink")),
        *shortcuts("Find and search", ("f", "Filter files"), ("/", "Find next"), ("?", "Find previous"), ("n", "Next match"), ("N", "Previous match"), ("s", "Search filenames with fd"), ("S", "Search file contents with ripgrep"), ("<Ctrl> s", "Cancel search")),
        *shortcuts("Sorting", (", m", "Sort by modified time"), (", M", "Modified time (reverse)"), (", e", "Sort by extension"), (", E", "Extension (reverse)"), (", a", "Sort alphabetically"), (", A", "Alphabetical (reverse)"), (", n", "Natural sort"), (", N", "Natural sort (reverse)"), (", s", "Sort by size"), (", S", "Size (reverse)"), (", r", "Random order")),
        *shortcuts("Tabs", ("t t", "Create tab"), ("1…9", "Switch to tab"), ("[", "Previous tab"), ("]", "Next tab"), ("{", "Swap with previous tab"), ("}", "Swap with next tab"), ("<Ctrl> c", "Close current tab")),
        *shortcuts("Help and quit", ("w", "Task manager"), ("F1", "Open help"), ("~", "Open help"), ("q", "Quit")),
    ]
    if kitty_config and kitty_config.is_file():
        kitty.extend(parse_kitty_config(kitty_config))
    if vim_config and vim_config.is_file():
        vim.extend(parse_vim_config(vim_config))
    if tmux_config and tmux_config.is_file():
        tmux.extend(parse_tmux_config(tmux_config))
    if yazi_config and yazi_config.is_file():
        yazi.extend(parse_yazi_config(yazi_config))
    return collections.OrderedDict((("Kitty", kitty), ("Vim", vim), ("tmux", tmux), ("Yazi", yazi)))


def key_name(token: str) -> str:
    names = {
        "Mod4": "Super", "Mod1": "Alt", "Control": "Ctrl",
        "super": "Super", "ctrl": "Ctrl", "control": "Ctrl", "alt": "Alt", "shift": "Shift",
        "Return": "Enter", "Escape": "Esc", "space": "Space",
        "enter": "Enter", "return": "Enter", "escape": "Esc",
        "minus": "−", "plus": "+", "slash": "/", "equal": "=",
        "Left": "←", "Right": "→", "Up": "↑", "Down": "↓",
        "left": "←", "right": "→", "up": "↑", "down": "↓",
        "XF86AudioRaiseVolume": "Vol +", "XF86AudioLowerVolume": "Vol −",
        "XF86AudioMute": "Mute", "XF86AudioMicMute": "Mic Mute",
        "XF86MonBrightnessUp": "Bright +", "XF86MonBrightnessDown": "Bright −",
    }
    # Case is significant in Vim: i/I, a/A, o/O, v/V, p/P and n/N
    # are different commands. Preserve unknown tokens exactly as written.
    return names.get(token, token)


def split_chord(raw: str, variables: dict[str, str]) -> list[str]:
    raw = raw.strip()
    if re.search(r"<[^>]+>", raw):
        # Preserve order in sequences such as Ctrl+\ followed by Ctrl+N.
        parts = [angle or plain for angle, plain in re.findall(r"<([^>]+)>|(\S+)", raw)]
    else:
        parts = raw.split("+") if "+" in raw else raw.split()
    resolved = []
    for part in parts:
        part = part.strip()
        seen = set()
        while part.startswith("$") and part in variables and part not in seen:
            seen.add(part)
            part = variables[part]
        resolved.append(key_name(part))
    return [p for p in resolved if p]


def compact_action(text: str, limit: int = 68) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text[:limit] + ("…" if len(text) > limit else "")


def parse_kitty_config(path: Path) -> list[Entry]:
    """Parse active `map KEY ACTION` declarations from kitty.conf."""
    variables: dict[str, str] = {"kitty_mod": "ctrl+shift"}
    result: list[Entry] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        setting = re.match(r"^(kitty_mod)\s+(.+?)\s*$", line, re.I)
        if setting:
            variables[setting.group(1).lower()] = setting.group(2).strip()
            continue
        match = re.match(r"^map\s+(\S+)\s+(.+?)\s*$", line, re.I)
        if not match or match.group(2).lower() in ("no_op", "noop"):
            continue
        keys, action = match.groups()
        for name, value in variables.items():
            keys = re.sub(rf"\b{re.escape(name)}\b", value, keys, flags=re.I)
        result.append(Entry("Custom mappings", compact_action(action), [split_chord(keys, {})]))
    return result


def vim_key_tokens(lhs: str, leader: str) -> list[str]:
    lhs = re.sub(r"<leader>", leader, lhs, flags=re.I)
    tokens: list[str] = []
    for token in re.findall(r"<[^>]+>|.", lhs):
        if token.isspace():
            tokens.append("Space")
            continue
        if token.startswith("<"):
            inner = token[1:-1]
            parts = inner.split("-")
            modifiers = {"c": "Ctrl", "s": "Shift", "a": "Alt", "m": "Alt"}
            if len(parts) > 1 and all(p.lower() in modifiers for p in parts[:-1]):
                tokens.extend(modifiers[p.lower()] for p in parts[:-1])
                tokens.append(key_name(parts[-1]))
            else:
                tokens.append(key_name(inner))
        else:
            tokens.append(key_name(token))
    return tokens


def parse_vim_config(path: Path) -> list[Entry]:
    """Parse Vim map/noremap commands and keep the mapping mode in the label."""
    leader = "\\"
    result: list[Entry] = []
    map_re = re.compile(r"^\s*(noremap|map|nmap|nnoremap|vmap|vnoremap|xmap|xnoremap|smap|s noremap|omap|onoremap|imap|inoremap|lmap|cmap|cnoremap|tmap|tnoremap)\s+(.+)$", re.I)
    mode_names = {"n": "Normal", "v": "Visual", "x": "Visual", "s": "Select", "o": "Operator", "i": "Insert", "l": "Insert", "c": "Command", "t": "Terminal"}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r'^\s*"', raw_line):
            continue
        leader_match = re.match(r'^\s*let\s+mapleader\s*=\s*["\'](.*)["\']\s*$', raw_line, re.I)
        if leader_match:
            leader = leader_match.group(1).replace("\\<Space>", " ") or "Space"
            continue
        match = map_re.match(raw_line)
        if not match:
            continue
        command, rest = match.groups()
        while re.match(r"^<(?:silent|script|expr|buffer|nowait|special|unique)>\s*", rest, re.I):
            rest = re.sub(r"^<[^>]+>\s*", "", rest, count=1)
        fields = rest.split(None, 1)
        if len(fields) != 2:
            continue
        lhs, rhs = fields
        mode = mode_names.get(command[0].lower(), "Normal/Visual/Operator")
        result.append(Entry("Custom mappings", f"[{mode}] {compact_action(rhs)}", [vim_key_tokens(lhs, leader)]))
    return result


def tmux_key_tokens(key: str) -> list[str]:
    names = {"C": "Ctrl", "M": "Alt", "S": "Shift"}
    parts = key.split("-")
    if len(parts) > 1 and all(part in names for part in parts[:-1]):
        return [*(names[p] for p in parts[:-1]), key_name(parts[-1])]
    return [key_name(key.strip('"\''))]


def parse_tmux_config(path: Path) -> list[Entry]:
    """Parse bind/bind-key declarations, respecting a configured prefix."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    prefix = ["Ctrl", "B"]
    for raw_line in lines:
        match = re.match(r"^\s*set(?:-option)?\s+(?:-g\s+)?prefix\s+(\S+)", raw_line)
        if match:
            prefix = tmux_key_tokens(match.group(1))
    result: list[Entry] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(?:bind|bind-key)\s+(.+)$", line)
        if not match:
            continue
        try:
            fields = shlex.split(match.group(1), comments=True, posix=True)
        except ValueError:
            continue
        no_prefix = False
        note = None
        index = 0
        while index < len(fields) and fields[index].startswith("-"):
            option = fields[index]
            if option == "-n":
                no_prefix = True
            if option in ("-T", "-t", "-N"):
                if index + 1 >= len(fields):
                    break
                if option == "-N":
                    note = fields[index + 1]
                index += 2
            else:
                index += 1
        if len(fields) - index < 2:
            continue
        key = fields[index]
        command = " ".join(fields[index + 1:])
        chord = ([] if no_prefix else prefix) + tmux_key_tokens(key)
        action = note or command
        result.append(Entry("Custom mappings", compact_action(action), [chord]))
    return result


def parse_yazi_config(path: Path) -> list[Entry]:
    """Parse inline keymap records from Yazi's keymap.toml.

    Both ``keymap`` and ``prepend_keymap`` arrays are supported.  The parser is
    intentionally small and only reads the ``on``, ``run`` and ``desc`` fields,
    so it does not require a third-party TOML package on Python 3.10.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    result: list[Entry] = []
    for record in re.findall(r"\{([^{}]*\bon\s*=\s*[^{}]+?)\}", text, re.S):
        on_match = re.search(r"\bon\s*=\s*\[([^]]*)\]", record, re.S)
        if on_match:
            keys = re.findall(r'["\']((?:\\.|[^"\'])*)["\']', on_match.group(1))
        else:
            single = re.search(r"\bon\s*=\s*([\"\'])(.*?)\1", record, re.S)
            keys = [single.group(2)] if single else []
        if not keys:
            continue
        desc = re.search(r"\bdesc\s*=\s*([\"\'])(.*?)\1", record, re.S)
        run = re.search(r"\brun\s*=\s*([\"\'])(.*?)\1", record, re.S)
        action = (desc or run)
        if not action:
            continue
        label = action.group(2).replace(r'\"', '"').replace(r"\'", "'")
        result.append(Entry("Custom mappings", compact_action(label), [[key_name(key) for key in keys]]))
    return result


def classify(command: str) -> tuple[str, str]:
    cmd = re.sub(r"\s+", " ", command.strip())
    tests = [
        (r"\bkitty\b", "Applications", "Open terminal"),
        (r"\brofi\b.*-show\s+drun", "Applications", "Application launcher"),
        (r"\bi3lock\b", "Session", "Lock screen"),
        (r"^kill$", "Window management", "Close window"),
        (r"^fullscreen toggle", "Window management", "Toggle fullscreen"),
        (r"^floating toggle", "Window management", "Toggle floating"),
        (r"^focus mode_toggle", "Window management", "Focus tiling/floating"),
        (r"^focus parent", "Navigation", "Focus parent container"),
        (r"^focus (left|right|up|down)$", "Navigation", "Focus {0}"),
        (r"^move (left|right|up|down)$", "Move windows", "Move window {0}"),
        (r"^split h$", "Layout", "Horizontal split"),
        (r"^split v$", "Layout", "Vertical split"),
        (r"^layout stacking", "Layout", "Stacking layout"),
        (r"^layout tabbed", "Layout", "Tabbed layout"),
        (r"^layout toggle split", "Layout", "Toggle split layout"),
        (r"^move scratchpad", "Scratchpad", "Move window to scratchpad"),
        (r"^scratchpad show", "Scratchpad", "Show/hide scratchpad"),
        (r"^workspace number (.+)$", "Workspaces", "Switch to workspace {0}"),
        (r"^move container to workspace number (.+)$", "Workspaces", "Move window to workspace {0}"),
        (r"^reload$", "i3", "Reload configuration"),
        (r"^restart$", "i3", "Restart i3"),
        (r"i3-msg exit", "Session", "Exit i3 session"),
        (r"mode [\"']?resize", "Resize", "Enter/leave resize mode"),
        (r"resize shrink width", "Resize", "Shrink width"),
        (r"resize grow width", "Resize", "Grow width"),
        (r"resize shrink height", "Resize", "Shrink height"),
        (r"resize grow height", "Resize", "Grow height"),
        (r"set-sink-volume.*\+", "Audio", "Volume up"),
        (r"set-sink-volume.*-", "Audio", "Volume down"),
        (r"set-sink-mute", "Audio", "Mute output"),
        (r"set-source-mute", "Audio", "Mute microphone"),
    ]
    for pattern, section, label in tests:
        match = re.search(pattern, cmd, re.I)
        if match:
            values = [v.replace("$ws", "") for v in match.groups()]
            return section, label.format(*values)
    short = re.sub(r"^exec(?:\s+--no-startup-id)?\s+", "", cmd)
    return "Other", short[:72] + ("…" if len(short) > 72 else "")


def parse_config(path: Path) -> list[Entry]:
    text = path.read_text(encoding="utf-8", errors="replace")
    variables: dict[str, str] = {}
    rows: list[tuple[str, str, list[str]]] = []
    annotated_chords: set[tuple[str, ...]] = set()

    for line in text.splitlines():
        match = VARIABLE.match(line)
        if match:
            variables[match["name"]] = match["value"]

    for line in text.splitlines():
        match = ANNOTATION.match(line)
        if match:
            chord = split_chord(match["keys"], variables)
            rows.append((match["section"], match["action"], chord))
            annotated_chords.add(tuple(chord))

    for line in text.splitlines():
        match = BINDING.match(line)
        if not match or line.lstrip().startswith("#"):
            continue
        chord = split_chord(match["keys"], variables)
        if tuple(chord) in annotated_chords:
            continue
        section, action = classify(match["command"])
        rows.append((section, action, chord))

    grouped: collections.OrderedDict[tuple[str, str], Entry] = collections.OrderedDict()
    for section, action, chord in rows:
        key = (section, action)
        entry = grouped.setdefault(key, Entry(section, action))
        if chord and chord not in entry.chords:
            entry.chords.append(chord)
    return list(grouped.values())


def dump_entries(entries: list[Entry]) -> None:
    current = None
    for entry in entries:
        if entry.section != current:
            current = entry.section
            print(f"\n[{current}]")
        chords = " / ".join(" + ".join(c) for c in entry.chords)
        print(f"  {chords:<34} {entry.action}")


CSS = r"""
window { background: rgba(29,32,33,0.97); color: #ebdbb2; }
.root { padding: 24px 30px 30px; }
.title { font-size: 22px; font-weight: 700; color: #d5c4a1; }
.subtitle { color: #928374; }
.search { min-width: 300px; border-radius: 8px; padding: 6px 10px;
          background: #282828; color: #ebdbb2; border: 1px solid #504945; }
.card { background: rgba(40,40,40,0.94); border: 1px solid #3c3836;
        border-radius: 12px; padding: 14px; }
.section { font-size: 15px; font-weight: 700; color: #b8bb26; margin-bottom: 7px; }
.row { padding: 3px 0; }
.action { color: #d5c4a1; }
.key { background: #504945; color: #ebdbb2; border-radius: 4px; padding: 3px 7px;
       border: 1px solid #665c54; font-weight: 700; }
.super { background: #98971a; color: #1d2021; border-color: #b8bb26; }
.ctrl { background: #458588; color: #1d2021; border-color: #83a598; }
.alt { background: #b16286; color: #1d2021; border-color: #d3869b; }
.shift { background: #d79921; color: #1d2021; border-color: #fabd2f; }
.closehint { color: #a89984; }
scrollbar slider { background: #665c54; min-width: 8px; min-height: 8px; border-radius: 4px; }
"""


def run_gui(
    config: Path,
    entries: list[Entry],
    extra_maps: collections.OrderedDict[str, list[Entry]],
) -> int:
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, Gio, GLib, Gtk
    except (ImportError, ValueError) as exc:
        print("GTK3 bindings are missing. Install: sudo apt install python3-gi gir1.2-gtk-3.0", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2

    class OverlayApp(Gtk.Application):
        def __init__(self):
            super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
            self.window = None
            self.cards = []
            self.current_page = "i3"

        def do_startup(self):
            Gtk.Application.do_startup(self)
            provider = Gtk.CssProvider()
            provider.load_from_data(CSS.encode())
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        def do_activate(self):
            if self.window is not None:
                self.window.destroy()
                self.quit()
                return
            self.window = Gtk.ApplicationWindow(application=self)
            self.window.set_title("Keymap Overlay")
            self.window.set_decorated(False)
            self.window.set_app_paintable(True)
            self.window.connect("key-press-event", self.on_key)
            self.window.connect("destroy", lambda *_: self.quit())
            self.window.add(self.build_ui())
            self.window.fullscreen()
            self.window.show_all()

        def build_ui(self):
            root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
            root.get_style_context().add_class("root")
            header = Gtk.Box(spacing=14)
            titlebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title = Gtk.Label(label="⌨  Keymap", xalign=0)
            title.get_style_context().add_class("title")
            subtitle = Gtk.Label(label="1 i3  ·  2 Kitty  ·  3 Vim  ·  4 tmux  ·  5 Yazi", xalign=0)
            subtitle.get_style_context().add_class("subtitle")
            titlebox.pack_start(title, False, False, 0)
            titlebox.pack_start(subtitle, False, False, 0)
            self.search = Gtk.SearchEntry()
            self.search.set_placeholder_text("Search shortcuts…   Ctrl+F")
            self.search.get_style_context().add_class("search")
            self.search.connect("search-changed", self.filter_rows)
            hint = Gtk.Label(label="Esc  close")
            hint.get_style_context().add_class("closehint")
            header.pack_start(titlebox, True, True, 0)
            header.pack_start(self.search, False, False, 0)
            header.pack_start(hint, False, False, 0)
            root.pack_start(header, False, False, 0)

            self.stack = Gtk.Stack()
            self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.stack.set_transition_duration(120)
            switcher = Gtk.StackSwitcher()
            switcher.set_stack(self.stack)
            switcher.set_halign(Gtk.Align.CENTER)
            root.pack_start(switcher, False, False, 0)

            maps = collections.OrderedDict((("i3", entries), *extra_maps.items()))
            for name, page_entries in maps.items():
                self.stack.add_titled(self.make_page(name, page_entries), name.lower(), name)
            self.stack.connect("notify::visible-child-name", self.on_page_changed)
            root.pack_start(self.stack, True, True, 0)
            return root

        def make_page(self, page_name, page_entries):
            scroll = Gtk.ScrolledWindow()
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(False)
            flow.set_row_spacing(12)
            flow.set_column_spacing(12)
            flow.set_min_children_per_line(3)
            flow.set_max_children_per_line(4)
            sections = collections.OrderedDict()
            for entry in page_entries:
                sections.setdefault(entry.section, []).append(entry)
            for section, section_entries in sections.items():
                card = self.make_card(page_name.lower(), section, section_entries)
                flow.add(card)
            scroll.add(flow)
            return scroll

        def make_card(self, page, section, section_entries):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            card.set_size_request(390, -1)
            card.get_style_context().add_class("card")
            heading = Gtk.Label(label=section, xalign=0)
            heading.get_style_context().add_class("section")
            card.pack_start(heading, False, False, 0)
            records = []
            for entry in section_entries:
                row = Gtk.Box(spacing=10)
                row.get_style_context().add_class("row")
                keybox = Gtk.Box(spacing=3)
                for ci, chord in enumerate(entry.chords):
                    if ci:
                        keybox.pack_start(Gtk.Label(label="or"), False, False, 2)
                    for key in chord:
                        label = Gtk.Label(label=key)
                        context = label.get_style_context()
                        context.add_class("key")
                        lower = key.lower()
                        if lower in ("super", "ctrl", "alt", "shift"):
                            context.add_class(lower)
                        keybox.pack_start(label, False, False, 0)
                action = Gtk.Label(label=entry.action, xalign=0)
                action.set_line_wrap(True)
                action.get_style_context().add_class("action")
                row.pack_start(keybox, False, False, 0)
                row.pack_start(action, True, True, 0)
                card.pack_start(row, False, False, 0)
                records.append((row, entry.action.lower(), " ".join(sum(entry.chords, [])).lower()))
            self.cards.append((page, card, heading, section.lower(), records))
            return card

        def on_page_changed(self, *_args):
            self.current_page = self.stack.get_visible_child_name() or "i3"
            self.filter_rows(self.search)

        def filter_rows(self, entry):
            query = entry.get_text().strip().lower()
            for page, card, _heading, section, records in self.cards:
                if page != self.current_page:
                    continue
                any_visible = False
                for row, action, keys in records:
                    visible = not query or query in section or query in action or query in keys
                    row.set_visible(visible)
                    any_visible |= visible
                card.set_visible(any_visible)

        def on_key(self, _window, event):
            key = Gdk.keyval_name(event.keyval)
            if key == "Escape":
                self.window.destroy()
                return True
            if key and key.lower() == "f" and event.state & Gdk.ModifierType.CONTROL_MASK:
                self.search.grab_focus()
                return True
            if key in ("1", "2", "3", "4", "5") and not event.state & (
                Gdk.ModifierType.CONTROL_MASK
                | Gdk.ModifierType.MOD1_MASK
                | Gdk.ModifierType.SUPER_MASK
            ):
                self.stack.set_visible_child_name(("i3", "kitty", "vim", "tmux", "yazi")[int(key) - 1])
                return True
            if event.state & Gdk.ModifierType.CONTROL_MASK and key in ("Page_Up", "Page_Down"):
                names = ("i3", "kitty", "vim", "tmux", "yazi")
                index = names.index(self.current_page)
                step = -1 if key == "Page_Up" else 1
                self.stack.set_visible_child_name(names[(index + step) % len(names)])
                return True
            return False

    return OverlayApp().run([sys.argv[0]])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("~/.config/i3/config").expanduser())
    parser.add_argument("--kitty-config", type=Path, default=Path("~/.config/kitty/kitty.conf").expanduser())
    parser.add_argument("--vim-config", type=Path, default=Path("~/.vimrc").expanduser())
    parser.add_argument("--tmux-config", type=Path, default=Path("~/.tmux.conf").expanduser())
    parser.add_argument("--yazi-config", type=Path, default=Path("~/.config/yazi/keymap.toml").expanduser())
    parser.add_argument("--check", action="store_true", help="validate and summarize without opening GTK")
    parser.add_argument("--dump", action="store_true", help="print parsed shortcuts")
    args = parser.parse_args()
    try:
        entries = parse_config(args.config)
    except OSError as exc:
        parser.error(str(exc))
    if not entries:
        parser.error(f"no bindsym entries or annotations found in {args.config}")
    extra_maps = static_keymaps(args.kitty_config, args.vim_config, args.tmux_config, args.yazi_config)
    if args.check:
        sections = len({entry.section for entry in entries})
        chords = sum(len(entry.chords) for entry in entries)
        print(f"OK: {chords} shortcuts, {len(entries)} actions, {sections} sections from {args.config}")
        for name, map_entries in extra_maps.items():
            custom = sum(entry.section == "Custom mappings" for entry in map_entries)
            source = {"Kitty": args.kitty_config, "Vim": args.vim_config, "tmux": args.tmux_config, "Yazi": args.yazi_config}[name]
            status = str(source) if source.is_file() else "config not found"
            print(f"{name}: {len(map_entries)} actions ({custom} custom) — {status}")
        return 0
    if args.dump:
        dump_entries(entries)
        return 0
    return run_gui(args.config, entries, extra_maps)


if __name__ == "__main__":
    raise SystemExit(main())
