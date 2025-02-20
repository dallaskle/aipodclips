from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

REFINEMENT_PROMPT = """You are helping refine a user's request for creating short video content. 
The goal is to understand exactly what kind of YouTube videos we should search for to create these shorts.

User Request: {user_input}

Analyze if this request is specific enough to search for relevant YouTube videos. If not, ask clarifying questions.
If it is specific enough, provide:
1. A refined search query
2. A report prompt focused on finding relevant YouTube video links

Respond in JSON format:
{{
    "is_specific": true/false,
    "clarifying_questions": [] if specific, else list of questions,
    "refined_query": null if not specific, else the refined query,
    "report_prompt": null if not specific, else the report prompt
}}
"""

def _clean_json_string(text: str) -> str:
    # Remove leading/trailing code fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    # Extract the JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
    # Escape newline characters
    text = re.sub(r'(?<!\\)\n', '\\n', text)
    return text

async def refine_query(user_input: str) -> dict:
    """
    Use OpenAI to refine the user's query and determine if more clarification is needed.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant specializing in content creation and research."},
                {"role": "user", "content": REFINEMENT_PROMPT.format(user_input=user_input)}
            ],
            response_format={ "type": "json_object" }
        )
        
        text_output = response.choices[0].message.content
        text_output = _clean_json_string(text_output)
        
        try:
            parsed_object = json.loads(text_output)
            return parsed_object
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse model response as JSON: {e}\nResponse text: {text_output}")
            
    except Exception as e:
        print(f"OpenAI Error: {str(e)}")
        raise 