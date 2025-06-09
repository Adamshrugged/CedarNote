

import yaml

 
# Checks for YAML formatting and converts to a dictionary 
def parse_frontmatter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if lines[0].strip() == "---":
        frontmatter_lines = []
        for line in lines[1:]:
            if line.strip() == "---":
                break
            frontmatter_lines.append(line)
        frontmatter_text = ''.join(frontmatter_lines)
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            frontmatter = {}
    else:
        frontmatter = {}

    return frontmatter