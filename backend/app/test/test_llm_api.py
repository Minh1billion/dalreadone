from groq import Groq
from app.core.config import Config

def test_groq():
    client = Groq(api_key=Config.GROQ_API_KEY)

    response = client.chat.completions.create(
        model=Config.MODEL_ID,
        messages=[
            {"role": "user", "content": "Hello"}
        ]
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    test_groq()