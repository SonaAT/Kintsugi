import json

input_file = "output.txt"
output_file = "processed_dataset.json"

formatted_data = []

with open(input_file, "r", encoding="utf-8") as file:
    raw_text = file.read().strip()

conversations = raw_text.split("<s>")[1:]

for conv in conversations:
    conv = conv.strip().replace("</s>", "").strip()
    if "[INST]" in conv and "[/INST]" in conv:
        formatted_data.append({"text": f"<s>{conv.strip()}</s>"})

with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(formatted_data, json_file, indent=4, ensure_ascii=False)

print(f"Processed dataset saved to {output_file}")
