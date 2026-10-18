#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 /path/to/YanxiaoZhao-yymmdd.pdf" >&2
    exit 2
fi

pdf_path=$1

if [[ ! -f "$pdf_path" ]]; then
    echo "ERROR: PDF not found: $pdf_path" >&2
    exit 1
fi

for command_name in pdfinfo pdffonts pdftotext python3; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "ERROR: required command is unavailable: $command_name" >&2
        exit 1
    fi
done

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
resume_dir=$(cd "$script_dir/.." && pwd -P)
temp_parent="$resume_dir/tmp/pdfs"
mkdir -p "$temp_parent"
check_dir=$(mktemp -d "$temp_parent/check.XXXXXX")

cleanup() {
    local resolved_parent resolved_target
    resolved_parent=$(cd "$temp_parent" && pwd -P) || return
    resolved_target=$(cd "$check_dir" && pwd -P) || return

    case "$resolved_target" in
        "$resolved_parent"/check.*) ;;
        *) return ;;
    esac

    [[ -d "$resolved_target" && ! -L "$resolved_target" ]] || return
    find "$resolved_target" -type l -print >/dev/null
    /bin/rm -rf -- "$resolved_target"
}
trap cleanup EXIT

info_file="$check_dir/pdfinfo.txt"
fonts_file="$check_dir/pdffonts.txt"
raw_text_file="$check_dir/raw.txt"
layout_text_file="$check_dir/layout.txt"

pdfinfo "$pdf_path" > "$info_file"
pdffonts "$pdf_path" > "$fonts_file"
pdftotext -raw "$pdf_path" "$raw_text_file"
pdftotext -layout "$pdf_path" "$layout_text_file"

pages=$(awk -F: '/^Pages:/ {gsub(/[[:space:]]/, "", $2); print $2}' "$info_file")
tagged=$(awk -F: '/^Tagged:/ {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}' "$info_file")
page_size=$(awk -F: '/^Page size:/ {sub(/^[[:space:]]+/, "", $2); print $2}' "$info_file")
pdf_title=$(awk -F: '/^Title:/ {sub(/^[[:space:]]+/, "", $2); print $2}' "$info_file")
pdf_bytes=$(wc -c < "$pdf_path" | tr -d '[:space:]')

[[ "$pages" == "1" ]] || { echo "ERROR: expected one page, got $pages" >&2; exit 1; }
[[ "$tagged" == "yes" ]] || { echo "ERROR: PDF is not tagged" >&2; exit 1; }
[[ "$page_size" == *"A4"* ]] || { echo "ERROR: expected A4, got $page_size" >&2; exit 1; }
[[ "$pdf_title" =~ ^YanxiaoZhao-[0-9]{6}$ ]] || { echo "ERROR: unexpected PDF title: $pdf_title" >&2; exit 1; }
(( pdf_bytes < 2621440 )) || { echo "ERROR: PDF exceeds the 2.5 MB ATS limit" >&2; exit 1; }

python3 - "$fonts_file" "$raw_text_file" <<'PY'
from pathlib import Path
import re
import sys

fonts_path = Path(sys.argv[1])
text_path = Path(sys.argv[2])

font_lines = [line for line in fonts_path.read_text(encoding="utf-8").splitlines()[2:] if line.strip()]
if not font_lines:
    raise SystemExit("ERROR: no embedded fonts found")

for line in font_lines:
    if "Type 3" in line:
        raise SystemExit(f"ERROR: Type 3 font found: {line}")
    fields = line.split()
    if len(fields) < 7:
        raise SystemExit(f"ERROR: unrecognized pdffonts line: {line}")
    embedded, subset, unicode_map = fields[-5:-2]
    if embedded != "yes" or unicode_map != "yes":
        raise SystemExit(f"ERROR: font is not embedded with Unicode mapping: {line}")

text = text_path.read_text(encoding="utf-8")
normalized = re.sub(r"\s+", " ", text).strip()

ordered_phrases = [
    "赵砚潇",
    "adam.zhao.cs@outlook.com",
    "+86 185-6776-0728",
    "教育经历",
    "中国科学院大学",
    "厦门大学嘉庚学院",
    "实习经历",
    "智谱华章",
    "RLVR for Computer Use Agent",
    "开发 300K+ 行 CUA 环境平台",
    "理想汽车",
    "商汤科技",
    "零一汽车",
    "研究工作",
    "GLM-5V-Turbo: Toward a Native Foundation Model",
    "SATQuest: A Verifier for Logical Reasoning Evaluation",
    "ComputerRL: Scaling End-to-End Online Reinforcement Learning",
    "CAMEL: Continuous Action Masking Enabled by LLMs for RL",
    "Snapshot Reinforcement Learning: Leveraging Prior Trajectories",
    "SCALECUA: Scaling Computer Use Agents",
    "Open RL Benchmark: Comprehensive Tracked Experiments",
    "开源贡献",
    "sdpkjc/abcdrl",
    "vwxyzjn/cleanrl",
    "xlang-ai/OSWorld",
    "sglang",
]

cursor = -1
for phrase in ordered_phrases:
    position = normalized.find(phrase, cursor + 1)
    if position < 0:
        raise SystemExit(f"ERROR: missing or out-of-order text: {phrase}")
    cursor = position

print(f"PASS: {len(font_lines)} fonts embedded with Unicode maps; no Type 3 fonts")
print(f"PASS: {len(ordered_phrases)} required text blocks appear in logical order")
PY

echo "PASS: one-page tagged A4 PDF, ${pdf_bytes} bytes"
echo "PASS: title is $pdf_title"
echo "ATS CHECK PASSED: $pdf_path"
