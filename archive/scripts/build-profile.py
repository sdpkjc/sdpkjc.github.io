#!/usr/bin/env python3
"""Build the outlined homepage SVG and embed it in index.html.

Run in a virtual environment:
    python -m pip install -r scripts/profile-requirements.txt
    python scripts/build-profile.py

Edit copy/layout below and page styles in profile-shell.html, then regenerate.
The generated page needs no JavaScript, font download, or build step to view.
"""

from html import escape
from io import BytesIO
from pathlib import Path
import xml.etree.ElementTree as ET

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


ROOT = Path(__file__).resolve().parents[1]
FONT_SIZE = 20
WIDTH, HEIGHT = 360, 240
INK = "#242321"
SECONDARY_INK = "#62615D"
NAME_GAP = 10
ENGLISH_NAME = "Yanxiao Zhao"
CHINESE_NAME = "赵砚潇"
INTEREST = "Reinforcement Learner"
EDUCATION = ("CS PhD Student @ ", "UCAS", "https://www.ucas.ac.cn/")
EMPLOYMENT = ("Intern @ ", "Tencent Hy", "https://hy.tencent.ai/")


def number(value):
    return f"{value:.3f}".rstrip("0").rstrip(".") or "0"


class OutlinedFont:
    def __init__(self, filename, prefix, axes=None):
        font = TTFont(ROOT / "assets/fonts" / filename)
        if axes:
            font = instantiateVariableFont(font, axes, inplace=True)
        font.flavor = None
        binary = BytesIO()
        font.save(binary)
        self.hb_font = hb.Font(hb.Face(binary.getvalue()))
        hb.ot_font_set_funcs(self.hb_font)
        self.scale = FONT_SIZE / font["head"].unitsPerEm
        self.glyphs = font.getGlyphSet()
        self.order = font.getGlyphOrder()
        self.prefix = prefix
        self.definitions = {}

    def shape(self, text):
        buffer = hb.Buffer()
        buffer.add_str(text)
        buffer.guess_segment_properties()
        hb.shape(self.hb_font, buffer, {"liga": False, "calt": False})
        shaped = list(zip(buffer.glyph_infos, buffer.glyph_positions))
        if any(info.codepoint == 0 for info, _ in shaped):
            raise ValueError(f"Missing glyph in {text!r}")
        return shaped

    def width(self, text):
        return sum(position.x_advance for _, position in self.shape(text)) * self.scale

    def ink_center(self, text):
        bounds = []
        for info, position in self.shape(text):
            pen = BoundsPen(self.glyphs)
            self.glyphs[self.order[info.codepoint]].draw(pen)
            if pen.bounds:
                bounds.append((pen.bounds[1] + position.y_offset,
                               pen.bounds[3] + position.y_offset))
        return (min(b[0] for b in bounds) + max(b[1] for b in bounds)) * self.scale / 2

    def render(self, text, x, baseline):
        uses = []
        for info, position in self.shape(text):
            glyph_id = f"{self.prefix}-{info.codepoint}"
            if glyph_id not in self.definitions:
                pen = SVGPathPen(self.glyphs, ntos=number)
                transformed = TransformPen(pen, (self.scale, 0, 0, -self.scale, 0, 0))
                self.glyphs[self.order[info.codepoint]].draw(transformed)
                self.definitions[glyph_id] = pen.getCommands()
            if self.definitions[glyph_id]:
                uses.append(f'<use href="#{glyph_id}" x="{number(x + position.x_offset * self.scale)}" '
                            f'y="{number(baseline - position.y_offset * self.scale)}"/>')
            x += position.x_advance * self.scale
        return "".join(uses)


def rect(class_name, x, y, width, height, radius=0):
    return (f'<rect class="{class_name}" x="{number(x)}" y="{number(y)}" '
            f'width="{number(width)}" height="{number(height)}" rx="{radius}"/>')


