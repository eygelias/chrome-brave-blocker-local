import json, re, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILTERS = ROOT / "filters"
RES = ROOT / "resources"
EXT = ROOT / "extension"
RULESETS = EXT / "rulesets"
for p in (FILTERS, RES, EXT):
    p.mkdir(parents=True, exist_ok=True)

lists = [
    (1, "EasyList", "https://easylist.to/easylist/easylist.txt"),
    (2, "EasyPrivacy", "https://easylist.to/easylist/easyprivacy.txt"),
    (3, "uBlock filters", "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/filters.txt"),
    (4, "uBlock badware", "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/badware.txt"),
    (5, "uBlock privacy", "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/privacy.txt"),
    (6, "uBlock quick fixes", "https://raw.githubusercontent.com/uBlockOrigin/uAssets/master/filters/quick-fixes.txt"),
]

metadata = []
all_filter_text = []
for fid, name, url in lists:
    out = FILTERS / f"filter_{fid}.txt"
    print(f"Downloading {name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome Brave-like-blocker-builder"})
    data = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    out.write_text(data, encoding="utf-8")
    metadata.append({"filterId": fid, "name": name, "url": url})
    all_filter_text.append(data)
(FILTERS / "filters.json").write_text(json.dumps({"filters": metadata}, indent=2), encoding="utf-8")

# Convert network rules to Chrome MV3 declarativeNetRequest.
if RULESETS.exists():
    import shutil; shutil.rmtree(RULESETS)
subprocess.run(["npx.cmd", "tsurlfilter", "convert", str(FILTERS), "/resources", str(RULESETS), "--prettify-json", "false"], cwd=ROOT, check=True)

# Build cosmetic CSS: generic ABP cosmetic rules only. Skip procedural/scriptlet rules.
skip = ("#@#", "#?#", "#$#", "##+js", ":contains(", ":matches-css", ":xpath", ":style(", "[-ext-")
css_rules, seen = [], set()
for text in all_filter_text:
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("!") or any(s in line for s in skip):
            continue
        if line.startswith("##"):
            selector = line[2:].strip()
            if not selector or selector in seen or len(selector) > 500:
                continue
            # ponytail: Chrome CSS gets generic cosmetic rules; domain/procedural rules need a real adblock engine.
            if re.search(r"[:](?:has-text|contains|matches-css|xpath|upward|remove)\(", selector):
                continue
            seen.add(selector)
            css_rules.append(f"{selector} {{ display: none !important; }}")

cosmetic = "/* Generated from EasyList/uBlock generic cosmetic rules. */\n" + "\n".join(css_rules) + "\n"
(EXT / "cosmetic.css").write_text(cosmetic, encoding="utf-8")

# Collect rule_resources. Ignore AdGuard metadata ruleset for Chrome DNR.
rule_resources = []
for js in sorted(RULESETS.glob("*/**/*.json")):
    rel = js.relative_to(EXT).as_posix()
    try:
        arr = json.loads(js.read_text(encoding="utf-8"))
    except Exception:
        continue
    if not isinstance(arr, list) or not arr:
        continue
    if not isinstance(arr[0], dict) or "condition" not in arr[0] or "action" not in arr[0]:
        continue
    # Skip converter metadata ruleset; Chrome DNR rejects extra metadata field.
    if js.parent.name == "ruleset_0":
        continue
    for rule in arr:
        rule.pop("metadata", None)
    js.write_text(json.dumps(arr, separators=(",", ":")), encoding="utf-8")
    rid = js.parent.name
    rule_resources.append({"id": rid, "enabled": True, "path": rel})

manifest = {
    "manifest_version": 3,
    "name": "Brave-like Blocker for Chrome (Local)",
    "version": "1.1.0",
    "description": "Local MV3 blocker using EasyList/EasyPrivacy/uBlock lists, recreating Brave Shields behavior as far as Chrome allows.",
    "permissions": ["declarativeNetRequest"],
    "host_permissions": ["<all_urls>"],
    "declarative_net_request": {"rule_resources": rule_resources},
    "content_scripts": [{
        "matches": ["<all_urls>"],
        "css": ["cosmetic.css"],
        "js": ["youtube.js"],
        "run_at": "document_start"
    }]
}
(EXT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

rule_count = 0
for rr in rule_resources:
    arr = json.loads((EXT / rr["path"]).read_text(encoding="utf-8"))
    rule_count += len(arr)
print(json.dumps({
    "extension": str(EXT),
    "rulesets": len(rule_resources),
    "network_rules": rule_count,
    "cosmetic_rules": len(css_rules),
}, indent=2))
