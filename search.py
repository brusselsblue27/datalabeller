import pandas as pd
import random
import csv
import os
import requests

# === SETTINGS ===
INPUT_FILE = "bigfile.csv"         # ← Replace with your filename
OUTPUT_FILE = "labeled_sample.csv"
SAMPLE_SIZE = 180
TEXT_COLUMN = "product"
ID_COLUMN = "entryid"
API_KEY = "XX"  # ← Paste your API key here

# === GLOBAL FLAG FOR TRANSLATION ===
USE_TRANSLATE = False

# === TRANSLATION ===
def translate_text(text, target="en"):
    url = f"https://translation.googleapis.com/language/translate/v2"
    params = {
        'q': text,
        'target': target,
        'format': 'text',
        'key': API_KEY
    }
    try:
        response = requests.post(url, data=params)
        response.raise_for_status()
        return response.json()['data']['translations'][0]['translatedText']
    except Exception as e:
        print(f"⚠️ Translation error: {e}")
        return "[Translation failed]"

# === LOAD RANDOM SAMPLE ===
def load_random_sample(file_path, sample_size, text_column, id_column):
    chunksize = 10000
    all_rows = []
    print("🔍 Reading file in chunks...")
    for chunk in pd.read_csv(file_path, usecols=[id_column, text_column], chunksize=chunksize):
        chunk = chunk.dropna(subset=[text_column])
        all_rows.extend(chunk.to_dict(orient='records'))
    print(f"✅ Total usable rows: {len(all_rows)}")
    random.shuffle(all_rows)
    return all_rows[:sample_size]

# === LOAD EXISTING LABELS ===
def load_existing_labels(output_file):
    if not os.path.exists(output_file):
        return {}
    df = pd.read_csv(output_file)
    return {str(row["entryid"]): row for _, row in df.iterrows()}

# === MAIN LABELING FUNCTION ===
def label_rows(sampled_rows, existing_labels, output_file):
    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["entryid", "Excerpt", "Dual-use", "Maybe", "No"])
        if f.tell() == 0:
            writer.writeheader()

        for row in sampled_rows:
            entryid = str(row[ID_COLUMN])
            text = row[TEXT_COLUMN]

            if entryid in existing_labels:
                continue

            print(f"\n📝 ID {entryid}")
            print(f"📦 Original: {text}")

            if USE_TRANSLATE:
                translated = translate_text(text)
                print(f"🌍 English:  {translated}")

            print("Type: 1 = dual-use, 0 = not dual-use, m = maybe, q = quit")

            while True:
                label = input("Your choice: ").strip().lower()
                if label in ['1', '0', 'm', 'q']:
                    break
                print("❌ Invalid input. Please type 1, 0, m, or q.")

            if label == 'q':
                print("👋 Exiting — progress saved.")
                return

            record = {
                "entryid": entryid,
                "Excerpt": text,
                "Dual-use": 1 if label == "1" else 0,
                "Maybe": 1 if label == "m" else 0,
                "No": 1 if label == "0" else 0
            }
            writer.writerow(record)
            f.flush()

# === MAIN LOGIC ===
def main():
    global USE_TRANSLATE

    print("🔠 Do you want to enable live English translation using Google Translate?")
    use_translate_input = input("Type 'y' for yes or 'n' for no: ").strip().lower()
    USE_TRANSLATE = use_translate_input == 'y'

    print("\n📦 Launching labeling tool...")
    sampled = load_random_sample(INPUT_FILE, SAMPLE_SIZE, TEXT_COLUMN, ID_COLUMN)
    existing = load_existing_labels(OUTPUT_FILE)
    label_rows(sampled, existing, OUTPUT_FILE)
    print(f"\n✅ Done! Labeled entries saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