def text_link(font, label, href, x, baseline):
    width = font.width(label)
    return (f'<a class="text-link" href="{escape(href, quote=True)}" target="_blank" '
            f'rel="noopener noreferrer" tabindex="0" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title>'
            '<g aria-hidden="true">'
            + rect("hit", x - 3, baseline - 23, width + 6, 32)
            + font.render(label, x, baseline)
            + f'<path class="underline" d="M{number(x)} {baseline + 5}h{number(width)}"/>'
            + rect("focus-ring", x - 4, baseline - 24, width + 8, 34, 3)
            + '</g></a>')


def linked_line(font, parts, baseline):
    prefix, label, href = parts
    # A round, open @ avoids squeezing a complex symbol into a narrow mono cell.
    use_custom_at = prefix.endswith(" @ ")
    role = prefix[:-3] if use_custom_at else prefix
    prefix_width = font.width(role) + (30 if use_custom_at else 0)
    x = (WIDTH - prefix_width - font.width(label)) / 2
    prefix_art = font.render(role, x, baseline)
    if use_custom_at:
        symbol_x = x + font.width(role) + 6.6
        prefix_art += (
            f'<g class="at-sign" transform="translate({number(symbol_x)} {baseline - 15}) scale(.7)" '
            'fill="none" stroke="currentColor" stroke-width="2.1" '
            'stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="4"/>'
            '<path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-4 8"/>'
            '</g>')
    return (f'<!-- {escape(prefix + label)} -->\n'
            '<g class="secondary">'
            f'<g aria-hidden="true">{prefix_art}</g>\n'
            + text_link(font, label, href, x + prefix_width, baseline)
            + '</g>')


def icon_geometry(filename, size, center_x, center_y):
    root = ET.parse(ROOT / "assets/social" / filename).getroot()
    vx, vy, vw, vh = map(float, root.attrib["viewBox"].split())
    scale = size / max(vw, vh)
    shapes = []
    for child in root:
        if child.tag.rsplit("}", 1)[-1] == "path":
            shapes.append(f'<path d="{escape(child.attrib["d"], quote=True)}"/>')
    return (f'<g transform="translate({number(center_x - vw * scale / 2)} '
            f'{number(center_y - vh * scale / 2)}) scale({number(scale)}) '
            f'translate({number(-vx)} {number(-vy)})">{"".join(shapes)}</g>')


def contact_link(label, href, geometry, center_x):
    external = ' target="_blank" rel="noopener noreferrer"' if not href.startswith("mailto:") else ""
    return (f'<a class="contact-link" href="{escape(href, quote=True)}"{external} '
            f'tabindex="0" aria-label="{escape(label)}">'
            f'<title>{escape(label)}</title><g aria-hidden="true">'
            + rect("hit", center_x - 16, 194, 32, 32)
            + geometry
            + rect("focus-ring", center_x - 15, 195, 30, 30, 4)
            + '</g></a>')


