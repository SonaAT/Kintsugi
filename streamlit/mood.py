import streamlit as st
import replicate
import os
import altair as alt
import requests

# App title
st.set_page_config(page_title="Iris")

# Django API URL
DJANGO_API_URL = ""
flag=True

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
    st.markdown('📖 Learn how to build this app in this [blog](https://blog.streamlit.io/how-to-build-a-llama-2-chatbot/)!')

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi Maria, It's me Iris your personal healing partner. How was your day"}
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
        {"role": "assistant", "content": "Hi Maria, It's me Iris your personal healing partner. How was your day"}
    ]
    st.session_state.mood = None
    st.session_state.waiting_for_mood = False
    st.session_state.response_emotion = []  # Reset response_emotion on clear

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

def send_mood_to_django(mood):
    data = {"user_name": "Maria", "mood": mood}
    try:
        response = requests.post(DJANGO_API_URL, json=data)
        if response.status_code == 201:
            st.sidebar.success("Mood saved to database!")
        else:
            st.sidebar.error(f"Failed to save mood: {response.text}")
    except Exception as e:
        st.sidebar.error(f"Error connecting to Django API: {str(e)}")

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    global flag
    if flag:
        string_dialogue = "You are a helpful medical assistant. You do not respond as 'User' or pretend to be 'User'.If You sense anxiety in the user's response ask the user to name the feeling and rate it out of 100. ask the user to Explain what makes them anxious and help them find positive alternatives of the negetive thoughts. Do it step by step not all together wait for each user response. You dont respond as User or pretend to be the User  " + prompt_input 
        flag = False
    else:
        string_dialogue = "You are a helpful medical assistant. You do not respond as 'User' or pretend to be 'User'.You only respond as 'Assistant'. If the User is sharing about a problem in their life and is anxious, help them find positive alternative to their negative thoughts and give them a different perspective where things will go right" + prompt_input 
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    
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
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    
    # Handle mood extraction when user says "Im better now"
    if user_input.lower() == "im better now":
        print(st.session_state.response_emotion)  # Debug: should now show accumulated responses
        st.session_state.waiting_for_mood = True
        # Prepare prompt for emotion extraction
        emotion_prompt = st.session_state.response_emotion + ["Extract the most prevalent emotion from the user's response. Your response should be one word, just the extracted emotion."]
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
        # Process the output and store the mood
        full_output = ''.join(output)
        st.session_state.mood = full_output.strip()  # Store the extracted mood
        send_mood_to_django(st.session_state.mood)  # Send to Django API

# Display stored mood in sidebar
if st.session_state.mood:
    with st.sidebar:
        st.write(f"Stored Mood: {st.session_state.mood}")