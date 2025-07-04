import streamlit as st
import requests
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

def send_trigger_to_django(trigger):
    try:
        response = requests.post("http://127.0.0.1:8000/api/save_trigger/", data={"trigger": trigger})
        if response.status_code == 201:
            print("Trigger saved successfully!")
        else:
            print("Failed to save trigger:", response.text)
    except Exception as e:
        print("Error sending trigger to Django:", e)

@st.cache_resource
def load_hf_model():
    tokenizer = AutoTokenizer.from_pretrained("Sonaat/llama-2-7b-panic-attack-chatbot")
    model = AutoModelForCausalLM.from_pretrained("Sonaat/llama-2-7b-panic-attack-chatbot")
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
    return pipe

pipe = load_hf_model()

def generate_llama2_response(prompt_input):
    if st.session_state.waiting_for_trigger and prompt_input:
        st.session_state.trigger = prompt_input
        st.session_state.waiting_for_trigger = False
        send_trigger_to_django(prompt_input)
        return f"Thank you for sharing that, {st.session_state.username}. I've noted it down. How can I assist you further?"

    if prompt_input and "i'm better" in prompt_input.lower():
        st.session_state.waiting_for_trigger = True
        return f"I'm glad to hear that, {st.session_state.username}. What do you think triggered this panic attack?"


    prompt = "You are a calm assistant helping someone through a panic attack using sensory grounding.\n"
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        prompt += f"{role.capitalize()}: {content}\n"
    prompt += f"User: {prompt_input}\nAssistant:"

    response = pipe(prompt, max_new_tokens=200, temperature=0.7, top_p=0.9)[0]["generated_text"]


    if "Assistant:" in response:
        return response.split("Assistant:")[-1].strip()
    return response.strip()

st.set_page_config(page_title="Panic Attack Assistant", page_icon="💬")
st.title("🧘‍♀️ Panic Attack Support Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "waiting_for_trigger" not in st.session_state:
    st.session_state.waiting_for_trigger = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "trigger" not in st.session_state:
    st.session_state.trigger = ""


if not st.session_state.username:
    st.session_state.username = st.text_input("Enter your name to start chatting:", key="username_input")
    st.stop()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input(f"How can I help you, {st.session_state.username}?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = generate_llama2_response(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
