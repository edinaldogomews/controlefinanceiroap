import os

def is_likely_emoji(char):
    code = ord(char)
    # Range checks for common emojis and symbols
    return (
        (0x1F300 <= code <= 0x1F9FF) or  # Misc Symbols, Emoticons, Transport, Supplemental
        (0x2600 <= code <= 0x26FF) or    # Misc Symbols
        (0x2700 <= code <= 0x27BF) or    # Dingbats
        (0xFE00 <= code <= 0xFE0F) or    # Variation Selectors
        (0x1F600 <= code <= 0x1F64F) or  # Emoticons
        (0x1F680 <= code <= 0x1F6FF) or  # Transport
        (0x1FA70 <= code <= 0x1FAFF)     # Symbols and Pictographs Extended-A
    )

root_dir = r"c:\Temp\controlefinanceiroap\controlefinanceiroap"
found_emojis = {}

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith(".py") and file != "find_emojis.py":
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, root_dir)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    line_content = line.strip()
                    # Skip comments if possible? No, user might want to know about them too.
                    # But usually code.
                    
                    chars_in_line = [c for c in line if is_likely_emoji(c)]
                    if chars_in_line:
                        if rel_path not in found_emojis:
                            found_emojis[rel_path] = []
                        found_emojis[rel_path].append(f"Line {i+1}: {line_content}")
            except Exception:
                pass

for file, lines in found_emojis.items():
    print(f"\n=== {file} ===")
    for line in lines:
        print(line)
