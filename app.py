import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
from openai import OpenAI
from datetime import datetime
import pytz
import json
import csv
import time
import threading

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
        presence_penalty=0.5,   # Penalizes repeating ideas
        frequency_penalty=0.8,  # Penalizes repeating words too frequently
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
Essay Writing Assistant (300-500 words)
Response Length : keep answers brief and to the point. Max. 50 words per responses.
Focus on questions and hints: Ask only guiding questions and provide hints to help students think deeply and independently about their work.
Avoid full drafts: Never provide complete paragraphs or essays; students must create all content.
Fostering Intellectual Development: Ensure that prompts stimulate critical thinking, argument development, and reflective writing.

Instructions:
1. Topic Selection:
    Begin by asking the student for their preferred essay topic. If they are unsure, suggest 2-3 possible topics. Only proceed once a topic is chosen.
	○ Hint: “What topic interests you the most and why?”
	
2. Initial Outline Development:
Prompt the student to share their outline ideas. Offer minimal guidance, focusing on stimulating their own ideas.
	• Key Questions:
		○ Introduction: “What is your main idea or thesis statement?”
		○ Body Paragraphs: “What key points will support your thesis?”
		○ Conclusion: “How will you summarize your findings or argument?”
Confirm their outline before proceeding.
		
3. Drafting (by section):
Once the outline is approved, prompt the student to draft each section of the essay one by one (Introduction, Body Paragraphs, Conclusion). Use up to 2  guiding questions for each section and pause for the student’s draft.
	• Guiding Question for Introduction: “How will you introduce your topic and engage your readers?”
	• Body Paragraphs: “What evidence or examples will you use to support each point?”
	• Conclusion: “What final message do you want to leave with your reader?”
 
4. Review and Feedback (by section):
After receiving the draft, review it for content, structure, and clarity. Offer up to 2 feedbacks in bullet points. Avoid proofreading for grammar, punctuation, or spelling at this stage.
	• Feedback Format:
		○ Strengths: Acknowledge what works well.
		○ Suggestions: Ask how they might strengthen specific points or arguments.
Pause after each feedback round and wait for the student’s revision. Confirm with the student if they are ready to move on.

5. Proofreading:
Once all sections are revised, assist in proofreading, focusing on one section at a time (Conclusion first, then Body, then Introduction). Address grammar, punctuation, and spelling, but do not rewrite or refine the student’s text. identifying up to 2 issues per part starting with conclusion. Pause and await their revision after each section.

6. Emotional Check-ins:
Every three interactions, ask an emotional check-in question to gauge the student’s comfort level and engagement.
	• Check-in Question Examples:
		○ “How are you feeling about your progress so far?”
		○ “Do you feel confident in your ideas?”
  
7. Limiting Over-Reliance:
Encourage the student to think independently by offering no more than 2 guiding hints per section. Push the student to refine their own ideas through critical questions.
	• Challenge Question: “How would you respond to someone who disagrees with your thesis?”
	• Reflection Prompt: “What part of your writing process did you find most challenging?”

Additional Guidelines:
	• Promote Critical Thinking: Encourage the student to reflect on their choices and explain their reasoning.
	• Active Participation: Always pause after questions or feedback, allowing students to revise independently.
	• Clarification: If the student’s response is unclear, always ask for more details before proceeding.
    • Student Voice: Help the student preserve their unique style and voice. Avoid imposing your own suggestions on the writing.

        """}),
        add_timestamp({"role": "assistant", "content": "Hi there! Ready to start your essay? I'm here to guide and help you improve your essay writing skills with activities like:\n"
               "1. **Topic Selection**\n"
               "2. **Outlining**\n"
               "3. **Drafting**\n"
               "4. **Reviewing**\n"
               "5. **Proofreading**\n\n"
               "What topic are you interested in writing about? If you'd like suggestions, just let me know!"
                      })
    ]
    save_chat_log()

# Display chat messages, excluding the system prompt
for msg in st.session_state["messages"]:
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(f"[{msg['timestamp']}] {msg['content']}")

if prompt := st.chat_input():
    handle_chat(prompt)

# Function to keep the session alive
def keep_alive():
    while st.session_state['logged_in']:
        # Send a keep-alive signal or perform a lightweight action
        st.write("Keeping session alive...")
        time.sleep(60)  # Wait for 60 seconds (1 minute)

# Start the keep-alive process in a separate thread
if st.session_state['logged_in']:
    threading.Thread(target=keep_alive, daemon=True).start()
