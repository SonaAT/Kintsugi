from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login


login("TOKEN")


model_name = "Sonaat/llama-2-7b-panic-attack-chatbot"
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=True)


input_text = "Hello, how are you?"
inputs = tokenizer(input_text, return_tensors="pt")
output = model.generate(**inputs)
response = tokenizer.decode(output[0], skip_special_tokens=True)

print(response)
