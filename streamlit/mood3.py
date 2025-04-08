import streamlit as st
import replicate
import os
import requests

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

# Replicate Credentials
with st.sidebar:
    st.title('🤙💬 Llama 2 Chatbot')
    st.write('This chatbot is created using the open-source Llama 2 LLM model from Meta.')
    if 'REPLICATE_API_TOKEN' in st.secrets:
        st.success('API key already provided!', icon='✅')
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👇')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

    st.subheader('Models and parameters')
    selected_model = st.sidebar.selectbox('Choose a Llama2 model', ['Llama2-7B', 'Llama2-13B'], key='selected_model')
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=1.0, value=0.1, step=0.01)
    top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
    max_length = st.sidebar.slider('max_length', min_value=20, max_value=80, value=50, step=5)

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi, it's me Iris, your personal healing partner. How was your day?"}
    ]
if "mood" not in st.session_state:
    st.session_state.mood = None
if "response_emotion" not in st.session_state:
    st.session_state.response_emotion = []

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": f"Hi, it's me Iris, your personal healing partner. How was your day?"}
    ]
    st.session_state.mood = None
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

def generate_llama2_response(prompt_input):
    string_dialogue = ("You are a helpful medical assistant. If the User is anxious, "
                       "ask them to name the feeling and rate it out of 100. Guide them step by step.")
    
    for dict_message in st.session_state.messages:
        string_dialogue += f"{dict_message['role'].capitalize()}: {dict_message['content']}\n\n"
    
    output = replicate.run(
        llm,
        input={
            "prompt": f"{string_dialogue} Assistant: ",
            "temperature": temperature,
            "top_p": top_p,
            "max_length": max_length,
            "repetition_penalty": 0.1,
        },
    )
    return output

if user_input := st.chat_input(placeholder="Type your response here..."):
    if user_input.lower() != "i'm better now":
        st.session_state.response_emotion.append(user_input)
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(user_input)
            placeholder = st.empty()
            full_response = ''.join(response)
            placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    if user_input.lower() == "i'm better now":
        # Ensure response_emotion is a list and properly formatted
        if not isinstance(st.session_state.response_emotion, list):
            st.session_state.response_emotion = []

        # Construct the prompt properly
        emotion_prompt = st.session_state.response_emotion + [
            'Extract the most prevalent emotion from the user\'s response in one word. '
            'Return only the word and nothing else, enclosed in double quotes.'
        ]
        output = replicate.run(
            llm,
            input={
                "prompt": f"{' '.join(emotion_prompt)} Assistant: ",
                "temperature": temperature,
                "top_p": top_p,
                "max_length": max_length,
                "repetition_penalty": 0.1,
            },
        )
        st.session_state.mood = ''.join(output).strip()
        send_mood_to_django(st.session_state.mood)

if st.session_state.mood:
    with st.sidebar:
        st.write(f"Stored Mood: {st.session_state.mood}")
