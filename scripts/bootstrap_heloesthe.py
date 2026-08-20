#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")

TEXT_EXTS = {".html", ".js", ".css", ".json", ".webmanifest", ".txt", ".md"}

REPLACEMENTS = [
    ("Simulados da Ana e Dani", "HeloeSthe"),
    ("Simulados Ana e Dani", "HeloeSthe"),
    ("Ana e Dani", "Helo e Sthe"),
    ("Ana & Dani", "Helo & Sthe"),
    ("Ana/Dani", "Helo/Sthe"),
    ("para estudar ouvindo Anavitória 🎧", "Feito com afeto, para vocês. Estou na torcida!"),
    ("para estudar ouvindo Anavitória", "Feito com afeto, para vocês. Estou na torcida!"),
    ("ana-dani-question-images-v1", "heloesthe-question-images-v1"),
    ("danieana-image-support", "heloesthe-image-support"),
]


def replace_text(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def namespace_local_storage(html: str) -> str:
    marker = "heloesthe-local-storage-namespace"
    if marker in html:
        return html
    shim = r'''<script id="heloesthe-local-storage-namespace">
(()=>{
  const PREFIX="heloesthe:";
  const p=Storage.prototype;
  const get=p.getItem, set=p.setItem, rem=p.removeItem;
  p.getItem=function(k){return get.call(this,this===localStorage && !String(k).startsWith(PREFIX)?PREFIX+k:k)};
  p.setItem=function(k,v){return set.call(this,this===localStorage && !String(k).startsWith(PREFIX)?PREFIX+k:k,v)};
  p.removeItem=function(k){return rem.call(this,this===localStorage && !String(k).startsWith(PREFIX)?PREFIX+k:k)};
})();
</script>'''
    pos = html.lower().find("</head>")
    if pos < 0:
        raise SystemExit("HeloeSthe bootstrap: </head> not found in index.html")
    return html[:pos] + shim + "\n" + html[pos:]


def patch_sw(text: str) -> str:
    # Cache Storage belongs to the whole github.io origin, not to a path.
    # Prefix common cache-name declarations so Dani&Ana and HeloeSthe cannot evict each other.
    def repl(m: re.Match) -> str:
        prefix, quote, value = m.group(1), m.group(2), m.group(3)
        if value.startswith("heloesthe-"):
            return m.group(0)
        return f"{prefix}{quote}heloesthe-{value}{quote}"

    text = re.sub(
        r"((?:CACHE(?:_NAME)?|CACHE_NAME|STATIC_CACHE|APP_CACHE)\s*=\s*)([\"'])([^\"']+)(?:\2)",
        repl,
        text,
        flags=re.I,
    )
    return text


def patch_manifest(path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    data["name"] = "HeloeSthe — Simulados de Humanas"
    data["short_name"] = "HeloeSthe"
    if isinstance(data.get("description"), str):
        data["description"] = "Feito com afeto, para vocês. Estou na torcida!"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    index = ROOT / "index.html"
    if not index.exists():
        raise SystemExit(f"HeloeSthe bootstrap: index.html not found under {ROOT}")

    changed = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = replace_text(text)
        if path.name == "index.html":
            new = namespace_local_storage(new)
        if path.name == "sw.js":
            new = patch_sw(new)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed += 1

    for name in ("manifest.json", "manifest.webmanifest"):
        p = ROOT / name
        if p.exists():
            patch_manifest(p)

    html = index.read_text(encoding="utf-8")
    required = [
        "HeloeSthe",
        "Feito com afeto, para vocês. Estou na torcida!",
        "heloesthe-local-storage-namespace",
    ]
    missing = [x for x in required if x not in html]
    if missing:
        raise SystemExit(f"HeloeSthe bootstrap validation failed; missing {missing}")
    if "Simulados da Ana e Dani" in html:
        raise SystemExit("HeloeSthe bootstrap validation failed; Dani&Ana branding remains in index.html")

    print(f"HeloeSthe bootstrap complete. Text files changed: {changed}")


if __name__ == "__main__":
    main()
