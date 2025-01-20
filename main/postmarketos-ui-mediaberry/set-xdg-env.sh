#!/bin/sh

# Mediaberry doesn't set XDG variables automatically, so we do it here.

XDG_CONFIG_HOME="${HOME}/.config"
export XDG_CONFIG_HOME
XDG_CACHE_HOME="${HOME}/.cache"
export XDG_CACHE_HOME
XDG_DATA_HOME="${HOME}/.local/share"
export XDG_DATA_HOME
XDG_STATE_HOME="${HOME}/.local/state"
export XDG_STATE_HOME
XDG_DATA_DIRS="${HOME}/.local/share/:${HOME}/.local/share/flatpak/exports/share/:/var/lib/flatpak/exports/share/:/usr/local/share/:/usr/share/"
export XDG_DATA_DIRS
XDG_RUNTIME_DIR="/run/user/$(id -u)"
export XDG_RUNTIME_DIR
