text = "мій, моя, моє, твій, твоя, твоє, наш, наша, ваш, ваша, його, її"
for word in text.split(', '):
    print(f"{word}: {[hex(ord(c)) for c in word]}")
