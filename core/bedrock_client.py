"""AWS Bedrock client.

Provides a shared boto3 Bedrock runtime client and helper functions
for invoking Claude Sonnet 4.5 and Llama 3.3 70B on AWS Bedrock.
"""

import json
import boto3
from core.config import settings

_client = None


def get_bedrock_client():
    """Return a shared Bedrock runtime client (lazy init)."""
    global _client
    if _client is None:
        _client = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.aws_region,
        )
    return _client


def invoke_claude(
    prompt: str,
    system: str = "",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """Invoke Claude Sonnet 4.5 on Bedrock and return the response text.

    Args:
        prompt:      The user message.
        system:      Optional system prompt.
        max_tokens:  Maximum tokens to generate.
        temperature: Sampling temperature (lower = more deterministic).

    Returns:
        The model's text response as a plain string.
    """
    client = get_bedrock_client()

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    response = client.invoke_model(
        modelId=settings.bedrock_claude_model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def invoke_llama(
    prompt: str,
    max_gen_len: int = 512,
    temperature: float = 0.3,
) -> str:
    """Invoke Llama 3.3 70B on Bedrock and return the response text.

    Args:
        prompt:      The full prompt string (instruction + input).
        max_gen_len: Maximum tokens to generate.
        temperature: Sampling temperature.

    Returns:
        The model's generated text as a plain string.
    """
    client = get_bedrock_client()

    body = {
        "prompt": prompt,
        "max_gen_len": max_gen_len,
        "temperature": temperature,
    }

    response = client.invoke_model(
        modelId=settings.bedrock_llama_model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["generation"]
