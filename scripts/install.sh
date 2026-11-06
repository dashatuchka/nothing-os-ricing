#!/usr/bin/env bash
# Copy only this project's configs. Existing files require --replace.
set -euo pipefail

replace=false
case "${1:-}" in
  '') ;;
  --replace) replace=true ;;
  *) echo 'Usage: bash scripts/install.sh [--replace]' >&2; exit 2 ;;
esac

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../config" && pwd)"
target_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
backup_dir="${XDG_STATE_HOME:-$HOME/.local/state}/nothing-rice/backups/$(date +%Y%m%d-%H%M%S)-$$"
configs=(niri waybar fuzzel foot mako swaylock kitty)

# Preflight every destination before copying anything.
for name in "${configs[@]}"; do
  if [[ -e "$target_dir/$name" || -L "$target_dir/$name" ]]; then
    if [[ "$replace" == false ]]; then
      printf 'Already exists: %s\nUse --replace to back up and replace the project config directories.\n' "$target_dir/$name" >&2
      exit 1
    fi
  fi
done

mkdir -p -- "$target_dir"
for name in "${configs[@]}"; do
  if [[ -e "$target_dir/$name" || -L "$target_dir/$name" ]]; then
    mkdir -p -- "$backup_dir"
    mv -- "$target_dir/$name" "$backup_dir/$name"
  fi
  cp -R -- "$source_dir/$name" "$target_dir/$name"
done
printf 'Installed in %s\n' "$target_dir"
if [[ -d "$backup_dir" ]]; then printf 'Backup: %s\n' "$backup_dir"; fi
printf 'Validate before logging in: niri validate\n'
