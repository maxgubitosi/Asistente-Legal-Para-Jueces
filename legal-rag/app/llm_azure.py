import asyncio
from openai import AsyncAzureOpenAI
from typing import List, Dict
from .config import get_settings

settings = get_settings()

azure_client = AsyncAzureOpenAI(
    api_key=settings.azure_api_key,
    azure_endpoint=settings.azure_endpoint,
    api_version=settings.azure_api_version,
)

def _format(messages: List[Dict[str, str]]):
    """convierte [{'role': 'user', 'content': '…'}] -> mismo formato."""
    return messages

async def _arun(messages, max_tokens):
    rsp = await azure_client.chat.completions.create(
        model=settings.azure_deployment,   # <- nombre de deployment
        messages=_format(messages),
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return rsp.choices[0].message.content.strip()

def run_llm(messages, max_tokens=512):
    """Función síncrona compatible con el resto del código."""
    return asyncio.run(_arun(messages, max_tokens))
