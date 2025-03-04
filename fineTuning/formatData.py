# code used to format output.txt to processed_dataset.json

import json

# Input and output file paths
input_file = "output.txt"  # Your raw text dataset
output_file = "processed_dataset.json"  # Processed JSON dataset

# List to store structured conversations
formatted_data = []

# Read the text file
with open(input_file, "r", encoding="utf-8") as file:
    raw_text = file.read().strip()

# Split conversations by `<s>` and `</s>` (ensuring proper format)
conversations = raw_text.split("<s>")[1:]  # Ignore anything before the first `<s>`

for conv in conversations:
    conv = conv.strip().replace("</s>", "").strip()  # Remove closing tags
    if "[INST]" in conv and "[/INST]" in conv:
        formatted_data.append({"text": f"<s>{conv.strip()}</s>"})

# Save as JSON
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(formatted_data, json_file, indent=4, ensure_ascii=False)

print(f"Processed dataset saved to {output_file}")
