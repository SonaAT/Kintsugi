import streamlit as st
import os
import requests
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

st.set_page_config(page_title="Iris")

DJANGO_USER_API = "http://127.0.0.1:8000/iris/api/get_user/"
DJANGO_MOOD_API = "http://127.0.0.1:8000/iris/api/save_mood/"

@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained("Sonaat/llama-2-7b-panic-attack-chatbot")
    model = AutoModelForCausalLM.from_pretrained("Sonaat/llama-2-7b-panic-attack-chatbot")
    return tokenizer, model

tokenizer, model = load_model()

def get_logged_in_user():
    try:
        session_cookies = {"sessionid": st.query_params.get("sessionid", "")}
        response = requests.get(DJANGO_USER_API, cookies=session_cookies)
        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get("username", "Guest")
            st.session_state.username = username
            return username
        else:
            return "Guest"
    except Exception:
        return "Guest"

st.session_state.username = get_logged_in_user()
st.sidebar.write(f"Logged in as: {st.session_state.username}")

with st.sidebar:
    st.title('IRIS Conversational Journaling')
    st.write('This chatbot is powered by your custom Llama 2 model.')

    st.subheader('Model Parameters')
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=1.0, value=0.7, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=20, max_value=500, value=250, step=10)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi {st.session_state.username}, It's me Iris your personal healing partner. How was your day"}
    ]
if "mood" not in st.session_state:
    st.session_state.mood = None
if "waiting_for_mood" not in st.session_state:
    st.session_state.waiting_for_mood = False
if "response_emotion" not in st.session_state:
    st.session_state.response_emotion = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi {st.session_state.username}, It's me Iris your personal healing partner. How was your day"}
    ]
    st.session_state.mood = None
    st.session_state.waiting_for_mood = False
    st.session_state.response_emotion = []

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

def send_mood_to_django(mood):
    username = st.session_state.get("username", "Guest")
    data = {"username": username, "mood": mood}
    try:
        response = requests.post(DJANGO_MOOD_API, json=data)
        if response.status_code == 201:
            st.sidebar.success("Mood saved to database!")
        else:
            st.sidebar.error(f"Failed to save mood: {response.text}")
    except Exception as e:
        st.sidebar.error(f"Error connecting to Django API: {str(e)}")

if "flag" not in st.session_state:
    st.session_state.flag = True

def generate_response(prompt_input):
    dialogue_context = (
        "Consider yourself as a helpful medical assistant. "
        "If you sense anxiety in my response, ask me to name the feeling and rate it out of 100. "
        "Ask me to explain what makes me anxious and help me find positive alternatives of the negative thoughts. "
        "Do it step by step, not all together, wait for each of my responses. "
        "Do not assume that I have anxiety unless I mention it. "
    ) if st.session_state.flag else (
        "You are a helpful medical assistant. Only respond as 'Assistant'. "
        "If the User is anxious, help them reframe their thoughts positively. "
    )

    st.session_state.flag = False

    full_prompt = dialogue_context + "\n"
    for m in st.session_state.messages:
        role = "User" if m["role"] == "user" else "Assistant"
        full_prompt += f"{role}: {m['content']}\n"

    full_prompt += f"User: {prompt_input}\nAssistant:"

    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    output = model.generate(
        **inputs,
        do_sample=True,
        temperature=temperature,
        max_length=inputs["input_ids"].shape[1] + max_length,
        pad_token_id=tokenizer.eos_token_id,
    )
    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
    assistant_reply = decoded_output.split("Assistant:")[-1].strip()
    return assistant_reply

if user_input := st.chat_input(placeholder="Type your response here..."):
    if user_input.lower() != "im better now":
        st.session_state.response_emotion.append(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(user_input)
            st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

    if user_input.lower() == "i'm better now":
        st.session_state.waiting_for_mood = True
        emotion_prompt = " ".join(
            st.session_state.response_emotion +
            ["Extract the most prevalent emotion from the user's response. Your response should be one word only."]
        )

        with st.chat_message("assistant"):
            with st.spinner("Extracting mood..."):
                inputs = tokenizer(emotion_prompt, return_tensors="pt").to(model.device)
                output = model.generate(**inputs, max_length=50, pad_token_id=tokenizer.eos_token_id)
                mood = tokenizer.decode(output[0], skip_special_tokens=True).strip().split()[-1]
                st.session_state.mood = mood
                st.write(f"Detected mood: **{mood}**")
                send_mood_to_django(mood)

if st.session_state.mood:
    with st.sidebar:
        st.write(f"Stored Mood: **{st.session_state.mood}**")
