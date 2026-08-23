# i3 Keymap Overlay

A searchable, full-screen keyboard shortcut overlay for **i3/X11**, inspired by
the Noctalia Keymap plugin.

It combines four reference pages in one window:

- **i3** — shortcuts parsed live from the active i3 configuration;
- **Kitty** — built-in shortcuts plus custom mappings from `kitty.conf`;
- **Vim** — a practical reference plus mappings imported from `.vimrc`;
- **tmux** — built-in shortcuts plus bindings imported from `.tmux.conf`.

The overlay uses GTK 3, has no Python package dependencies, and is designed for
keyboard-driven i3 environments.

## Features

- full-screen Gruvbox-style overlay;
- visual keycaps with colored modifier keys;
- responsive category cards and vertical scrolling;
- live search with `Ctrl+F`;
- keyboard and mouse tab switching;
- case-sensitive Vim commands (`i` and `I`, `v` and `V`, etc.);
- a detailed Vim reference, including Visual Block commenting;
- automatic import of custom Kitty, Vim, and tmux mappings;
- repeat invocation closes the existing overlay;
- optional Remontoire-compatible annotations in the i3 config.

## Requirements

- Linux with X11;
- i3 window manager;
- Python 3.10 or newer;
- GTK 3 Python bindings.

### Ubuntu, Debian, Lubuntu

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-3.0 git
```

### Arch Linux

```bash
sudo pacman -S python python-gobject gtk3 git
```

### Fedora

```bash
sudo dnf install python3 python3-gobject gtk3 git
```

## Installation from the repository

Clone the repository into `~/tools`:

```bash
mkdir -p ~/tools

git clone \
  https://github.com/antivariant/i3-keymap-overlay.git \
  ~/tools/i3-keymap-overlay
```

Install the script for the current user:

```bash
install -Dm755 \
  ~/tools/i3-keymap-overlay/i3-keymap-overlay.py \
  ~/.local/bin/i3-keymap-overlay
```

Check the installation:

```bash
~/.local/bin/i3-keymap-overlay --check
```

Open the overlay manually:

```bash
~/.local/bin/i3-keymap-overlay
```

## i3 configuration

Add the following binding to `~/.config/i3/config`.

Replace `YOUR_USER` with your Linux username:

```i3config
## Help // Show keymap overlay // <Super><Shift> / ##
bindsym $mod+Shift+slash exec --no-startup-id /home/YOUR_USER/.local/bin/i3-keymap-overlay
```

For example:

```i3config
## Help // Show keymap overlay // <Super><Shift> / ##
bindsym $mod+Shift+slash exec --no-startup-id /home/antivariant/.local/bin/i3-keymap-overlay
```

Validate and reload the i3 configuration:

```bash
i3 -C -c ~/.config/i3/config && i3-msg reload
```

Press `Super+Shift+/` to open the overlay. Press the same shortcut again or
press `Esc` to close it.

If the binding does not react, inspect the actual X11 keysym:

```bash
xev -event keyboard
```

On some keyboard layouts, `Shift+/` is reported directly as `question`. In that
case use:

```i3config
bindsym $mod+question exec --no-startup-id /home/YOUR_USER/.local/bin/i3-keymap-overlay
```

## Controls

| Key | Action |
| --- | --- |
| `1` | Open the i3 page |
| `2` | Open the Kitty page |
| `3` | Open the Vim page |
| `4` | Open the tmux page |
| `Ctrl+PageUp` | Previous page |
| `Ctrl+PageDown` | Next page |
| `Ctrl+F` | Focus search |
| `Esc` | Close the overlay |

The tabs can also be selected with the mouse.

## Configuration sources

The default files are:

| Page | Configuration file | Imported declarations |
| --- | --- | --- |
| i3 | `~/.config/i3/config` | `set`, `bindsym`, overlay annotations |
| Kitty | `~/.config/kitty/kitty.conf` | `kitty_mod`, `map` |
| Vim | `~/.vimrc` | `map`, `nmap`, `nnoremap`, `imap`, `vnoremap`, etc. |
| tmux | `~/.tmux.conf` | `prefix`, `bind`, `bind-key` |

Imported Kitty, Vim, and tmux shortcuts appear in a separate **Custom
mappings** category. Missing configuration files are ignored; the built-in
reference remains available.

Mappings are read each time the overlay starts. Close and reopen the overlay
after editing a configuration file.

### Alternative configuration paths

```bash
i3-keymap-overlay \
  --config ~/.config/i3/config \
  --kitty-config ~/.config/kitty/custom.conf \
  --vim-config ~/.vim/vimrc \
  --tmux-config ~/.config/tmux/tmux.conf
```

Use the same arguments in the i3 `bindsym` command if the alternative paths
should always be used.

## i3 shortcut descriptions

Ordinary `bindsym` declarations are detected and classified automatically:

```i3config
bindsym $mod+Return exec --no-startup-id kitty
```

For a precise category and description, add a Remontoire-compatible annotation
directly above the binding:

```i3config
## Applications // Open terminal // <Super> Enter ##
bindsym $mod+Return exec --no-startup-id kitty
```

The annotation format is:

```text
## Category // Description // Keys ##
```

The annotated shortcut replaces the automatically generated entry, so it is not
shown twice.

## Command-line options

```text
--config PATH         i3 configuration file
--kitty-config PATH   Kitty configuration file
--vim-config PATH     Vim configuration file
--tmux-config PATH    tmux configuration file
--check               Validate configuration and print a summary
--dump                Print parsed i3 shortcuts without opening GTK
```

Show built-in help:

```bash
i3-keymap-overlay --help
```

## Updating

```bash
git -C ~/tools/i3-keymap-overlay pull --ff-only

install -Dm755 \
  ~/tools/i3-keymap-overlay/i3-keymap-overlay.py \
  ~/.local/bin/i3-keymap-overlay
```

Restarting i3 is not required after updating the script. Close and reopen the
overlay.

## Uninstalling

Remove the executable:

```bash
rm ~/.local/bin/i3-keymap-overlay
```

Then remove its `bindsym` line from `~/.config/i3/config` and reload i3:

```bash
i3-msg reload
```

The cloned repository can be removed separately if it is no longer needed.
