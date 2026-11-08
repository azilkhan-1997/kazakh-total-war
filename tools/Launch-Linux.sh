#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
engine_path="${1:-pyrogenesis}"
target_dir="${XDG_DATA_HOME:-$HOME/.local/share}/0ad/mods/kazakh_total_war"
if [[ -e "$target_dir" ]]; then
  printf 'Module destination already exists: %s\nInstall/update it explicitly, then launch with -mod=public -mod=kazakh_total_war.\n' "$target_dir"
  exit 1
fi
mkdir -p -- "$(dirname -- "$target_dir")"
ln -s -- "$project_dir/mods/kazakh_total_war" "$target_dir"
exec "$engine_path" -mod=public -mod=kazakh_total_war
