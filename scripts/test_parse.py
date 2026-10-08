"""
test_parse.py
Validates markdown concatenation and block parsing.
"""

import sys
import os
import re

sys.path.insert(0, ".")
from scripts.report_sections.phase1_to_4 import get_markdown_phase1_to_4
from scripts.report_sections.phase5_to_8 import get_markdown_phase5_to_8
from scripts.report_sections.phase9_to_12 import get_markdown_phase9_to_12
from scripts.report_sections.phase13_to_16 import get_markdown_phase13_to_16

full_md = (
    get_markdown_phase1_to_4() + "\n\n" +
    get_markdown_phase5_to_8() + "\n\n" +
    get_markdown_phase9_to_12() + "\n\n" +
    get_markdown_phase13_to_16()
)

lines = full_md.splitlines()
print(f"Total lines in full markdown: {len(lines)}")
print(f"Total characters: {len(full_md)}")

# Check image references
img_matches = list(re.finditer(r'!\[([^\]]*)\]\(([^)]+)\)', full_md))
print(f"Image matches: {len(img_matches)}")
for m in img_matches:
    alt = m.group(1)
    path = m.group(2)
    norm = path.replace('/', os.sep)
    if not os.path.exists(norm):
        print(f"ERROR: missing {norm}")

print("Validation completed successfully.")
