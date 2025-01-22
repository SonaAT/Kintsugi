import os
import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig
from trl import SFTTrainer

# Step 1: Dataset and Model Configuration
# Dataset file path
dataset_name = "output.txt"

# Hugging Face model name and fine-tuned model output name
model_name = "NousResearch/Llama-2-7b-chat-hf"
new_model = "Llama-2-7b-chat-finetune"

# LoRA configuration
lora_r = 64
lora_alpha = 16
lora_dropout = 0.1

# BitsAndBytes configuration
use_4bit = True
bnb_4bit_compute_dtype = "float16"
bnb_4bit_quant_type = "nf4"
use_nested_quant = False

# TrainingArguments configuration
output_dir = "./results"
num_train_epochs = 1
fp16 = False
bf16 = False
per_device_train_batch_size = 4
gradient_accumulation_steps = 1
gradient_checkpointing = True
max_grad_norm = 0.3
learning_rate = 2e-4
weight_decay = 0.001
optim = "paged_adamw_32bit"
lr_scheduler_type = "cosine"
max_steps = -1
warmup_ratio = 0.03
group_by_length = True
save_steps = 0
logging_steps = 25

# Step 2: Load Dataset
with open(dataset_name, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Prepare the dataset in Hugging Face format
data = {"text": [line.strip() for line in lines if line.strip()]}
dataset = Dataset.from_dict(data)

# Step 3: Load Tokenizer and Model with QLoRA Configuration
compute_dtype = getattr(torch, bnb_4bit_compute_dtype)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=use_4bit,
    bnb_4bit_quant_type=bnb_4bit_quant_type,
    bnb_4bit_compute_dtype=compute_dtype,
    bnb_4bit_use_double_quant=use_nested_quant,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map={"": 0}
)
model.config.use_cache = False
model.config.pretraining_tp = 1

# Load tokenizer and add special tokens
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
special_tokens = ["<s>", "</s>", "[INST]", "<<SYS>>"]
tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
model.resize_token_embeddings(len(tokenizer))

# Tokenizer configuration for padding
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

# Step 4: Configure LoRA
peft_config = LoraConfig(
    lora_alpha=lora_alpha,
    lora_dropout=lora_dropout,
    r=lora_r,
    bias="none",
    task_type="CAUSAL_LM",
)

# Step 5: Set Training Parameters
training_arguments = TrainingArguments(
    output_dir=output_dir,
    num_train_epochs=num_train_epochs,
    per_device_train_batch_size=per_device_train_batch_size,
    gradient_accumulation_steps=gradient_accumulation_steps,
    optim=optim,
    save_steps=save_steps,
    logging_steps=logging_steps,
    learning_rate=learning_rate,
    weight_decay=weight_decay,
    fp16=fp16,
    bf16=bf16,
    max_grad_norm=max_grad_norm,
    max_steps=max_steps,
    warmup_ratio=warmup_ratio,
    group_by_length=group_by_length,
    lr_scheduler_type=lr_scheduler_type,
    report_to="tensorboard"
)

# Step 6: Initialize Trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    peft_config=peft_config,
    dataset_text_field="text",
    max_seq_length=None,  # Adjust as necessary for your use case
    tokenizer=tokenizer,
    args=training_arguments,
    packing=False,
)

# Step 7: Train Model
trainer.train()

# Step 8: Save Fine-Tuned Model
trainer.model.save_pretrained(new_model)
tokenizer.save_pretrained(new_model)
