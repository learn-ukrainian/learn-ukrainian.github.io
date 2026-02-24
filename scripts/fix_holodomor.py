import re

with open('curriculum/l2-uk-en/b2-hist/holodomor-pamiat.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove inline English. Looks like: (English text)
# We only want to remove it if it's english text.
# The inline translations are mostly like: `**Some Ukrainian** (english text)`
text = re.sub(r' \([a-zA-Z\s-]+\)', '', text)

# Also fix the repetition.
# "не просто ..., а" -> "не лише ..., але й" or rephrase
text = text.replace('не просто приховувала факти, вона активно', 'намагалася не лише приховати факти, але й активно')
text = text.replace('не просто вбивством голодом, а спробою', 'не типовим вбивством голодом, а цілеспрямованою спробою')
text = text.replace('не просто ритуал скорботи — це акт', 'значно більше, ніж ритуал скорботи — це справжній акт')
text = text.replace('не просто голод, а сплановане вбивство', 'штучний голод, який став спланованим убивством')
text = text.replace('не просто як економічна категорія, а як носій', 'не в ролі економічної категорії, а як головний носій')
text = text.replace('не лише функцію збереження артефактів, але й є важливим', 'головну функцію збереження артефактів, водночас будучи важливим')

# Some others that might exist:
# "не лише ..., а й ..."
text = text.replace('не лише акт справедливості щодо жертв, але й механізм', 'акт справедливості щодо жертв, а також надійний механізм')

with open('curriculum/l2-uk-en/b2-hist/holodomor-pamiat.md', 'w', encoding='utf-8') as f:
    f.write(text)

print("Done.")
