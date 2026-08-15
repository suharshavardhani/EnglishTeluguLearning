import urllib.request
import re

print("Downloading English word dataset...")
url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa-no-swears.txt"

# Download raw word list
urllib.request.urlretrieve(url, "raw_10k.txt")

with open("raw_10k.txt", "r", encoding="utf-8") as f:
    all_words = [line.strip() for line in f if line.strip()]

# Filter out basic/short words to isolate intermediate and advanced vocabulary
# Keeps words 5+ characters long containing only standard letters
advanced_words = []
for word in all_words:
    if len(word) >= 5 and re.match("^[a-zA-Z]+$", word):
        advanced_words.append(word.capitalize())

# Write to english_words.txt
with open("english_words.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(advanced_words))

print(f"Success! Generated 'english_words.txt' with {len(advanced_words)} advanced words.")
