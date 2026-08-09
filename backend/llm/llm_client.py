import os
import logging
import asyncio
from typing import List, Dict, Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

# SDK Imports
from google import genai
from google.genai import types
from groq import AsyncGroq
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Global Semaphore to limit concurrent LLM requests and prevent 429 errors
# Set to 2 to stay well under Gemini free-tier limit of 15 requests/minute
llm_semaphore = asyncio.Semaphore(2)

# Initialize Clients conditionally (they will pull from os.environ by default)
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)

def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return AsyncGroq(api_key=api_key)

def get_openrouter_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    return AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

@retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(4))
async def call_gemini(prompt: str, system_instruction: str = "") -> str:
    async with llm_semaphore:
        client = get_gemini_client()
        
        config = types.GenerateContentConfig(temperature=0.2)
        if system_instruction:
            config.system_instruction = system_instruction
            
        # google-genai async support
        response = await client.aio.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=config
        )
        return response.text

@retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(4))
async def call_groq(prompt: str, system_instruction: str = "") -> str:
    async with llm_semaphore:
        client = get_groq_client()
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
            
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content

@retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(4))
async def call_openrouter(prompt: str, system_instruction: str = "") -> str:
    async with llm_semaphore:
        client = get_openrouter_client()
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
            
        response = await client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct:free",
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content

async def generate_text(prompt: str, system_instruction: str = "", provider_pref: str = "gemini") -> str:
    """
    Primary fallback chain: Gemini -> Groq -> OpenRouter
    If provider_pref is 'groq' (e.g. for fast pre-filter), it tries Groq first.
    """
    providers = [call_gemini, call_groq, call_openrouter]
    if provider_pref == "groq":
        providers = [call_groq, call_gemini, call_openrouter]
        
    last_err = None
    for call_fn in providers:
        try:
            return await call_fn(prompt, system_instruction)
        except Exception as e:
            real_err = e
            if hasattr(e, "last_attempt") and e.last_attempt is not None:
                real_err = e.last_attempt.exception()
            logger.warning(f"LLM provider {call_fn.__name__} failed: {type(real_err).__name__} - {real_err}")
            last_err = real_err
            continue
            
    raise RuntimeError(f"All LLM providers failed. Last error: {last_err}")

@retry(wait=wait_exponential(multiplier=2, min=5, max=30), stop=stop_after_attempt(4))
async def get_embeddings(texts: List[str]) -> List[List[float]]:
    try:
        client = get_gemini_client()
    except ValueError:
        return [[0.1] * 768 for _ in texts]
        
    embeddings = []
    
    # Process sequentially or we can use gather, but to avoid rate limits, we use the semaphore
    async def embed_single(text: str):
        async with llm_semaphore:
            response = await client.aio.models.embed_content(
                model="gemini-embedding-2",
                contents=text
            )
            return response.embeddings[0].values

    try:
        tasks = [embed_single(t) for t in texts]
        embeddings = await asyncio.gather(*tasks)
        return embeddings
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return [[0.1] * 768 for _ in texts]

def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x*y for x, y in zip(a, b))
    norm_a = sum(x*x for x in a) ** 0.5
    norm_b = sum(x*x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
