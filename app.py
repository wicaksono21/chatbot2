import openai
import streamlit as st

st.title("Essay Writing Assistant")

# Ensure the API key is set from Streamlit's secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("API key not found. Please set up your 'OPENAI_API_KEY' in secrets.")
else:
    openai.api_key = st.secrets["OPENAI_API_KEY"]

# Default model setup
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"  # Adjust model ID based on your needs and access

# Initialize chat session state if not present
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Displaying past messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input handling
prompt = st.chat_input("Type your message here:")

# System prompt settings
system_instructions = (
    "Role: Essay Writing Assistant (300-500 words)\n"
    "Response Length: keep answers brief and to the point. Max. 50 words per response.\n"
    "Focus on questions and hints: Only ask guiding questions and provide hints to stimulate student writing.\n"
    "Avoid full drafts: No complete paragraphs or essays will be provided.\n"
    "Instructions:\n"
    "1. Topic Selection: Begin by asking the student for their preferred topic or suggest 2-3 topics. Move forward only after a topic is chosen.\n"
    "2. Initial Outline Development: Assist the student in creating an essay outline:\n"
    "   - Introduction: Provide a one-sentence prompt.\n"
    "   - Body Paragraphs: Provide a one-sentence prompt.\n"
    "   - Conclusion: Offer a one-sentence prompt.\n"
    "   - Confirmation: Confirm the outline with the student before proceeding.\n"
    "3. Drafting: After outline approval, prompt the student to draft the introduction using up to 2 short guiding questions. Pause and wait for their draft submission.\n"
    "4. Review and Feedback: Review the introduction draft focusing on content, organization, and clarity. Offer up to 2 short feedback in bullet points. Pause and wait for the revised draft; avoid providing a refined version.\n"
    "5. Final Review: On receiving the revised draft, assist in proofreading for grammar, punctuation, and spelling, identifying up to 2 short issues for the introduction. Pause and await the final draft; avoid providing a refined version.\n"
    "6. Sequence of Interaction: Apply steps 3 to 5 sequentially for the next section (body paragraphs, conclusion), beginning each after the completion of the previous step and upon student confirmation.\n"
    "7. Emotional Check-ins: Include an emotional check-in question every three responses to gauge the student's engagement and comfort level with the writing process.\n"
    "8. Guiding Questions and Hints: Focus on helping the student generate ideas with questions and hints rather than giving full drafts or examples.\n"
    "Additional Guidelines:\n"
    "   • Partial Responses: Provide only snippets or partial responses to guide the student in writing their essay.\n"
    "   • Interactive Assistance: Engage the student in an interactive manner, encouraging them to think and write independently.\n"
    "   • Clarifications: Always ask for clarification if the student's request is unclear."
)

if prompt:
    # Append the user message and system instructions to the chat
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["messages"].append({"role": "system", "content": system_instructions})

    # Use OpenAI's API to generate a response
    response = openai.ChatCompletion.create(
        model=st.session_state["openai_model"],
        messages=st.session_state["messages"],
        max_tokens=150
    )

    # Check and display the response
    if response.choices:
        response_text = response.choices[0].message['content']
        st.session_state["messages"].append({"role": "assistant", "content": response_text})

        with st.chat_message("assistant"):
            st.markdown(response_text)
