#!/usr/bin/env bash
set -euo pipefail

for command_name in pdfinfo pdffonts pdftotext python3; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "ERROR: required command is unavailable: $command_name" >&2
        exit 1
    fi
done

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
resume_dir=$(cd "$script_dir/.." && pwd -P)
html_path="$resume_dir/index.html"

if [[ ! -f "$html_path" ]]; then
    echo "ERROR: resume source not found: $html_path" >&2
    exit 1
fi

if [[ -n "${CHROME_BIN:-}" ]]; then
    chrome_bin=$CHROME_BIN
elif [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]; then
    chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif command -v google-chrome >/dev/null 2>&1; then
    chrome_bin=$(command -v google-chrome)
elif command -v chromium >/dev/null 2>&1; then
    chrome_bin=$(command -v chromium)
else
    echo "ERROR: Chrome or Chromium was not found; set CHROME_BIN explicitly" >&2
    exit 1
fi

date_code=${RESUME_DATE:-$(date +%y%m%d)}
if [[ ! "$date_code" =~ ^[0-9]{6}$ ]]; then
    echo "ERROR: RESUME_DATE must use yymmdd format" >&2
    exit 1
fi

output_path=${1:-"$resume_dir/output/pdf/YanxiaoZhao-${date_code}.pdf"}
output_dir=$(dirname "$output_path")
mkdir -p "$output_dir"

temp_parent="$resume_dir/tmp/pdfs"
mkdir -p "$temp_parent"
profile_dir=$(mktemp -d "$temp_parent/chrome-profile.XXXXXX")
chrome_log="$temp_parent/chrome-${date_code}.log"
staged_pdf="$profile_dir/YanxiaoZhao-${date_code}.pdf"
chrome_pid=""

stop_export_chrome() {
    local chrome_command attempt

    [[ "$chrome_pid" =~ ^[0-9]+$ ]] || return 0
    kill -0 "$chrome_pid" 2>/dev/null || { wait "$chrome_pid" 2>/dev/null || true; return 0; }

    chrome_command=$(ps -p "$chrome_pid" -o command=) || return 1
    case "$chrome_command" in
        *"--user-data-dir=$profile_dir"*) ;;
        *) echo "ERROR: refusing to stop an unrecognized process: $chrome_pid" >&2; return 1 ;;
    esac

    kill -TERM "$chrome_pid" || return 1
    for attempt in {1..50}; do
        if ! kill -0 "$chrome_pid" 2>/dev/null; then
            wait "$chrome_pid" 2>/dev/null || true
            return 0
        fi
        sleep 0.1
    done

    echo "ERROR: Chrome did not stop cleanly; temporary profile preserved at $profile_dir" >&2
    return 1
}

cleanup() {
    local resolved_parent resolved_target

    stop_export_chrome || return
    resolved_parent=$(cd "$temp_parent" && pwd -P) || return
    resolved_target=$(cd "$profile_dir" && pwd -P) || return

    case "$resolved_target" in
        "$resolved_parent"/chrome-profile.*) ;;
        *) return ;;
    esac

    [[ -d "$resolved_target" && ! -L "$resolved_target" ]] || return
    find "$resolved_target" -type l -print >/dev/null
    /bin/rm -rf -- "$resolved_target"
}
trap cleanup EXIT

resume_url=$(python3 - "$html_path" "$date_code" <<'PY'
from pathlib import Path
from urllib.parse import urlencode
import sys

print(Path(sys.argv[1]).resolve().as_uri() + "?" + urlencode({"resumeDate": sys.argv[2]}))
PY
)

"$chrome_bin" \
    --headless=new \
    --disable-background-networking \
    --disable-component-update \
    --disable-default-apps \
    --disable-extensions \
    --disable-gpu \
    --no-default-browser-check \
    --no-first-run \
    --no-pdf-header-footer \
    --allow-file-access-from-files \
    --user-data-dir="$profile_dir" \
    --print-to-pdf="$staged_pdf" \
    "$resume_url" >"$chrome_log" 2>&1 &
chrome_pid=$!

last_size=0
stable_checks=0
pdf_ready=false

for attempt in {1..450}; do
    if [[ -s "$staged_pdf" ]]; then
        current_size=$(wc -c < "$staged_pdf" | tr -d '[:space:]')
        if [[ "$current_size" == "$last_size" ]]; then
            stable_checks=$((stable_checks + 1))
        else
            stable_checks=0
            last_size=$current_size
        fi

        if (( stable_checks >= 3 )); then
            pdf_ready=true
            break
        fi
    fi

    if ! kill -0 "$chrome_pid" 2>/dev/null; then
        break
    fi
    sleep 0.1
done

stop_export_chrome

if [[ "$pdf_ready" != true || ! -s "$staged_pdf" ]]; then
    echo "ERROR: Chrome did not finish the PDF; see $chrome_log" >&2
    exit 1
fi

"$script_dir/check-resume-pdf.sh" "$staged_pdf"
mv -f -- "$staged_pdf" "$output_path"

resolved_log=$(realpath "$chrome_log")
case "$resolved_log" in
    "$temp_parent"/chrome-??????.log) ;;
    *) echo "ERROR: refusing to remove an unrecognized log path: $resolved_log" >&2; exit 1 ;;
esac
[[ -f "$resolved_log" && ! -L "$resolved_log" ]] || exit 1
find "$resolved_log" -maxdepth 0 -type f -delete

echo "EXPORTED: $output_path"
