import re


def top_words(text, k):
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("k must be a non-negative integer")
    if k < 0:
        raise ValueError("k must be a non-negative integer")
    if k == 0:
        return []
    counts = {}
    for word in re.findall(r"[A-Za-z]+", text or ""):
        word = word.lower()
        counts[word] = counts.get(word, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ordered[:k]
