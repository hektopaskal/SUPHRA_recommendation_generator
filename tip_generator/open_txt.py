from pathlib import Path
'''
# otherwise generated txt files are one-liners
def line_breaker(text):
    words = text.split()
    lines = []
    for i in range(0, len(words), 20):
        lines.append(" ".join(words[i:i+20]))
    return "\n".join(lines)
'''
