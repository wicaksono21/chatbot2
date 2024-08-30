import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from openai import OpenAI
from datetime import datetime
import pytz
import json

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["FIREBASE"]))
    firebase_admin.initialize_app(cred, {
        'storageBucket': st.secrets["FIREBASE"]["storage_bucket"]
    })

# Initialize Firestore DB
db = firestore.client()

# Get London timezone
london_tz = pytz.timezone("Europe/London")

# Function to add timestamp in London time
def add_timestamp(message):
    now_london = datetime.now(pytz.utc).astimezone(london_tz)
    message['timestamp'] = now_london.strftime("%Y-%m-%d %H:%M:%S")
    return message

# Function to save chat log
def save_chat_log():
    # Ensure all messages have timestamps
    st.session_state["messages"] = [add_timestamp(msg) if 'timestamp' not in msg else msg for msg in st.session_state["messages"]]
    
    # Save to Firestore
    db.collection('chat_logs').document(st.session_state['user'].uid).set({"messages": st.session_state["messages"]}, merge=True)
    
    # Save to Firebase Storage
    user_email = st.session_state['user'].email.replace('@', '_').replace('.', '_')
    filename = f"{user_email}_{datetime.now(london_tz).strftime('%H%M')}_chat_log.txt"
    
    # Convert chat to string and save as file
    chat_content = "\n".join([f"[{msg['timestamp']}] {msg['role']}: {msg['content']}" for msg in st.session_state["messages"] if msg['role'] != 'system'])
    with open(filename, 'w') as file:
        file.write(chat_content)
    
    # Upload file
    bucket = storage.bucket(st.secrets["FIREBASE"]["storage_bucket"])
    blob = bucket.blob(f"chat_logs/{st.session_state['user'].uid}_{filename}")
    blob.upload_from_filename(filename)
    blob.make_public()
    st.success(f"Chat log saved. Access it [here]({blob.public_url}).")

# Function to handle chat
def handle_chat(prompt):
    st.session_state["messages"].append(add_timestamp({"role": "user", "content": prompt}))
    st.chat_message("user").write(prompt)
    
    # Simulate AI response
    response = OpenAI(api_key=st.secrets["default"]["OPENAI_API_KEY"]).chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state["messages"],
        temperature=1,
        max_tokens=150
    )
    st.session_state["messages"].append(add_timestamp({"role": "assistant", "content": response.choices[0].message.content}))
    st.chat_message("assistant").write(response.choices[0].message.content)
    
    save_chat_log()

# Login/Register logic
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None

if not st.session_state['logged_in']:
    st.title("Login / Register")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        user = auth.create_user(email=email, password=password)
        st.session_state['logged_in'] = True
        st.session_state['user'] = user
    elif st.button("Login"):
        user = auth.get_user_by_email(email)
        st.session_state['logged_in'] = True
        st.session_state['user'] = user
    st.stop()

# Chat UI
st.title("💬 Essay Writing Assistant")
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        add_timestamp({"role": "system", "content": """
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
        """}),
        add_timestamp({"role": "assistant", "content": "Hi there! Ready to start your essay? I'm here to guide and help you improve your essay writing skills through a series of activities, starting with topic selection and continuing through outlining, drafting, reviewing, and proofreading. What topic are you interested in writing about? If you’d like suggestions, just let me know!"})
    ]
    save_chat_log()

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(f"[{msg['timestamp']}] {msg['content']}")

if prompt := st.chat_input():
    handle_chat(prompt)
