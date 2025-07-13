import yaml


def file_parse_frontmatter(content: str) -> dict:
    if not content:
        return {}

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            _, meta_block, _ = parts
            try:
                return yaml.safe_load(meta_block) or {}
            except yaml.YAMLError as e:
                print("YAML error:", e)
    return {}


 
# Checks for YAML formatting and converts to a dictionary 
def parse_frontmatter(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Add some sanity to ignore empty files
    if not lines:
        return {}
    
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