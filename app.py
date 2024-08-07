import streamlit as st
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key='')  # Replace with your OpenAI API key

def converse_with_openai(input_text):
    # Define the conversation system prompt
    messages = [
        {
            "role": "system",
            "content": (
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
                "   • Clarifications: Always ask for clarification if the student's request is unclear to avoid giving a complete essay response.\n"
            )
        },
        {
            "role": "user",
            "content": input_text
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=1,
        max_tokens=150
    )
    return response.choices[0].message.content if response.choices else "Sorry, I couldn't generate a response. Please try again."

st.title('Essay Writing Assistant')

# User input for the conversation
input_text = st.text_input("Type your message here:", value="", key="user_input")

send_button = st.button('Send')

# Handling the send button action
if send_button and input_text:
    conversation = st.session_state.get('conversation', '')
    conversation += f"You: {input_text}\n"
    ai_response = converse_with_openai(input_text)
    conversation += f"Assistant: {ai_response}\n"
    st.session_state.conversation = conversation  # Update the conversation in state

# Display the conversation history in one text area
if 'conversation' in st.session_state:
    st.text_area("Chat", value=st.session_state.conversation, height=400, disabled=True)
else:
    st.session_state.conversation = ""  # Initialize the conversation state if not already done
