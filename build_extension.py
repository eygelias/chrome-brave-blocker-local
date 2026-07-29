from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILTERS = ROOT / "filters"
BUILD = ROOT / ".build"
BUILT_RULESETS = BUILD / "rulesets"
PACKED_RULESETS = BUILD / "packed-rulesets"
FIREFOX_RULESETS = BUILD / "firefox-rulesets"
FIREFOX_MAX_STATIC_RULES = 30_000
FIREFOX_RULE_BUDGETS = {1: 18_500, 2: 8_000, 3: 554, 4: 1_743, 5: 1_181, 6: 22}
CHROME = ROOT / "extension"
FIREFOX = ROOT / "firefox"
VENDOR = ROOT / "vendor"
DIST = ROOT / "dist"
SOURCE_CONFIG = ROOT / "filter_sources.json"
PACKAGE = ROOT / "package.json"

YOUTUBE_MATCHES = [
    "*://www.youtube.com/*",
    "*://m.youtube.com/*",
    "*://music.youtube.com/*",
    "*://tv.youtube.com/*",
    "*://www.youtubekids.com/*",
    "*://www.youtube-nocookie.com/*",
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> bytes:
    last_error = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 Brave-like-blocker-local-builder/3.0"},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
            if len(data) < 16 or b"<html" in data[:512].lower():
                raise ValueError("unexpected or empty filter response")
            return data
        except Exception as error:  # network errors vary by platform
            last_error = error
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"Failed to download {url}: {last_error}")


def prepare_filters(config: dict) -> tuple[list[str], list[dict]]:
    if FILTERS.exists():
        shutil.rmtree(FILTERS)
    FILTERS.mkdir(parents=True)
    metadata = []
    all_filter_text = []
    source_records = []
    ids = set()

    for group in config["groups"]:
        filter_id = int(group["id"])
        if filter_id in ids:
            raise ValueError(f"Duplicate filter group id: {filter_id}")
        ids.add(filter_id)

        chunks = [f"! Compiled group: {group['name']}"]
        group_record = {"id": filter_id, "name": group["name"], "sources": []}
        for source in group["sources"]:
            print(f"Downloading {source['name']}...")
            raw = download(source["url"])
            text = raw.decode("utf-8-sig", "replace").replace("\r\n", "\n")
            chunks.extend(["", f"! Source: {source['name']}", f"! URL: {source['url']}", text])
            all_filter_text.append(text)
            group_record["sources"].append(
                {
                    "name": source["name"],
                    "url": source["url"],
                    "bytes": len(raw),
                    "sha256": sha256(raw),
                }
            )

        combined = "\n".join(chunks).rstrip() + "\n"
        (FILTERS / f"filter_{filter_id}.txt").write_text(combined, encoding="utf-8")
        metadata.append(
            {
                "filterId": filter_id,
                "name": group["name"],
                "description": group["name"],
                "homepage": config["catalog"]["url"],
            }
        )
        source_records.append(group_record)

    # dnr-converter 1.x expects a JSON array, unlike old tsurlfilter CLI builds.
    write_json(FILTERS / "filters.json", metadata)
    return all_filter_text, source_records


def build_cosmetic_css(filter_texts: list[str]) -> tuple[str, int]:
    skipped_markers = (
        "#@#",
        "#?#",
        "#$#",
        "##+js",
        ":contains(",
        ":has-text(",
        ":matches-css",
        ":matches-attr(",
        ":matches-prop(",
        ":xpath(",
        ":upward(",
        ":remove(",
        ":remove-attr(",
        ":remove-class(",
        ":style(",
        "[-ext-",
    )
    unsafe_css = ("url(", "image-set(", "javascript:", "@import", "/*", "*/")
    selectors = []
    seen = set()

    for text in filter_texts:
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line.startswith("##") or any(marker in line for marker in skipped_markers):
                continue
            selector = line[2:].strip()
            lowered = selector.lower()
            if (
                not selector
                or selector.startswith(("^", "+js("))
                or selector in seen
                or len(selector) > 1000
                or any(char in selector for char in "{}\x00")
                or any(marker in lowered for marker in unsafe_css)
            ):
                continue
            seen.add(selector)
            selectors.append(selector)

    header = (
        "/* Generated generic cosmetic selectors. YouTube is excluded in manifest.\n"
        " * Security hardening mirrors Brave adblock-rust 0.12.4/0.12.5: no url() or image-set(). */\n"
    )
    css = header + "\n".join(f"{selector} {{ display: none !important; }}" for selector in selectors) + "\n"
    return css, len(selectors)


