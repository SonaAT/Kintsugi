from datasets import load_dataset
import json

def reformat_dialog_to_llama2(ds, output_file):
    """
    Extracts the dialog between "usr" and "sys" from the Hugging Face dataset
    and formats it according to the Llama 2 template.

    Args:
        ds (DatasetDict): Hugging Face dataset object containing the dataset.
        output_file (str): Path to save the formatted output.
    """
    # List to hold formatted conversations
    formatted_data = []

    # Process each record in the "train" split of the dataset
    for record in ds['train']:  # You can change to another split if needed
        # Get the emotion type
        emotion_type = record.get("emotion_type", "unknown")

        # Process the dialog for the current record
        dialog = record.get("dialog", [])
        for i in range(len(dialog) - 1):
            user_turn = dialog[i]
            system_turn = dialog[i + 1]

            # Ensure alternating "usr" and "sys"
            if user_turn["speaker"] == "usr" and system_turn["speaker"] == "sys":
                user_text = user_turn["text"]
                system_text = system_turn["text"]

                # Apply the Llama 2 template
                formatted_entry = (
                    f"<s>[INST] <<SYS>>\n"
                    f"Emotion: {emotion_type}\n"
                    f"<<SYS>>\n\n"
                    f"{user_text} [/INST] {system_text} </s>"
                )
                formatted_data.append(formatted_entry)

    # Save the formatted data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n\n".join(formatted_data))

    print(f"Dialog reformatted and saved to {output_file}")

# Example usage
# Load the dataset from Hugging Face
ds = load_dataset("thu-coai/esconv")

# Call the function to reformat and save the dialog
reformat_dialog_to_llama2(ds, 'output.txt')
