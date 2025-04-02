import openai
import numpy as np
import copy
import ast
import re
import math
# from openai import OpenAI
import time
import anthropic
import boto3
import json
from botocore.exceptions import ClientError
import os
from botocore.config import Config


def GPT_response(messages, model_name = 'gpt-4o'):
  if model_name in ['gpt-4-turbo-preview','gpt-4-1106-preview', 'gpt-4', 'gpt-4o', 'gpt-4-32k', 'gpt-3.5-turbo-0301', 'gpt-4-0613', 'gpt-4-32k-0613', 'gpt-3.5-turbo-16k-0613', 'gpt-3.5-turbo']:
    #print(f'-------------------Model name: {model_name}-------------------')
    # client = OpenAI()
    response = openai.ChatCompletion.create(
      model=model_name,
      messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": messages}
        ],
      temperature = 0.0,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
  elif model_name == 'o1-preview':
     response = openai.ChatCompletion.create(
        model="o1-preview",
        messages=[
            {
                "role": "user", 
                "content": messages
            }
        ]
    )
  else:
    response = ''

  return response.choices[0].message.content



# This function uses AWS to access Claude, please replace with your own function to call Claude
os.environ['AWS_PROFILE'] = "MyProfile1"
os.environ['AWS_DEFAULT_REGION'] = "us-west-2"

def Claude_response(messages):
  # import pdb; pdb.set_trace()
  region ="us-east-1"
  config = Config(read_timeout=1000)
  client = boto3.client('bedrock-runtime',region,config=config) 
  model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

  native_request = {
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 4096,
      "temperature": 0.0,
      "messages": [
          {
              "role": "user",
              "content": [{"type": "text", "text": messages}],
          }
      ],
  }

  # Convert the native request to JSON.
  request = json.dumps(native_request)

  try:
      # Invoke the model with the request.
      response = client.invoke_model(modelId=model_id, body=request)

  except (ClientError, Exception) as e:
      print(f"ERROR: Can't invoke '{model_id}'. Reason: {e}")
      exit(1)

  # Decode the response body.
  model_response = json.loads(response["body"].read())

  # Extract and print the response text.
  response_text = model_response["content"][0]["text"]
  return response_text
