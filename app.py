import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from openai import OpenAI
from datetime import datetime
import pytz
import json
import csv

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
    message['length'] = len(message['content'].split())  # Count the number of words
    return message

# Function to calculate response time between messages
def calculate_response_time(messages):
    for i in range(1, len(messages)):
        current_time = datetime.strptime(messages[i]['timestamp'], "%Y-%m-%d %H:%M:%S")
        previous_time = datetime.strptime(messages[i-1]['timestamp'], "%Y-%m-%d %H:%M:%S")
        messages[i]['response_time'] = (current_time - previous_time).total_seconds()
    return messages

# Function to save chat log in CSV format
def save_chat_log():
    st.session_state["messages"] = calculate_response_time(
        [add_timestamp(msg) if 'timestamp' not in msg else msg for msg in st.session_state["messages"]]
    )
    
    # Prepare CSV file path
    user_email = st.session_state['user'].email.replace('@', '_').replace('.', '_')
    filename = f"{user_email}_{datetime.now(london_tz).strftime('%H%M')}_chat_log.csv"

    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['date', 'time', 'role', 'content', 'length', 'response_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for msg in st.session_state["messages"]:
            # Split timestamp into date and time
            date, time = msg['timestamp'].split(' ')
            writer.writerow({
                'date': date,
                'time': time,
                'role': msg['role'],
                'content': msg['content'],
                'length': msg['length'],
                'response_time': msg.get('response_time', '')
            })
    
    # Upload CSV file
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

# -------------------------------------------------------------------------------------------------
# Authentication Logic (Login, Sign-Up, Password Reset)
# -------------------------------------------------------------------------------------------------
if 'user_info' not in st.session_state:
    col1, col2, col3 = st.columns([1, 2, 1])

    # Authentication form layout
    do_you_have_an_account = col2.selectbox(label='Do you have an account?', options=('Yes', 'No', 'I forgot my password'))
    auth_form = col2.form(key='Authentication form', clear_on_submit=False)
    email = auth_form.text_input(label='Email')
    password = auth_form.text_input(label='Password', type='password') if do_you_have_an_account in {'Yes', 'No'} else auth_form.empty()
    auth_notification = col2.empty()

    # Sign In
    if do_you_have_an_account == 'Yes' and auth_form.form_submit_button(label='Sign In', use_container_width=True, type='primary'):
        with auth_notification, st.spinner('Signing in'):
            auth_functions.sign_in(email, password)

    # Create Account
    elif do_you_have_an_account == 'No' and auth_form.form_submit_button(label='Create Account', use_container_width=True, type='primary'):
        with auth_notification, st.spinner('Creating account'):
            auth_functions.create_account(email, password)

    # Password Reset
    elif do_you_have_an_account == 'I forgot my password' and auth_form.form_submit_button(label='Send Password Reset Email', use_container_width=True, type='primary'):
        with auth_notification, st.spinner('Sending password reset link'):
            auth_functions.reset_password(email)

    # Authentication success and warning messages
    if 'auth_success' in st.session_state:
        auth_notification.success(st.session_state.auth_success)
        del st.session_state.auth_success
    elif 'auth_warning' in st.session_state:
        auth_notification.warning(st.session_state.auth_warning)
        del st.session_state.auth_warning

# -------------------------------------------------------------------------------------------------
# If Logged In, Display Chat Interface
# -------------------------------------------------------------------------------------------------
else:
    # Show user information
    st.header('User information:')
    st.write(st.session_state.user_info)

    # Sign out
    st.header('Sign out:')
    st.button(label='Sign Out', on_click=auth_functions.sign_out, type='primary')

    # Delete Account
    st.header('Delete account:')
    password = st.text_input(label='Confirm your password', type='password')
    st.button(label='Delete Account', on_click=auth_functions.delete_account, args=[password], type='primary')
    
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

# Display chat messages, excluding the system prompt
for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(f"[{msg['timestamp']}] {msg['content']}")

if prompt := st.chat_input():
    handle_chat(prompt)
