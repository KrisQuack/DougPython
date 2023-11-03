from openai import AsyncAzureOpenAI

class GPT:
    def __init__(self, api_version, azure_endpoint, api_key):
        self.client = AsyncAzureOpenAI(
            api_version=api_version,
            azure_endpoint=azure_endpoint,
            api_key=api_key,
        )

    async def gpt48k(self, prompt, message):
        response = await self.client.chat.completions.create(
            model="gpt-4-8k",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content