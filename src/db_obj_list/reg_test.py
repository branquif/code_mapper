import re

# Sample string
s = 'abs = sxt.app("select * from tb_forn a, tb_cli b where a.cod = b.cod") // tb_abacaxi'

# Set of words to search for
search_words = {'tb_forn', 'tb_abacaxi'}

# Regex pattern to match words only within double quotes

# Updated regex pattern to extract only the specific words within the double quotes
pattern = r'(?<=")[^"]*\b(?:' + '|'.join(re.escape(word) for word in search_words) + r')\b[^"]*(?=")'
print(pattern)

# Find all matches
matches = re.findall(pattern, s)

# Extracting the specific words from the matched strings
matched_words = set()
for match in matches:
    for word in search_words:
        if word in match:
            matched_words.add(word)

print(matched_words)