def build_svg():
    latin = OutlinedFont("Recursive-1.085-latin.woff2", "latin", {
        "MONO": 1, "CASL": 0.2, "wght": 400, "slnt": 0, "CRSV": 0,
    })
    chinese = OutlinedFont("SarasaMonoSC-Minimal.ttf", "han")
    name_width = latin.width(ENGLISH_NAME) + NAME_GAP + chinese.width(CHINESE_NAME)
    name_x = (WIDTH - name_width) / 2
    chinese_baseline = 32 + chinese.ink_center(CHINESE_NAME) - latin.ink_center(ENGLISH_NAME)
    visual = [
        f'<!-- {ENGLISH_NAME} {CHINESE_NAME} -->',
        '<g aria-hidden="true">'
        + latin.render(ENGLISH_NAME, name_x, 32)
        + chinese.render(CHINESE_NAME, name_x + latin.width(ENGLISH_NAME) + NAME_GAP, chinese_baseline)
        + '</g>',
        f'<!-- {INTEREST} -->',
        f'<g aria-hidden="true">{latin.render(INTEREST, (WIDTH - latin.width(INTEREST)) / 2, 84)}</g>',
        linked_line(latin, EDUCATION, 116),
        linked_line(latin, EMPLOYMENT, 148),
    ]
    # 32px hit areas on 48px centers leave a genuine 16px non-clickable gap.
    email = ('<g transform="translate(73.5 199.5) scale(.875)" fill="none" '
             'stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'
             '<rect x="2" y="4.5" width="20" height="15" rx="1.5"/>'
             '<path d="m2.75 5.75 8.35 6.35q.9.7 1.8 0l8.35-6.35"/></g>')
    visual.extend([
        contact_link("Email hi@sdpkjc.com", "mailto:hi@sdpkjc.com", email, 84),
        contact_link("GitHub", "https://github.com/sdpkjc",
                     icon_geometry("github.svg", 19, 132, 210), 132),
        '<!-- Scholar: Academicons by James Walsh, SIL OFL 1.1. https://jpswalsh.github.io/academicons/ -->',
        contact_link("Google Scholar", "https://scholar.google.com/citations?user=Netm2wsAAAAJ",
                     icon_geometry("google-scholar-academicons.svg", 22, 180, 210), 180),
        contact_link("X", "https://twitter.com/sdpkjc_adam",
                     icon_geometry("x.svg", 18.5, 228, 210), 228),
        contact_link("LinkedIn", "https://www.linkedin.com/in/yanxiao-zhao/",
                     icon_geometry("linkedin.svg", 18, 276, 210), 276),
    ])
    definitions = [f'<path id="{key}" d="{path}"/>'
                   for font in (latin, chinese)
                   for key, path in font.definitions.items() if path]
    # Keep interaction styles inside the SVG so the standalone asset works as well.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" class="profile" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="group" aria-label="Profile links" fill="currentColor" color="{INK}">
<title>{ENGLISH_NAME} {CHINESE_NAME}</title>
<desc>{INTEREST}. {EDUCATION[0]}{EDUCATION[1]}. {EMPLOYMENT[0]}{EMPLOYMENT[1]}. Email, GitHub, Google Scholar, X and LinkedIn.</desc>
<style>
a {{ cursor: pointer; color: inherit; }}
.secondary {{ color: {INK}; fill: currentColor; }}
.contact-link {{ color: {SECONDARY_INK}; fill: currentColor; }}
.contact-link {{ transition: color 150ms ease-out; }}
.contact-link:hover, .contact-link:focus-visible {{ color: {INK}; }}
.hit {{ fill: transparent; }}
.underline, .focus-ring {{ fill: none; stroke: currentColor; stroke-width: 1; opacity: 0; pointer-events: none; }}
.text-link:hover .underline {{ opacity: 1; }}
a:focus {{ outline: none; }}
a:focus-visible .focus-ring {{ opacity: 1; }}
@media (prefers-reduced-motion: reduce) {{
    .contact-link {{ transition: none; }}
}}
@media (forced-colors: active) {{
    .profile, .secondary {{ color: CanvasText; }}
    a, .contact-link, .contact-link:hover, .contact-link:focus-visible {{ color: LinkText; }}
}}
</style>
<!-- Outlined Recursive Mono: MONO=1, CASL=0.2, wght=400, slnt=0, CRSV=0.
     Chinese: Sarasa Mono SC. Font license notices are retained in assets/fonts/. -->
<defs>
{chr(10).join(definitions)}
</defs>
{chr(10).join(visual)}
</svg>'''


def main():
    template = (ROOT / "scripts/profile-shell.html").read_text(encoding="utf-8")
    marker = "<!-- PROFILE_SVG -->"
    if template.count(marker) != 1:
        raise ValueError("Expected exactly one PROFILE_SVG marker")
    svg = build_svg()
    ET.fromstring(svg)  # Refuse malformed generated SVG before updating either output.
    (ROOT / "assets/profile.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
    (ROOT / "index.html").write_text(template.replace(marker, svg), encoding="utf-8", newline="\n")
    print("Generated assets/profile.svg and index.html")


if __name__ == "__main__":
    main()
