import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
)

# Test 1: Amazon Titan Text Embeddings V2
embedding_response = client.invoke_model(
    modelId=os.environ["BEDROCK_EMBED_MODEL"],
    body=json.dumps({
        "inputText": "Hello Amazon Bedrock",
        "dimensions": 1024,
        "normalize": True,
    }),
    contentType="application/json",
    accept="application/json",
)

embedding_data = json.loads(embedding_response["body"].read())
print("Embedding dimension:", len(embedding_data["embedding"]))

# Test 2: Amazon Nova Lite
chat_response = client.converse(
    modelId=os.environ["BEDROCK_CHAT_MODEL"],
    messages=[
        {
            "role": "user",
            "content": [{"text": "Explain RAG in one sentence."}],
        }
    ],
    inferenceConfig={"maxTokens": 200},
)

response_text = chat_response["output"]["message"]["content"][0]["text"]
print("Nova Response:", response_text)