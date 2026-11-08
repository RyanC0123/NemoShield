
from openai import OpenAI
from app.config import NVIDIA_API_KEY

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
    timeout=30.0,
)

response = client.chat.completions.create(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    messages=[
        {
            "role": "user",
            "content": "Explain what a firewall is in one sentence."
        }
    ],
    max_tokens=150,
    extra_body={
    "chat_template_kwargs": {
        "enable_thinking": False
    }
},
)

print(response.choices[0].message.content)
