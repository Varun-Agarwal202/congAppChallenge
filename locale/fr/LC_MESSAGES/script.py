from deep_translator import GoogleTranslator
import re

# === CONFIG ===
input_file = "django.po"       # your original .po file
output_file = "django_fr.po"   # translated French output
src_lang = "en"
dest_lang = "fr"

translator = GoogleTranslator(source=src_lang, target=dest_lang)

# === READ FILE ===
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# === FIND ALL ENTRIES ===
pattern = re.compile(r'(msgid\s+"(?:[^"]|\\")*"\s*(?:\n".*")*)\s*msgstr\s*""', re.MULTILINE)
entries = pattern.findall(content)

# === TRANSLATE EACH ENTRY ===
translated_content = content
for entry in entries:
    msgid_texts = re.findall(r'msgid\s+"((?:[^"]|\\")*)"', entry)
    msgid_text = "".join(msgid_texts).strip()

    if msgid_text:
        try:
            translated = translator.translate(msgid_text)
            translated = translated.replace('"', '\\"')  # escape quotes
            translated_content = translated_content.replace(
                f'{entry}\nmsgstr ""',
                f'{entry}\nmsgstr "{translated}"',
                1
            )
        except Exception as e:
            print(f"❌ Failed to translate: {msgid_text} ({e})")

# === WRITE OUTPUT ===
with open(output_file, "w", encoding="utf-8") as f:
    f.write(translated_content)

print(f"\n🎉 Translation complete! Saved to {output_file}")
