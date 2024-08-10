import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
from openai import OpenAI

# Check if Firebase app is already initialized
if not firebase_admin._apps:
    cred = credentials.Certificate("essay-writing-assistant-firebase-adminsdk-rtrnk-f280b8aa38.json")
    firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()

# Function to register a new user in Firebase Authentication
def register_user(email, password):
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        st.success("User registered successfully!")
        return user
    except firebase_admin.exceptions.FirebaseError as e:
        st.error(f"Error registering user: {e}")
        return None

# Function to login a user using Firebase Authentication
def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        st.session_state['user'] = user
        st.session_state['logged_in'] = True
        st.success(f"Logged in as {user.email}")
        return True
    except firebase_admin.exceptions.FirebaseError as e:
        st.error("Invalid credentials!")
        return False

# Firestore Collection Reference for Chat Logs
def get_chat_collection():
    return db.collection('chat_logs').document(st.session_state['user'].uid)

# Store Chat Log in Firestore
def store_chat_log(message, role='user'):
    doc_ref = get_chat_collection()
    doc = doc_ref.get()
    
    if doc.exists:
        chat_logs = doc.to_dict().get('messages', [])
    else:
        chat_logs = []

    chat_logs.append({"role": role, "content": message})
    doc_ref.set({"messages": chat_logs})

# Retrieve Chat Log from Firestore
def retrieve_chat_logs():
    doc_ref = get_chat_collection()
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get('messages', [])
    return []

# Check login status
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

# Login or Register Form
if not st.session_state['logged_in']:
    st.title("Login / Register")

    choice = st.radio("Login or Register", ["Login", "Register"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Register":
        if st.button("Register"):
            user = register_user(email, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user'] = user
                st.query_params = {"logged_in": "true"}  # Updated from deprecated experimental function
    else:
        if st.button("Login"):
            if login_user(email, password):
                st.query_params = {"logged_in": "true"}  # Updated from deprecated experimental function

    st.stop()
# User is logged in, continue with the chatbot
openai_api_key = st.secrets["default"]["OPENAI_API_KEY"]

st.title("💬 Essay Writing Assistant Chatbot-3")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")

# Load previous chat history
#if "messages" not in st.session_state:
#    st.session_state["messages"] = retrieve_chat_logs()

if "messages" not in st.session_state:
    # Update the system prompt with the new detailed instructions
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
    st.session_state.messages.append({"role": "assistant", "content": " Hi there! Ready to start your essay? What topic are you interested in writing about? If you’d like suggestions, just let me know!"})
    #store_chat_log(" Hi there! Ready to start your essay? What topic are you interested in writing about? If you’d like suggestions, just let me know!", role="assistant")

# Display chat messages
for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

# Input for new messages
if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    store_chat_log(prompt, role="user")

    # Simulate AI response using OpenAI
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"],
        temperature=0.7,
        max_tokens=150
    )
    
    msg = response.choices[0].message.content  # Fixed to correctly access content
    st.session_state["messages"].append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
    store_chat_log(msg, role="assistant")
