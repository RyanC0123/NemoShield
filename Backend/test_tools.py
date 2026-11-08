from openai import OpenAI
from app.config import NVIDIA_API_KEY

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY,
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_ip_reputation",
            "description": "Look up risk score of an IP",
            "parameters": {
                "type": "object",
                "properties": {
                    "ip": {"type": "string"}
                },
                "required": ["ip"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    messages=[
        {
            "role": "user",
            "content": "IP 198.51.100.24 had 32 failed SSH logins in 60s. Check its reputation."
        }
    ],
    tools=tools,
)

message = response.choices[0].message
print("TOOL CALLS:", message.tool_calls)
print("TEXT:", message.content)