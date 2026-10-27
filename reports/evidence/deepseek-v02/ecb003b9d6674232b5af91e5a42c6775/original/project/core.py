def top_words(text, k):
    counts = {}
    for word in text.split():
        counts[word] = counts.get(word, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:k]
