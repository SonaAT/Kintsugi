import streamlit as st
from openai import OpenAI
import os
import requests
import altair as alt

# App title
st.set_page_config(page_title="Iris")

# Django API URLs
DJANGO_USER_API = "http://127.0.0.1:8000/iris/api/get_user/"
DJANGO_MOOD_API = "http://127.0.0.1:8000/iris/api/save_mood/"

def get_logged_in_user():
    try:
        session_cookies = {"sessionid": st.query_params.get("sessionid", "")}  # Get session ID from URL
        response = requests.get(DJANGO_USER_API, cookies=session_cookies)

        if response.status_code == 200:
            user_data = response.json()
            username = user_data.get("username", "Guest")
            st.session_state.username = username  # Store in session state
            return username
        else:
            return "Guest"
    except Exception as e:
        return "Guest"

st.session_state.username = get_logged_in_user()
st.sidebar.write(f"Logged in as: {st.session_state.username}")

# LLaMA API Credentials
with st.sidebar:
    st.title('🤙💬 Llama 2 Chatbot')
    st.write('This chatbot is created using the open-source Llama 2 LLM model.')

    # Initialize the OpenAI client with LLaMA API
    client = OpenAI(
        api_key=os.environ['LLAMA_API_TOKEN'] ,
        base_url="https://api.llmapi.com/"  # Replace with your actual LLaMA API base URL
    )

    st.subheader('Models and parameters')
    selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['llama2-7b', 'llama2-13b'], key='selected_model')
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=20, max_value=100, value=50, step=5)
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi {st.session_state.username}, It's me Iris your personal healing partner. How was your day"}
    ]
if "mood" not in st.session_state:
    st.session_state.mood = None
if "waiting_for_mood" not in st.session_state:
    st.session_state.waiting_for_mood = False
if "response_emotion" not in st.session_state:
    st.session_state.response_emotion = []  # Persist response_emotion in session state

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi {st.session_state.username}, It's me Iris your personal healing partner. How was your day"}
    ]
    st.session_state.mood = None
    st.session_state.waiting_for_mood = False
    st.session_state.response_emotion = []  # Reset response_emotion on clear

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

# Function for generating LLaMA2 response using OpenAI client
def generate_llama2_response(prompt_input):
    if st.session_state.flag:
        string_dialogue = (
            "You are a helpful medical assistant. You do not respond as 'User' or pretend to be 'User'. "
            "If you sense anxiety in the user's response ask the user to name the feeling and rate it out of 100. "
            "Ask the user to explain what makes them anxious and help them find positive alternatives of the negative thoughts. "
            "Do it step by step not all together wait for each user response. "
            "Do not assume that the user has anxiety only ask the user to rate the feelings if the user is in distress. "
            "You don't respond as User or pretend to be the User "
        ) + prompt_input
        st.session_state.flag = False
    else:
        string_dialogue = (
            "You are a helpful medical assistant. You do not respond as 'User' or pretend to be 'User'. "
            "You only respond as 'Assistant'. If the User is sharing about a problem in their life and is anxious, "
            "help them find positive alternative to their negative thoughts and give them a different perspective where things will go right "
        ) + prompt_input

    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

    # Use OpenAI client to call LLaMA API
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": string_dialogue},
            {"role": "user", "content": prompt_input or "Please respond"}
        ],
        model="llama3-8b",  # Use the selected model (llama2-7b or llama2-13b)
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_length,
        stream=False
    )
    return chat_completion.choices[0].message.content

# User input for prompts
if user_input := st.chat_input(placeholder="Type your response here..."):
    if user_input.lower() != "im better now":
        st.session_state.response_emotion.append(user_input)  # Append to session state list

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate response to user input
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(user_input)
            placeholder = st.empty()
            full_response = response  # No streaming, direct response
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    
    # Handle mood extraction when user says "Im better now"
    if user_input.lower() == "i'm better now":
        print(st.session_state.response_emotion)  # Debug: should now show accumulated responses
        st.session_state.waiting_for_mood = True
        # Prepare prompt for emotion extraction
        emotion_prompt = " ".join(st.session_state.response_emotion + 
                                ["Extract the most prevalent emotion from the user's response. Your response should be one word, just the extracted emotion. Return only the word and nothing else."])
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": emotion_prompt},
                {"role": "user", "content": "Please extract the emotion"}
            ],
            model="llama3-8b",  # keep this
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_length,
            stream=False
        )
        full_output = chat_completion.choices[0].message.content
        st.session_state.mood = full_output  # Store the extracted mood
        send_mood_to_django(st.session_state.mood)  # Send to Django API

# Display stored mood in sidebar
if st.session_state.mood:
    with st.sidebar:
        st.write(f"Stored Mood: {st.session_state.mood}")