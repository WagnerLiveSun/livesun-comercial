import re

with open("src/templates/admin/comercial_panel.html","r",encoding="utf-8") as f:
    content = f.read()

# Remove all h6 + list-group-flush blocks
# Pattern matches: <h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">...</h6>\s*<div class="list-group list-group-flush mb-3">...</div>
# We need to remove each category block

# Find and remove all occurrences of the pattern
pattern = r'<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">[^<]*</h6>\\s*<div class="list-group list-group-flush mb-3">[^<]*</div>'

# Actually, let's do it line by line to be safe
lines = content.split('\n')
new_lines = []
skip = False
skip_count = 0
h6_pattern = re.compile(r'^<h6 class="small text-uppercase text-muted mb-2 mt-3 border-bottom pb-1">')

for i, line in enumerate(lines):
    if h6_pattern.match(line.strip()):
        # Found h6, now we need to skip until we find the closing </div> of list-group-flush
        skip = True
        # Don't add the h6 line
        continue
    if skip:
        if '</div>' in line and 'list-group-flush' in line:
            # Check if this is the closing div for list-group-flush
            # Look back to see if we started with h6
            skip = False
            # Also need to skip any lines between h6 and closing div
            continue
        else:
            # Skip this line (it's part of the list-group)
            continue
    new_lines.append(line)

new_content = '\n'.join(new_lines)

with open("src/templates/admin/comercial_panel.html","w",encoding="utf-8") as f:
    f.write(new_content)

print("Removed h6 + list-group-flush blocks")
print(f"Original lines: {len(content.split(chr(10)))}")
print(f"New lines: {len(new_lines)}")