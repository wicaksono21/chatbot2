import openai

openai.api_key = 'your-actual-openai-api-key-here'

try:
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Hello, how can I assist you?"},
            {"role": "user", "content": "I need help writing an essay."}
        ],
        max_tokens=50
    )
    print(response.choices[0].message['content'])
except openai.error.APIConnectionError as e:
    print(f"Connection error: {str(e)}")
except openai.error.OpenAIError as e:
    print(f"OpenAI error: {str(e)}")
