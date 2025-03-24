import streamlit as st
import replicate
import os
from gtts import gTTS
import base64

# App title
flag = 0
st.set_page_config(page_title="🤙💬 Llama 2 Chatbot")

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

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Hi Maria, It's me Kinsuki your personal healing partner. I'm sorry that you are having a panic attack, Let's guide you through this shall we?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "Hi Maria, It's me Kinsuki your personal healing partner. I'm sorry that you are having a panic attack, Let's guide you through this shall we?"}]

st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    string_dialogue = ("You are a helpful assistant. You only respond once as 'Assistant'. The user is having a panic attack, "
                       "Please guide 'User' through a step-by-step sensory grounding exercise, "
                       "and give each sensory grounding in each step and only move to the next one once 'User' replies. "
                       "Do not ask the 'User' to elaborate the feelings or their thoughts. "
                       "Strictly stick to the sensory grounding exercise. Do not use emojis. "
                       "Please respond in a calm and empathetic tone.")

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

# Function to generate audio and play it
def generate_audio(text):
    tts = gTTS(text)
    tts.save("response.mp3")
    audio_file = open("response.mp3", "rb").read()
    audio_base64 = base64.b64encode(audio_file).decode("utf-8")
    audio_html = f"<audio autoplay='true'><source src='data:audio/mp3;base64,{audio_base64}' type='audio/mp3'></audio>"
    st.markdown(audio_html, unsafe_allow_html=True)

# Panic button
if st.button("🚨 Panic Button"):
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_llama2_response(None)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
            st.write("Generating audio response...")
            generate_audio(full_response)

    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)

# User input for prompts
if user_input := st.chat_input(placeholder="Type your response here..."):
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
            st.write("Generating audio response...")
            generate_audio(full_response)

    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
