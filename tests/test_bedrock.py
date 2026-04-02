"""Quick sanity test for AWS Bedrock connectivity.

Tests both Claude Sonnet 4.5 and Llama 3.3 70B without requiring
a .env file — uses boto3 directly with ambient AWS credentials.
"""

import json
import boto3

AWS_REGION = "us-east-1"
CLAUDE_MODEL_ID = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
LLAMA_MODEL_ID  = "us.meta.llama3-3-70b-instruct-v1:0"


client = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def test_claude():
    print("=" * 50)
    print("Testing Claude Sonnet 4.5 ...")
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 64,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": "Say 'Claude on Bedrock works!' and nothing else."}],
    }
    response = client.invoke_model(
        modelId=CLAUDE_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    text = result["content"][0]["text"]
    print(f"Response: {text}")
    print("Claude test PASSED")


def test_llama():
    print("=" * 50)
    print("Testing Llama 3.3 70B ...")
    body = {
        "prompt": "Say 'Llama on Bedrock works!' and nothing else.",
        "max_gen_len": 32,
        "temperature": 0.3,
    }
    response = client.invoke_model(
        modelId=LLAMA_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    text = result["generation"]
    print(f"Response: {text}")
    print("Llama test PASSED")


if __name__ == "__main__":
    try:
        test_claude()
    except Exception as e:
        print(f"Claude test FAILED: {e}")

    try:
        test_llama()
    except Exception as e:
        print(f"Llama test FAILED: {e}")

    print("=" * 50)
    print("Done.")
