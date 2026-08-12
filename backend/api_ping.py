import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from tavily import AsyncTavilyClient

load_dotenv()

async def ping():
    print("Pinging OpenRouter...")
    try:
        client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY"))
        resp = await client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print("OpenRouter OK: " + str(resp.choices[0].message.content))
    except Exception as e:
        print(f"OpenRouter Failed: {e}")

    print("Pinging Tavily...")
    try:
        tavily = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEYS").split(",")[0].strip())
        res = await tavily.search("hello")
        print("Tavily OK")
    except Exception as e:
        print(f"Tavily Failed: {e}")

if __name__ == "__main__":
    asyncio.run(ping())