def run_converter() -> None:
    converter = ROOT / "scripts" / "convert_filters.mjs"
    node = shutil.which("node")
    if not node or not converter.is_file():
        raise RuntimeError("Build dependencies missing. Run: npm install")
    subprocess.run(
        [node, str(converter), str(FILTERS), str(BUILT_RULESETS)],
        cwd=ROOT,
        check=True,
    )


def chunk_rules(rules: list[dict], max_bytes: int = 4_500_000) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_bytes = 2  # JSON array brackets.
    for rule in rules:
        encoded_bytes = len(json.dumps(rule, separators=(",", ":")).encode("utf-8"))
        added_bytes = encoded_bytes + (1 if current else 0)
        if current and current_bytes + added_bytes > max_bytes:
            chunks.append(current)
            current = []
            current_bytes = 2
            added_bytes = encoded_bytes
        if current_bytes + added_bytes > max_bytes:
            raise ValueError(f"Single DNR rule exceeds {max_bytes} bytes")
        current.append(rule)
        current_bytes += added_bytes
    if current:
        chunks.append(current)
    return chunks


def collect_rulesets() -> list[dict]:
    if PACKED_RULESETS.exists():
        shutil.rmtree(PACKED_RULESETS)
    PACKED_RULESETS.mkdir(parents=True)

    rulesets = []
    for path in sorted(BUILT_RULESETS.glob("ruleset_*/ruleset_*.json")):
        match = re.fullmatch(r"ruleset_(\d+)", path.parent.name)
        if not match or int(match.group(1)) == 0:
            continue
        number = int(match.group(1))
        rules = load_json(path)
        if not isinstance(rules, list) or not rules:
            continue
        for rule in rules:
            if not isinstance(rule, dict):
                raise ValueError(f"Invalid DNR rule in {path}")
            rule.pop("metadata", None)
        # ponytail: obsolete Coinhive block signature is misread by Mozilla's linter as executable miner code.
        rules = [
            rule
            for rule in rules
            if not (
                rule.get("action", {}).get("type") == "block"
                and rule.get("condition", {}).get("urlFilter") == "/coinhive.min.js"
            )
        ]

        chunks = chunk_rules(rules)
        for chunk_number, chunk in enumerate(chunks, start=1):
            ruleset_id = f"ruleset_{number}" if len(chunks) == 1 else f"ruleset_{number}_{chunk_number}"
            output = PACKED_RULESETS / ruleset_id / f"{ruleset_id}.json"
            output.parent.mkdir(parents=True)
            output.write_text(json.dumps(chunk, separators=(",", ":")), encoding="utf-8")
            rulesets.append(
                {
                    "sort_key": (number, chunk_number),
                    "id": ruleset_id,
                    "source": output,
                    "count": len(chunk),
                    "regexp_count": sum("regexFilter" in rule.get("condition", {}) for rule in chunk),
                }
            )
    rulesets.sort(key=lambda item: item["sort_key"])
    if not rulesets:
        raise RuntimeError("DNR converter produced no usable rulesets")
    return rulesets


