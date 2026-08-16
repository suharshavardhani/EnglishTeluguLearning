import json
import os
import time
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Define the Structured Output Schema
class VocabularyItem(BaseModel):
    word: str
    meaning: str = Field(description="Telugu translation and definition")
    example: str = Field(description="Natural English example sentence")
    telugu_example: str = Field(description="Telugu translation of the English example sentence")

class VocabularyBatch(BaseModel):
    items: List[VocabularyItem]

# Initialize the Gemini client (automatically reads GEMINI_API_KEY from environment)
client = genai.Client()

def load_english_words(file_path="english_words.txt") -> List[str]:
    """Reads input words from english_words.txt (one word per line)."""
    if not os.path.exists(file_path):
        print(f"Error: '{file_path}' not found! Please create it with your target words.")
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def process_batch(word_batch: List[str]) -> List[dict]:
    """Sends a batch of words to Gemini and enforces JSON output matching the schema."""
    prompt = f"""
Provide Telugu meanings and example sentences for the following English vocabulary words:
{', '.join(word_batch)}

Rules:
- 'meaning': Clear Telugu definition/translation.
- 'example': Advanced, natural English sentence showing proper context.
- 'telugu_example': Accurate Telugu translation of the English example sentence.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VocabularyBatch,
            temperature=0.2,
        ),
    )

    # Validate and return data as Python dicts
    result = VocabularyBatch.model_validate_json(response.text)
    return [item.model_dump() for item in result.items]

def main():
    input_file = "english_words.txt"
    output_file = "words.json"
    batch_size = 50  # 50 words per API call (200 total calls for 10,000 words)
    delay_between_calls = 4.5  # Keeps execution under the Free Tier rate limit (15 RPM)

    words = load_english_words(input_file)
    if not words:
        return

    existing_data = []
    processed_words = set()

    # Load existing progress if script was previously paused or stopped
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                processed_words = {item["word"].lower() for item in existing_data}
            print(f"Loaded {len(existing_data)} existing entries from {output_file}.")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse existing {output_file}. Starting fresh.")

    remaining_words = [w for w in words if w.lower() not in processed_words]
    total_remaining = len(remaining_words)
    print(f"Total words left to process: {total_remaining}")

    for i in range(0, total_remaining, batch_size):
        batch = remaining_words[i:i + batch_size]
        current_batch_num = (i // batch_size) + 1
        total_batches = (total_remaining + batch_size - 1) // batch_size

        print(f"\n[Batch {current_batch_num}/{total_batches}] Processing {len(batch)} words...")

        try:
            batch_results = process_batch(batch)
            existing_data.extend(batch_results)

            # Real-time incremental save
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            print(f"Success! Saved {len(existing_data)} total entries to {output_file}.")

        except Exception as e:
            print(f"Error on batch starting with '{batch[0]}': {e}")
            print("Retrying after 10 seconds...")
            time.sleep(10)
            continue

        # Respect API Rate Limits
        time.sleep(delay_between_calls)

    print("\nAll done! Your complete dataset is saved in words.json.")

if __name__ == "__main__":
    main()
