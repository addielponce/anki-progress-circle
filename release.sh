#!/usr/bin/env sh
set -eu

addon_directory="src"

manifest="$addon_directory/manifest.json"
[ -f "$manifest" ] || {
	echo "Error: must be run from the repo root ($manifest not found)" >&2
	exit 1
}

package_name=$(jq -r '.package' "$manifest")
version=$(jq -r '.version' "$manifest")
output_addon="v$version-$package_name.ankiaddon"

[ -n "$package_name" ] && [ -n "$version" ] || {
	echo "Error: could not read package/version from $manifest" >&2
	exit 1
}

rm -f "$output_addon"

(cd "$addon_directory" && zip -vr "../$output_addon" .)

printf 'Created %s\n' "$output_addon"
