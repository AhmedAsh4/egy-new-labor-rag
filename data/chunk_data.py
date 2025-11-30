import json
import re

from arabic_reshaper import reshape
from bidi.algorithm import get_display

with open(r"data\files\labor law.txt", "r", encoding="utf-8") as f:
    text = f.read()

pattern1 = r"\(\s*ﺍﳌﺎﺩﺓ\s+([^)]+)\)"  # ( مادة ordinal )
pattern2 = r"ﻣﺎﺩﺓ\s*\(\s*([^)]+)\)\s*:"  # مادة (digit):

matches = []

for match in re.finditer(pattern1, text):
    matches.append((match.start(), match.group(0)))

for match in re.finditer(pattern2, text):
    matches.append((match.start(), match.group(0)))

matches.sort(key=lambda x: x[0])

chunks = []
for i, (start, title) in enumerate(matches):
    end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
    content = text[start + len(title) : end].strip()

    chunks.append({"id": str(i + 1), "content": content})

with open(r"data\files\chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=4)
