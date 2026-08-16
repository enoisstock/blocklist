from pathlib import Path
import re

root = Path(r"c:\Users\eteck\OneDrive\Desktop\blocklisten")


def normalize_rule(raw: str):
    s = raw.strip()
    if not s:
        return None
    if s.startswith("!") or s.startswith("#") or s.startswith(";"):
        return None

    # Strip common hostfile prefixes like "0.0.0.0" or "127.0.0.1"
    if re.match(r"^(0\.0\.0\.0|127\.0\.0\.1|::1)\s+", s, re.I):
        s = re.sub(r"^(0\.0\.0\.0|127\.0\.0\.1|::1)\s+", "", s, flags=re.I)

    # Strip Adblock-style wrappers
    if s.startswith("||") and s.endswith("^"):
        s = s[2:-1]

    # Strip likely invalid rule patterns
    if s.startswith("@@") or s.startswith("/") or s.startswith("$"):
        return None
    if " " in s:
        # keep only plain host/domain entries if space-separated hostfile format
        parts = s.split()
        if len(parts) == 2:
            s = parts[1]
        else:
            return None

    s = s.replace("http://", "").replace("https://", "")
    s = s.replace("www.", "", 1) if s.startswith("www.") else s
    s = s.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    s = s.strip(". \")

    if not s or s.startswith(".") or s.endswith("."):
        return None
    if any(ch in s for ch in " /?#@\\"):
        return None
    if s.startswith("*"):
        s = s[1:]
    if s.startswith("."):
        s = s[1:]
    if len(s) < 4:
        return None
    if "_" in s:
        return None
    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", s):
        return None
    if not re.fullmatch(r"[A-Za-z0-9.-]+", s):
        return None
    if s.count(".") < 1:
        return None

    # Keep only domain names after stripping TLD edge cases
    if s.lower().startswith(("localhost", "example", "invalid", "test")):
        return None
    if s.lower().endswith((".local", ".internal", ".localhost")):
        return None

    return s.lower()


def format_rule(domain: str) -> str:
    return f"||{domain}^"


all_domains = set()
for file in sorted(root.glob("*.txt")):
    if file.name == "blocklisten_adblock_all.txt":
        continue

    lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
    comments = []
    rules = []

    for line in lines:
        if not line.strip():
            continue
        if line.lstrip().startswith("!") or line.lstrip().startswith("#"):
            comments.append(line)
            continue
        domain = normalize_rule(line)
        if domain:
            rules.append(domain)

    unique_sorted = sorted(set(rules))
    cleaned_lines = []
    seen_comment = set()
    for comment in comments:
        c = comment.strip()
        if c and c not in seen_comment:
            cleaned_lines.append(comment)
            seen_comment.add(c)
    cleaned_lines.extend(format_rule(d) for d in unique_sorted)

    file.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")
    all_domains.update(unique_sorted)

combined = sorted(all_domains)
export_path = root / "blocklisten_adblock_all.txt"
export_lines = [
    "[Adblock Plus 1.2]",
    "! Title: Unified Clean Adblock List",
    "! Description: deduplicated, sorted, and sanitized domains from all blocklist files",
    "!",
]
export_lines.extend(format_rule(d) for d in combined)
export_path.write_text("\n".join(export_lines) + "\n", encoding="utf-8")

print(f"Processed files: {len(list(root.glob('*.txt')))-1}")
print(f"Unique domains across all files: {len(combined)}")
print(f"Export file: {export_path.name}")
PY