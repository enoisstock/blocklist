from pathlib import Path
import re

root = Path(r"c:\Users\eteck\OneDrive\Desktop\blocklisten")
exclude = {"blocklisten_adblock_all.txt"}


def normalize_domain(raw: str):
    line = raw.strip()
    if not line or line.startswith("!") or line.startswith("#") or line.startswith(";"):
        return None
    if line.startswith("[") and line.endswith("]"):
        return None
    if line.startswith("@@"):
        return None
    # hostfile: 0.0.0.0 example.com
    m = re.match(r"^(?:0\.0\.0\.0|127\.0\.0\.1|::1)\s+(.+)$", line, flags=re.I)
    if m:
        line = m.group(1)
    # adblock rule: ||example.com^
    if line.startswith("||") and line.endswith("^"):
        line = line[2:-1]
    # strip scheme / path / query
    if line.startswith(("http://", "https://")):
        line = line.split("//", 1)[1]
    line = line.split("/", 1)[0]
    line = line.split("?", 1)[0]
    line = line.split("#", 1)[0]
    line = line.strip(" .\"'\\")
    if not line:
        return None
    if line.startswith("."):
        line = line[1:]
    if line.endswith("."):
        line = line[:-1]
    if line.startswith(("*", "/", "$")):
        return None
    if any(ch in line for ch in " /?#@\\"):
        return None
    if not re.fullmatch(r"[A-Za-z0-9.-]+", line):
        return None
    if line.count(".") < 1 or len(line) < 4:
        return None
    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", line):
        return None
    if "_" in line:
        return None
    if line.lower().startswith(("localhost", "example", "invalid", "test")):
        return None
    if line.lower().endswith((".local", ".internal", ".localhost")):
        return None
    return line.lower()


def adblock_rule(domain: str) -> str:
    return "||" + domain + "^"

# Clean each individual file and keep comments + headers at the top
all_domains = set()
for path in sorted(root.glob("*.txt")):
    if path.name in exclude:
        continue

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    kept_comments = []
    domains = set()
    for line in lines:
        if not line.strip():
            continue
        if line.strip().startswith("!") or line.strip().startswith("#"):
            kept_comments.append(line)
            continue
        domain = normalize_domain(line)
        if domain:
            domains.add(domain)

    unique_sorted = sorted(domains)
    out = []
    # Preserve a compact header block
    out.append("[Adblock Plus 1.2]")
    out.append("! Cleaned and deduplicated")
    out.append("! Source: " + path.name)
    out.append("!")
    out.extend(adblock_rule(d) for d in unique_sorted)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    all_domains.update(unique_sorted)

# Unified export
export_path = root / "blocklisten_adblock_all.txt"
combined = sorted(all_domains)
export_lines = [
    "[Adblock Plus 1.2]",
    "! Title: Unified Clean Adblock List",
    "! Description: deduplicated, alphabetized, and sanitized rules",
    "!",
]
export_lines.extend(adblock_rule(d) for d in combined)
export_path.write_text("\n".join(export_lines) + "\n", encoding="utf-8")

print(f"cleaned_files={len(list(root.glob('*.txt'))) - 1}")
print(f"unique_domains={len(combined)}")
print(f"export={export_path.name}")
