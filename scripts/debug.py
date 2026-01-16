"""Debug script to check sitemap.xml content"""

from pathlib import Path

sitemap_path = Path(__file__).parent / "sitemap.xml"

print(f"Reading: {sitemap_path}")
print(f"File exists: {sitemap_path.exists()}")

if sitemap_path.exists():
    with open(sitemap_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"\nFile size: {len(content)} characters")
    print(f"\nFirst 500 characters:")
    print(repr(content[:500]))

    lines = content.split("\n")
    print(f"\nTotal lines: {len(lines)}")
    print(f"\nFirst 10 lines:")
    for i, line in enumerate(lines[:10], 1):
        print(f"{i}: {repr(line)}")

    # Count URLs
    url_count = sum(1 for line in lines if "https://" in line)
    print(f"\nLines containing 'https://': {url_count}")