def evenly_sample(items: list[tuple[int, dict]], count: int) -> list[tuple[int, dict]]:
    if count >= len(items):
        return list(items)
    return [items[(index * len(items)) // count] for index in range(count)]


def select_firefox_group(rules: list[dict], budget: int) -> list[dict]:
    indexed = list(enumerate(rules))
    essential = [
        item
        for item in indexed
        if item[1].get("action", {}).get("type") != "block" or item[1].get("priority", 1) > 1
    ]
    selected = {index: rule for index, rule in evenly_sample(essential, min(budget, len(essential)))}
    remaining = budget - len(selected)
    if remaining <= 0:
        return [selected[index] for index in sorted(selected)]

    candidates = [item for item in indexed if item[0] not in selected]
    domain_rules = [
        item
        for item in candidates
        if item[1].get("condition", {}).get("urlFilter", "").startswith("||")
        or item[1].get("condition", {}).get("requestDomains")
    ]
    domain_indices = {item[0] for item in domain_rules}
    generic_rules = [item for item in candidates if item[0] not in domain_indices]
    for index, rule in evenly_sample(domain_rules, min(len(domain_rules), int(remaining * 0.7))):
        selected[index] = rule
    remaining = budget - len(selected)
    for index, rule in evenly_sample(generic_rules, min(len(generic_rules), remaining)):
        selected[index] = rule
    remaining = budget - len(selected)
    leftovers = [item for item in indexed if item[0] not in selected]
    for index, rule in evenly_sample(leftovers, min(len(leftovers), remaining)):
        selected[index] = rule
    return [selected[index] for index in sorted(selected)]


def build_firefox_rulesets(rulesets: list[dict]) -> tuple[list[dict], dict]:
    if FIREFOX_RULESETS.exists():
        shutil.rmtree(FIREFOX_RULESETS)
    FIREFOX_RULESETS.mkdir(parents=True)

    grouped: dict[int, list[dict]] = {}
    for item in rulesets:
        match = re.fullmatch(r"ruleset_(\d+)(?:_\d+)?", item["id"])
        if not match:
            raise ValueError(f"Unexpected ruleset id: {item['id']}")
        grouped.setdefault(int(match.group(1)), []).extend(load_json(item["source"]))

    essential_counts = {
        number: sum(
            rule.get("action", {}).get("type") != "block" or rule.get("priority", 1) > 1
            for rule in source_rules
        )
        for number, source_rules in grouped.items()
    }
    if sum(essential_counts.values()) > FIREFOX_MAX_STATIC_RULES:
        raise ValueError("Firefox essential rules exceed its static-rule limit")

    budgets = {
        number: min(
            len(source_rules),
            max(FIREFOX_RULE_BUDGETS.get(number, 0), essential_counts[number]),
        )
        for number, source_rules in grouped.items()
    }
    excess = sum(budgets.values()) - FIREFOX_MAX_STATIC_RULES
    donor_order = [number for number in (5, 6, 1, 4, 3, 2) if number in grouped]
    donor_order.extend(number for number in sorted(grouped) if number not in donor_order)
    if excess > 0:
        for number in donor_order:
            reduction = min(excess, budgets[number] - essential_counts[number])
            budgets[number] -= reduction
            excess -= reduction
            if excess == 0:
                break
    if excess > 0:
        raise ValueError("Unable to fit Firefox essential rules within its static-rule limit")

    spare = FIREFOX_MAX_STATIC_RULES - sum(budgets.values())
    recipient_order = [number for number in (1, 2, 4, 3, 5, 6) if number in grouped]
    recipient_order.extend(number for number in sorted(grouped) if number not in recipient_order)
    for number in recipient_order:
        addition = min(spare, len(grouped[number]) - budgets[number])
        budgets[number] += addition
        spare -= addition
        if spare == 0:
            break

    selected_rulesets = []
    group_report = []
    for number in sorted(grouped):
        source_rules = grouped[number]
        budget = budgets[number]
        selected = select_firefox_group(source_rules, budget)
        essential_ids = {
            rule["id"]
            for rule in source_rules
            if rule.get("action", {}).get("type") != "block" or rule.get("priority", 1) > 1
        }
        selected_ids = {rule["id"] for rule in selected}
        if not essential_ids.issubset(selected_ids):
            raise ValueError(f"Firefox selection dropped an essential rule from group {number}")
        group_report.append(
            {
                "group": number,
                "available": len(source_rules),
                "essential": len(essential_ids),
                "target_budget": FIREFOX_RULE_BUDGETS.get(number, 0),
                "budget": budget,
                "selected": len(selected),
            }
        )
        chunks = chunk_rules(selected)
        for chunk_number, chunk in enumerate(chunks, start=1):
            ruleset_id = f"ruleset_{number}_fx" if len(chunks) == 1 else f"ruleset_{number}_fx_{chunk_number}"
            output = FIREFOX_RULESETS / ruleset_id / f"{ruleset_id}.json"
            output.parent.mkdir(parents=True)
            output.write_text(json.dumps(chunk, separators=(",", ":")), encoding="utf-8")
            selected_rulesets.append(
                {
                    "sort_key": (number, chunk_number),
                    "id": ruleset_id,
                    "source": output,
                    "count": len(chunk),
                    "regexp_count": sum("regexFilter" in rule.get("condition", {}) for rule in chunk),
                }
            )

    selected_total = sum(item["count"] for item in selected_rulesets)
    if selected_total > FIREFOX_MAX_STATIC_RULES:
        raise ValueError(f"Firefox rules exceed its {FIREFOX_MAX_STATIC_RULES} static-rule limit")
    return selected_rulesets, {
        "limit": FIREFOX_MAX_STATIC_RULES,
        "selected": selected_total,
        "strategy": "all non-block/high-priority rules, then evenly sampled domain and generic block rules",
        "groups": group_report,
        "source": "https://github.com/mozilla-firefox/firefox/blob/main/toolkit/components/extensions/ExtensionDNRLimits.sys.mjs",
    }


def manifest(version: str, rulesets: list[dict], target: str) -> dict:
    rule_resources = [
        {
            "id": item["id"],
            "enabled": True,
            "path": f"rulesets/{item['id']}/{item['id']}.json",
        }
        for item in rulesets
    ]
    value = {
        "manifest_version": 3,
        "name": f"Brave-like Blocker Local ({target})",
        "version": version,
        "description": "Bloqueador local inspirado en Brave | Local ad/tracker blocker inspired by Brave.",
        "homepage_url": "https://github.com/eygelias/chrome-brave-blocker-local",
        "permissions": ["declarativeNetRequest"],
        "host_permissions": ["<all_urls>"],
        "declarative_net_request": {"rule_resources": rule_resources},
        "content_scripts": [
            {
                "matches": ["<all_urls>"],
                "exclude_matches": YOUTUBE_MATCHES,
                "css": ["cosmetic.css"],
                "run_at": "document_start",
            },
            {
                "matches": YOUTUBE_MATCHES,
                "js": ["yt-main.js"],
                "run_at": "document_start",
                "all_frames": False,
                "world": "MAIN",
            },
            {
                "matches": ["*://m.youtube.com/*"],
                "js": ["brave-yt-sabr-fix.js"],
                "run_at": "document_start",
                "all_frames": False,
                "world": "MAIN",
            },
        ],
    }
    if target == "Chrome":
        value["minimum_chrome_version"] = "120"
    else:
        value["browser_specific_settings"] = {
            "gecko": {
                "id": "brave-like-blocker-local@eygelias.github.io",
                "data_collection_permissions": {"required": ["none"]},
                "strict_min_version": "142.0",
            }
        }
    return value


def copy_rulesets(target: Path, rulesets: list[dict]) -> None:
    destination = target / "rulesets"
    if destination.exists():
        shutil.rmtree(destination)
    for item in rulesets:
        folder = destination / item["id"]
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item["source"], folder / f"{item['id']}.json")


def write_targets(
    version: str,
    config: dict,
    rulesets: list[dict],
    cosmetic_css: str,
    cosmetic_count: int,
    source_records: list[dict],
) -> dict:
    canonical_youtube = CHROME / "yt-main.js"
    sabr_source = VENDOR / "brave-yt-sabr-fix.js"
    notices = ROOT / "THIRD_PARTY_NOTICES.md"
    project_license = ROOT / "LICENSE"
    mpl_license = ROOT / "LICENSES" / "MPL-2.0.txt"
    if not canonical_youtube.is_file() or not sabr_source.is_file():
        raise FileNotFoundError("Missing canonical YouTube scripts")
    if not all(path.is_file() for path in (notices, project_license, mpl_license)):
        raise FileNotFoundError("Missing project or third-party license files")

    firefox_rulesets, firefox_selection = build_firefox_rulesets(rulesets)
    if FIREFOX.exists():
        shutil.rmtree(FIREFOX)
    FIREFOX.mkdir(parents=True)
    CHROME.mkdir(parents=True, exist_ok=True)

    copy_rulesets(CHROME, rulesets)
    copy_rulesets(FIREFOX, firefox_rulesets)
    for target in (CHROME, FIREFOX):
        (target / "cosmetic.css").write_text(cosmetic_css, encoding="utf-8")
        shutil.copy2(sabr_source, target / "brave-yt-sabr-fix.js")
        (target / "LICENSES").mkdir(parents=True, exist_ok=True)
        shutil.copy2(project_license, target / "LICENSE")
        shutil.copy2(notices, target / "THIRD_PARTY_NOTICES.md")
        shutil.copy2(mpl_license, target / "LICENSES" / "MPL-2.0.txt")
    shutil.copy2(canonical_youtube, FIREFOX / "yt-main.js")

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    conversion_report_path = BUILT_RULESETS / "conversion-report.json"
    conversion_report = load_json(conversion_report_path) if conversion_report_path.is_file() else {}
    base_info = {
        "version": version,
        "generated_at": generated_at,
        "upstream": config["catalog"],
        "filter_groups": source_records,
        "dnr_converter": "@adguard/dnr-converter 1.1.0",
        "conversion_report": conversion_report,
        "cosmetic_rules": cosmetic_count,
    }

    def target_info(target_rulesets: list[dict], selection: dict | None = None) -> dict:
        info = {
            **base_info,
            "network_rules": sum(item["count"] for item in target_rulesets),
            "regexp_rules": sum(item["regexp_count"] for item in target_rulesets),
            "rulesets": [{"id": item["id"], "rules": item["count"]} for item in target_rulesets],
        }
        if selection:
            info["firefox_rule_selection"] = selection
        return info

    chrome_info = target_info(rulesets)
    firefox_info = target_info(firefox_rulesets, firefox_selection)
    write_json(CHROME / "manifest.json", manifest(version, rulesets, "Chrome"))
    write_json(CHROME / "build-info.json", chrome_info)
    write_json(FIREFOX / "manifest.json", manifest(version, firefox_rulesets, "Firefox"))
    write_json(FIREFOX / "build-info.json", firefox_info)
    return {
        "version": version,
        "generated_at": generated_at,
        "chrome": {"network_rules": chrome_info["network_rules"], "rulesets": chrome_info["rulesets"]},
        "firefox": {
            "network_rules": firefox_info["network_rules"],
            "rulesets": firefox_info["rulesets"],
            "selection": firefox_selection,
        },
    }


URL_SAFETY_SAMPLES = (
    ("http://a.invalid/", "http://example.org/path", "http://127.0.0.1:8080/q?x=1", "http://localhost/"),
    ("https://b.invalid/", "https://sample.net/deep/file.js", "https://192.0.2.1:8443/q?y=2", "https://localhost/"),
    ("ws://c.invalid/socket", "ws://example.org/live", "ws://198.51.100.1:8080/feed", "ws://localhost/channel"),
    ("wss://d.invalid/socket", "wss://sample.net/live", "wss://203.0.113.1:8443/feed", "wss://localhost/channel"),
)


def _url_filter_regex(url_filter: str, case_sensitive: bool) -> re.Pattern:
    pattern = url_filter
    left_anchored = pattern.startswith("|")
    if left_anchored:
        pattern = pattern[1:]
    right_anchored = pattern.endswith("|")
    if right_anchored:
        pattern = pattern[:-1]
    parts = []
    for char in pattern:
        if char == "*":
            parts.append(".*")
        elif char == "^":
            parts.append(r"(?:[^a-z0-9_\-.%]|$)")
        else:
            parts.append(re.escape(char))
    expression = f"{'^' if left_anchored else ''}{''.join(parts)}{'$' if right_anchored else ''}"
    return re.compile(expression, 0 if case_sensitive else re.IGNORECASE)


def is_unsafe_unscoped_block(rule: dict) -> bool:
    if rule.get("action", {}).get("type") != "block":
        return False
    condition = rule.get("condition", {})
    if condition.get("requestDomains") or condition.get("initiatorDomains"):
        return False
    # ponytail: unscoped regex blocks fail closed; Python's regex engine cannot prove RE2 scope safely.
    if "regexFilter" in condition:
        return True
    url_filter = condition.get("urlFilter")
    if not isinstance(url_filter, str):
        return True
    literal = re.sub(r"[|*^]", "", url_filter)
    if not literal or literal in {":", "://", "//", "."}:
        return True
    if url_filter.startswith("||"):
        return False
    matcher = _url_filter_regex(url_filter, bool(condition.get("isUrlFilterCaseSensitive")))
    return any(all(matcher.search(url) for url in urls) for urls in URL_SAFETY_SAMPLES)


def validate_target(target: Path, expected_version: str) -> dict:
    manifest_path = target / "manifest.json"
    data = load_json(manifest_path)
    if data.get("manifest_version") != 3 or data.get("version") != expected_version:
        raise ValueError(f"Invalid manifest version in {manifest_path}")
    if len(data.get("description", "")) > 132:
        raise ValueError(f"Manifest description exceeds Chrome limit: {manifest_path}")

    total = 0
    regexp_total = 0
    resources = data["declarative_net_request"]["rule_resources"]
    max_enabled_rulesets = 20 if target == FIREFOX else 50
    if len(resources) > max_enabled_rulesets:
        raise ValueError(f"Too many enabled static rulesets in {manifest_path}")
    for resource in resources:
        path = target / resource["path"]
        if path.stat().st_size > 4_500_000:
            raise ValueError(f"Ruleset exceeds package/linter size target: {path}")
        rules = load_json(path)
        if not isinstance(rules, list) or not rules:
            raise ValueError(f"Empty ruleset: {path}")
        ids = set()
        for rule in rules:
            if "metadata" in rule:
                raise ValueError(f"Converter metadata leaked into {path}")
            rule_id = rule.get("id")
            if not isinstance(rule_id, int) or rule_id <= 0 or rule_id in ids:
                raise ValueError(f"Invalid or duplicate rule id in {path}: {rule_id}")
            ids.add(rule_id)
            if not isinstance(rule.get("action"), dict) or not isinstance(rule.get("condition"), dict):
                raise ValueError(f"Invalid DNR rule shape in {path}: {rule_id}")
            condition = rule["condition"]
            if is_unsafe_unscoped_block(rule):
                raise ValueError(f"Unsafe unscoped universal block rule in {path}: {rule_id}")
            if "regexFilter" in condition:
                regexp_total += 1
        total += len(rules)

    for content_script in data.get("content_scripts", []):
        for key in ("js", "css"):
            for relative in content_script.get(key, []):
                if not (target / relative).is_file():
                    raise FileNotFoundError(f"Manifest references missing file: {target / relative}")

    node = shutil.which("node")
    if not node:
        raise RuntimeError("node is required for JavaScript syntax checks")
    for script in sorted(target.glob("*.js")):
        subprocess.run([node, "--check", str(script)], check=True, capture_output=True, text=True)

    info = load_json(target / "build-info.json")
    if info.get("network_rules") != total or info.get("version") != expected_version:
        raise ValueError(f"Build metadata mismatch in {target}")
    return {"target": target.name, "network_rules": total, "regexp_rules": regexp_total}


def validate_all() -> list[dict]:
    version = load_json(PACKAGE)["version"]
    results = [validate_target(CHROME, version), validate_target(FIREFOX, version)]
    firefox_manifest = load_json(FIREFOX / "manifest.json")
    if not firefox_manifest.get("browser_specific_settings", {}).get("gecko", {}).get("id"):
        raise ValueError("Firefox manifest needs a stable Gecko extension id")
    firefox_result = next(result for result in results if result["target"] == FIREFOX.name)
    firefox_info = load_json(FIREFOX / "build-info.json")
    if firefox_result["network_rules"] > FIREFOX_MAX_STATIC_RULES:
        raise ValueError(f"Firefox exceeds its {FIREFOX_MAX_STATIC_RULES} static-rule limit")
    if firefox_info.get("firefox_rule_selection", {}).get("selected") != firefox_result["network_rules"]:
        raise ValueError("Firefox selection metadata mismatch")
    return results


def zip_tree(source: Path, output: Path, prefix: str = "") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(item for item in source.rglob("*") if item.is_file()):
            relative = path.relative_to(source).as_posix()
            archive.write(path, f"{prefix}/{relative}" if prefix else relative)


def package_extensions() -> list[dict]:
    version = load_json(PACKAGE)["version"]
    DIST.mkdir(parents=True, exist_ok=True)
    outputs = [
        (CHROME, DIST / f"chrome-brave-blocker-local-v{version}.zip", "extension"),
        (FIREFOX, DIST / f"firefox-brave-blocker-local-v{version}.zip", "firefox"),
        (FIREFOX, DIST / f"firefox-brave-blocker-local-v{version}-unsigned.xpi", ""),
    ]
    records = []
    for source, output, prefix in outputs:
        zip_tree(source, output, prefix)
        raw = output.read_bytes()
        records.append({"file": str(output), "bytes": len(raw), "sha256": sha256(raw)})
    return records


def build() -> dict:
    package = load_json(PACKAGE)
    config = load_json(SOURCE_CONFIG)
    filter_texts, source_records = prepare_filters(config)
    cosmetic_css, cosmetic_count = build_cosmetic_css(filter_texts)
    run_converter()
    rulesets = collect_rulesets()
    info = write_targets(
        package["version"],
        config,
        rulesets,
        cosmetic_css,
        cosmetic_count,
        source_records,
    )
    info["validated_targets"] = validate_all()
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Chrome and Firefox Brave-like blocker packages")
    parser.add_argument("--check", action="store_true", help="validate existing generated extensions")
    parser.add_argument("--package", action="store_true", help="create distributable ZIP/XPI files")
    args = parser.parse_args()

    result = {"validated_targets": validate_all()} if args.check else build()
    if args.package:
        result["packages"] = package_extensions()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
