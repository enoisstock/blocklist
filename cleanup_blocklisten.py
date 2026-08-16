from pathlib import Path
import re
from datetime import datetime

root = Path(r"c:\Users\eteck\OneDrive\Desktop\blocklisten")


def normalize_candidate(raw: str):
    line = raw.strip()
    if not line or line.startswith(("!", "#", ";")):
        return None
    if line.startswith("[") and line.endswith("]"):
        return None

    if line.startswith(("0.0.0.0", "127.0.0.1", "::1")):
        parts = line.split(None, 1)
        if len(parts) == 2:
            line = parts[1]
    if line.startswith("||") and line.endswith("^"):
        line = line[2:-1]
    if line.startswith("@@"):
        return None
    if line.startswith("/") or line.startswith("."):
        return None

    line = line.strip(" \\").strip("'")
    line = line.replace("http://", "").replace("https://", "")
    line = line.replace("www.", "", 1) if line.startswith("www.") else line
    line = line.split("/", 1)[0]
    line = line.split("?", 1)[0]
    line = line.split("#", 1)[0]
    line = line.strip(".")
    line = line.strip()

    if not line or any(ch in line for ch in " /?#@\\"):
        return None
    if line.startswith("*."):
        line = line[2:]
    if line.startswith("."):
        line = line.lstrip(".")
    if line.endswith("."):
        line = line.rstrip(".")
    if not re.fullmatch(r"[A-Za-z0-9.-]+", line):
        return None
    if line.count(".") < 1:
        return None
    if line.startswith(("localhost", "example", "invalid")):
        return None
    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", line):
        return None
    if "_" in line:
        return None
    if line.startswith(".") or line.endswith("."):
        return None
    if len(line) < 4:
        return None
    if line.split(".")[-1].lower() in {"local", "internal", "localhost"}:
        return None
    return line.lower()


def canonical_adblock_rule(domain: str) -> str:
    return f"||{domain}^"


all_domains = set()
for file_path in sorted(root.glob("*.txt")):
    domains = set()
    for raw in file_path.read_text(encoding="utf-8", errors="replace").splitlines():
        dom = normalize_candidate(raw)
        if dom:
            domains.add(dom)
    all_domains |= domains

    sorted_domains = sorted(domains)
    output = [
        "[Adblock Plus 1.2]",
        "! Title: Cleaned Domain List",
        f"! Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "! Filter: unique domains only, sorted alphabetically",
        "!",
    ]
    output.extend(canonical_adblock_rule(d) for d in sorted_domains)
    file_path.write_text("\n".join(output) + "\n", encoding="utf-8")

combined = sorted(all_domains)
combined_output = [
    "[Adblock Plus 1.2]",
    "! Title: Unified Clean Adblock List",
    f"! Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    "! Description: Deduplicated, sorted, and sanitized domains from all workspace blocklists",
    "!",
]
combined_output.extend(canonical_adblock_rule(d) for d in combined)
(root / "blocklisten_adblock_all.txt").write_text("\n".join(combined_output) + "\n", encoding="utf-8")

print(f"Files processed: {len(list(root.glob('*.txt')))}")
print(f"Unique domains written: {len(combined)}")
print(f"Combined export: {root / 'blocklisten_adblock_all.txt'}")
