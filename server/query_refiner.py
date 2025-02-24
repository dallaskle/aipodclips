from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import json
import re
import logging
import sys

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all logs
    format='%(asctime)s [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console handler
        logging.FileHandler('query_refiner.log')  # File handler
    ]
)

# Get logger for this module
logger = logging.getLogger('query_refiner')
logger.setLevel(logging.DEBUG)

# Ensure OpenAI's logger doesn't overwhelm our logs
logging.getLogger('openai').setLevel(logging.WARNING)

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

REFINEMENT_PROMPT = """You are helping refine a user's request for creating short video content. 
The goal is to understand exactly what kind of YouTube videos we should search for to create these shorts.

User Request: {user_input}

First, provide a refined version of the query that better expresses the user's intent.
Then, analyze if this refined query is specific enough to search for relevant YouTube videos.

Even if the query is specific enough, always provide 2-3 clarifying questions that could make the search even more focused.
If the query is not specific enough, provide questions that are necessary to proceed.

If the query is specific enough, also provide a report prompt focused on finding relevant YouTube video links.

Respond in JSON format:
{{
    "is_specific": true/false,
    "clarifying_questions": [
        "list of 2-3 questions that could make the search even more specific",
        "if not specific enough, questions that are necessary to proceed"
    ],
    "refined_query": "the refined query (always provided)",
    "report_prompt": null if not specific, else the report prompt,
    "can_be_more_specific": true if the query could be even more specific, false if it's already highly specific
}}
"""

def _clean_json_string(text: str) -> str:
    logger.debug("Starting JSON string cleaning")
    logger.debug(f"Input text (first 100 chars): {text[:100]}...")
    
    # Remove leading/trailing code fences
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    # Extract the JSON object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end+1]
        logger.debug("Found JSON boundaries")
    else:
        logger.warning("Could not find JSON boundaries in the text")
    
    # Escape newline characters
    text = re.sub(r'(?<!\\)\n', '\\n', text)
    logger.debug(f"Cleaned text (first 100 chars): {text[:100]}...")
    return text

async def refine_query(user_input: str) -> dict:
    """
    Use OpenAI to refine the user's query and determine if more clarification is needed.
    """
    try:
        logger.info("=" * 80)
        logger.info("Starting query refinement process")
        
        # Parse the input if it's a JSON string
        try:
            input_data = json.loads(user_input)
            original_query = input_data.get('original_query', '')
            clarifications = input_data.get('clarifications', [])
            
            # Validate clarifications structure
            if clarifications and isinstance(clarifications, list):
                # Ensure each clarification has required fields
                valid_clarifications = []
                for c in clarifications:
                    if isinstance(c, dict) and 'question' in c and 'answer' in c:
                        valid_clarifications.append(c)
                    else:
                        logger.warning(f"Skipping invalid clarification: {c}")
                
                if valid_clarifications:
                    clarifications_text = '\n'.join(f'Q: {c["question"]}\nA: {c["answer"]}' for c in valid_clarifications)
                    formatted_input = f"""Original Query: {original_query}

Clarifications:
{clarifications_text}"""
                    logger.info("Processing query with clarifications:")
                    logger.info(f"Original query: {original_query}")
                    logger.info("Clarifications:")
                    for c in valid_clarifications:
                        logger.info(f"- Q: {c['question']}")
                        logger.info(f"  A: {c['answer']}")
                else:
                    formatted_input = original_query
                    logger.info(f"Processing original query: {formatted_input}")
            else:
                formatted_input = original_query or user_input
                logger.info(f"Processing simple query: {formatted_input}")
        except json.JSONDecodeError:
            # If not JSON, treat as simple query
            formatted_input = user_input
            logger.info(f"Processing simple query: {formatted_input}")
        
        logger.debug("Sending request to OpenAI")
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant specializing in content creation and research."},
                {"role": "user", "content": REFINEMENT_PROMPT.format(user_input=formatted_input)}
            ],
            response_format={ "type": "json_object" }
        )
        logger.debug("Received response from OpenAI")
        
        text_output = response.choices[0].message.content
        logger.debug("Raw GPT response:")
        logger.debug("-" * 40)
        logger.debug(text_output)
        logger.debug("-" * 40)
        
        text_output = _clean_json_string(text_output)
        
        try:
            parsed_object = json.loads(text_output)
            logger.info("Successfully parsed JSON response")
            logger.info("Query refinement result:")
            logger.info(f"- Is Specific: {parsed_object['is_specific']}")
            logger.info(f"- Number of Questions: {len(parsed_object['clarifying_questions'])}")
            logger.info(f"- Refined Query: {parsed_object['refined_query'][:100]}...")
            if parsed_object['report_prompt']:
                logger.info(f"- Report Prompt: {parsed_object['report_prompt'][:100]}...")
            logger.info("=" * 80)
            return parsed_object
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response")
            logger.error(f"Error message: {str(e)}")
            logger.error(f"Problematic text: {text_output}")
            raise ValueError(f"Failed to parse model response as JSON: {e}\nResponse text: {text_output}")
            
    except Exception as e:
        logger.error("Unexpected error in refine_query")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.exception("Full traceback:")
        raise 