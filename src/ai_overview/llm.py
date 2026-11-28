import logging
import os

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncGroq,
    RateLimitError,
)

logger = logging.getLogger(__name__)
load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL")


def create_groq_client() -> AsyncGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    if not GROQ_MODEL:
        raise RuntimeError("GROQ_MODEL is not configured.")

    return AsyncGroq(api_key=api_key)

client = create_groq_client()

async def generate(messages: list) -> str | None:
    try:
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,
            max_completion_tokens=512,
            reasoning_effort="low",
        )
        content = completion.choices[0].message.content
        return content.strip() if content else None

    except RateLimitError:
        logger.warning("Groq free-tier rate limit reached.")
        return None

    except APITimeoutError:
        logger.warning("Groq request timed out.")
        return None
    
    except APIConnectionError:
        logger.exception("Could not connect to Groq.")
        return None

    except APIError as e:
        logger.error(f"Groq API error: {e}")
        return None

