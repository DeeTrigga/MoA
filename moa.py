# Mixture-of-Agents in 50 lines of code
import asyncio
import os
import together
from together import AsyncTogether, Together
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the secret key
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')

# Initialize the clients
client = Together(api_key=TOGETHER_API_KEY)
async_client = AsyncTogether(api_key=TOGETHER_API_KEY)

user_prompt = "What are 3 fun things to do in SF?"
reference_models = [
    "Qwen/Qwen2-72B-Instruct",
    "Qwen/Qwen1.5-72B-Chat",
    "mistralai/Mixtral-8x22B-Instruct-v0.1",
    "databricks/dbrx-instruct",
]
aggregator_model = "mistralai/Mixtral-8x22B-Instruct-v0.1"
aggregator_system_prompt = """You have been provided with a set of responses from various open-source models to the latest user query. Your task is to synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.

Responses from models:"""

async def run_llm(model):
    """Run a single LLM call with a reference model."""
    for sleep_time in [1, 2, 4]:
        try:
            response = await async_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.7,
                max_tokens=512,
            )
            break
        except together.error.RateLimitError as e:
            print(e)
            await asyncio.sleep(sleep_time)
    return response.choices[0].message.content

async def main():
    results = await asyncio.gather(*[run_llm(model) for model in reference_models])
    finalStream = client.chat.completions.create(
        model=aggregator_model,
        messages=[
            {"role": "system", "content": aggregator_system_prompt + "\n" + "\n".join([f"{i+1}. {str(element)}" for i, element in enumerate(results)])},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
    )
    for chunk in finalStream:
        print(chunk.choices[0].delta.content or "", end="", flush=True)

asyncio.run(main())