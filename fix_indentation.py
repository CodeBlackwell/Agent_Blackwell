#!/usr/bin/env python3
"""
Fix indentation in tdd_feature_implementer.py
"""

# Read the file
with open('workflows/mvp_incremental/tdd_feature_implementer.py', 'r') as f:
    lines = f.readlines()

# Find the while loop line
while_line_num = None
for i, line in enumerate(lines):
    if 'while not implementation_successful and retry_count <=' in line:
        while_line_num = i
        break

if while_line_num is None:
    print("Could not find while loop")
    exit(1)

print(f"Found while loop at line {while_line_num + 1}")

# The while loop is at 12 spaces indentation
# Everything inside should be at 16 spaces

# Find where the while loop content starts (next non-empty line)
content_start = while_line_num + 1
while content_start < len(lines) and lines[content_start].strip() == '':
    content_start += 1

# Find where the while loop ends (look for the break statement around line 356)
# The break should be the last statement in the while loop
break_line_num = None
for i in range(content_start, min(content_start + 200, len(lines))):
    if 'break' in lines[i] and lines[i].strip() == 'break':
        break_line_num = i
        break

if break_line_num is None:
    print("Could not find break statement")
    exit(1)

print(f"Found break at line {break_line_num + 1}")

# Now we need to indent everything from content_start to break_line_num by 4 more spaces
for i in range(content_start, break_line_num + 1):
    if lines[i].strip():  # Don't indent empty lines
        lines[i] = '    ' + lines[i]

# Write the fixed file
with open('workflows/mvp_incremental/tdd_feature_implementer.py', 'w') as f:
    f.writelines(lines)

print(f"Fixed indentation for lines {content_start + 1} to {break_line_num + 1}")