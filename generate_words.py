import json
import os
import sys
import time
from typing import List
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class VocabularyItem(BaseModel):
  word: str
  meaning: str = Field(description="Telugu translation and definition")
  example: str = Field(description="Natural English example sentence")
  telugu_example: str = Field(
      description="Telugu translation of the English example sentence"
  )


class VocabularyBatch(BaseModel):
  items: List[VocabularyItem]


# Initialize Gemini client
client = genai.Client()


def load_english_words(file_path="english_words.txt") -> List[str]:
  if not os.path.exists(file_path):
    print(f"Error: '{file_path}' not found!")
    return []
  with open(file_path, "r", encoding="utf-8") as f:
    return [line.strip() for line in f if line.strip()]


def process_batch(word_batch: List[str]) -> List[dict]:
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
  result = VocabularyBatch.model_validate_json(response.text)
  return [item.model_dump() for item in result.items]


def main():
  input_file = "english_words.txt"
  output_file = "words.json"
  batch_size = 100  # 100 words per API call
  delay_between_calls = 0.5  # 0.5s pause optimized for pay-as-you-go billing

  # 1. Initialize output file immediately so Git always finds words.json
  if not os.path.exists(output_file):
    with open(output_file, "w", encoding="utf-8") as f:
      json.dump([], f)

  words = load_english_words(input_file)
  if not words:
    print("No words found in input file.")
    return

  existing_data = []
  processed_words = set()

  # 2. Load progress from previous runs
  if os.path.exists(output_file):
    try:
      with open(output_file, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
        processed_words = {item["word"].lower() for item in existing_data}
    except json.JSONDecodeError:
      pass

  remaining_words = [w for w in words if w.lower() not in processed_words]
  total_remaining = len(remaining_words)
  print(f"Total words remaining: {total_remaining}")

  if total_remaining == 0:
    print("All words have already been generated!")
    return

  # 3. Process remaining batches
  for i in range(0, total_remaining, batch_size):
    batch = remaining_words[i : i + batch_size]
    current_batch_num = (i // batch_size) + 1
    total_batches = (total_remaining + batch_size - 1) // batch_size

    print(
        f"\n[Batch {current_batch_num}/{total_batches}] Processing"
        f" {len(batch)} words..."
    )

    try:
      batch_results = process_batch(batch)
      existing_data.extend(batch_results)

      # Save progress incrementally after every batch
      with open(output_file, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

      print(f"Saved {len(existing_data)} total entries to {output_file}.")
      time.sleep(delay_between_calls)

    except Exception as e:
      err_msg = str(e)
      print(f"Error encountered: {err_msg}")

      if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
        print(
            "\nQuota reached! Saving progress and exiting cleanly for GitHub"
            " Actions."
        )
        sys.exit(0)
      else:
        print("Retrying next attempt in 5 seconds...")
        time.sleep(5)


if __name__ == "__main__":
  main()
