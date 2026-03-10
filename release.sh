#!/usr/bin/env sh
set -eu

manifest=manifest.json
package_name=$(jq -r '.package' "$manifest")
version=$(jq -r '.version' "$manifest")
output_addon="v$version-$package_name.ankiaddon"

[ -n "$package_name" ] && [ -n "$version" ] || {
	echo "Error: could not read package/version from $manifest" >&2
	exit 1
}

[ "$(basename "$PWD")" = "$package_name" ] || {
	echo "Error: must be run from the '$package_name' directory" >&2
	exit 1
}

rm -f "$output_addon"
git ls-files | zip "$output_addon" -@ -x README.md -x release.sh -x .gitignore -x ".github/*"

printf 'Created %s\n' "$output_addon"
