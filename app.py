import openai
import streamlit as st

st.title("Essay Writing Assistant")

# Initialize the OpenAI client with the API key from Streamlit's secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("API key not found. Please set up your 'OPENAI_API_KEY' in secrets.")
else:
    # API initialization with the new library
    openai.api_key = st.secrets["OPENAI_API_KEY"]

# Set the default model if not in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"  # Adjust the model identifier as necessary

# Initialize messages in session state if not already there
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display past messages using Streamlit's chat_message component
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input field
prompt = st.chat_input("Type your message here:")

# Handle chat input and generate responses
if prompt:
    # Append user message to the conversation
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    # Construct messages for API call
    messages = [
        {
            "role": "system",
            "content": "Your system instructions here"
        }
    ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]
    
    # Generate a response using the new Chat API
    response = openai.ChatCompletion.create(
        model=st.session_state["openai_model"],
        messages=messages,
        temperature=1,
        max_tokens=150
    )

    # Check for valid response and append to conversation
    if response.choices:
        response_text = response.choices[0].message['content'] if 'message' in response.choices[0] else "No response generated."
        st.session_state["messages"].append({"role": "assistant", "content": response_text})
        
        # Display the response using Streamlit's chat_message component
        with st.chat_message("assistant"):
            st.markdown(response_text)
