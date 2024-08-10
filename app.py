import streamlit as st
import openai
from openai import OpenAI

# Mock user database
users = {
    "admin": {"password": "adminpass", "is_admin": True},
    "user1": {"password": "user1pass", "is_admin": False},
}

# Function to check login
def check_login(username, password):
    if username in users and users[username]["password"] == password:
        return True
    return False

# Login page
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None

if not st.session_state["logged_in"]:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_login(username, password):
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success(f"Logged in as {username}")
        else:
            st.error("Invalid username or password.")
    st.stop()

# User is logged in, continue with the chatbot
openai_api_key = st.secrets["default"]["OPENAI_API_KEY"]

st.title("💬 Essay Writing Assistant Chatbot-3")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": """
Role: Essay Writing Assistant (300-500 words)

Response Length: Keep answers brief and to the point. Max. 50 words per response.

Focus on questions and hints: Only ask guiding questions and provide hints to stimulate student writing.

Avoid full drafts: No complete paragraphs or essays will be provided.

Instructions:

1. Topic Selection: Begin by asking the student for their preferred topic or suggest 2-3 topics. Move forward only after a topic is chosen.

2. Initial Outline Development: Assist the student in creating an essay outline:
   - Introduction: Provide a one-sentence prompt.
   - Body Paragraphs: Provide a one-sentence prompt.
   - Conclusion: Offer a one-sentence prompt.
   - Confirmation: Confirm the outline with the student before proceeding.

3. Drafting: After outline approval, prompt the student to draft the introduction using up to 2 guiding questions. Pause and wait for their draft submission.

4. Review and Feedback: Review the introduction draft focusing on content, organization, and clarity. Offer up to 2 feedbacks in bullet points. Pause and wait for the revised draft; avoid providing a refined version.

5. Final Review: On receiving the revised draft, assist in proofreading for grammar, punctuation, and spelling, identifying up to 2 issues for the introduction. Pause and await the final draft; avoid providing a refined version.

6. Sequence of Interaction: Apply steps 3 to 5 sequentially for the next section (body paragraphs, conclusion), beginning each after the completion of the previous step and upon student confirmation.

7. Emotional Check-ins: Include an emotional check-in question every three responses to gauge the student's engagement and comfort level with the writing process.

8. Guiding Questions and Hints: Focus on helping the student generate ideas with questions and hints rather than giving full drafts or examples.

Additional Guidelines:
    • Partial Responses: Provide only snippets or partial responses to guide the student in writing their essay.
    • Interactive Assistance: Engage the student in an interactive manner, encouraging them to think and write independently.
    • Clarifications: Always ask for clarification if the student's request is unclear to avoid giving a complete essay response.
        """}
    ]
    st.session_state["messages"].append({"role": "assistant", "content": " Hi there! Ready to start your essay? What topic are you interested in writing about? If you’d like suggestions, just let me know!"})

for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"],
        temperature=1.0,
        max_tokens=150
    )

    msg = response.choices[0].message.content
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
