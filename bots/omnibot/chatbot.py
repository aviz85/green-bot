from dotenv import load_dotenv
import json
import os
import sys
import logging
import requests

# Load environment variables from .env file if it exists
load_dotenv()

# Add the tools directory to the system path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))

# Try to import the generate_image function from tools/generate_image.py
try:
    from generate_image import generate_image
    logging.debug("generate_image function loaded successfully.")
except ImportError as e:
    logging.error(f"Error importing generate_image: {e}")
    sys.exit(1)

# Get the API key from the environment variable
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

if ANTHROPIC_API_KEY is None:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables.")

# Setup logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')

class ChatBot:
    def __init__(self, prompts_file=None, max_history=30):
        if prompts_file is None:
            prompts_file = os.path.join(os.path.dirname(__file__), 'prompts.json')
        
        with open(prompts_file, 'r') as f:
            prompts_data = json.load(f)
        self.prompts = prompts_data["prompts"]
        self.max_history = max_history
        self.conversation_history = []
        
        self.initial_prompt_label = "sarcastic_friend"
        self.system_message = self.get_system_message()

    def get_system_message(self):
        system_prompt = next((prompt["prompt"] for prompt in self.prompts if prompt["label"] == self.initial_prompt_label), None)
        if system_prompt:
            return system_prompt
        else:
            raise ValueError(f"Prompt with label '{self.initial_prompt_label}' not found in prompts.")

    def add_message_to_history(self, role, content):
        # Validate the alternating pattern
        if self.conversation_history:
            last_role = self.conversation_history[-1]["role"]
            if (role == "user" and last_role != "assistant") or (role == "assistant" and last_role != "user"):
                raise ValueError(f"Invalid message sequence. Expected {last_role} role, but got {role}.")

        # Append the message
        self.conversation_history.append({"role": role, "content": content})
        
        # If over max_history, remove the first two messages
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[2:]
            
        return True

    def get_chat_response_text(self, user_message):
        try:
            # Add the user's message to the conversation history
            self.add_message_to_history("user", [{"type": "text", "text": user_message}])
            
            # Define the tools to call
            tools = [
                {
                    "name": "generate_image",
                    "description": "Generate an image based on a given prompt",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The prompt for generating the image"
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            ]

            headers = {
                "content-type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            }

            data = {
                "model": "claude-3-5-sonnet-20240620",
                "max_tokens": 1024,
                "system": self.system_message,
                "tools": tools,
                "messages": self.conversation_history
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            response_data = response.json()
            if response.status_code != 200:
                raise Exception(f"API request failed with status {response.status_code}: {response_data}")

            # Check if the model wants to use a tool
            if response_data.get('stop_reason') == 'tool_use':
                for content_block in response_data.get('content', []):
                    if content_block.get('type') == 'tool_use':
                        tool_name = content_block.get('name')
                        tool_use_id = content_block.get('id')
                        tool_input = content_block.get('input')
                        tool_use = {
                            "role": "assistant",
                            "content": response_data.get('content')
                        }
                        self.add_message_to_history("assistant", tool_use["content"])
                        print(f"Tool use requested: {tool_name}")
                        print(f"Tool input: {tool_input}")
                        
                        if tool_name == "generate_image":
                            prompt = tool_input.get("prompt")
                            image_url = generate_image(prompt)
                            print(f"Image generated with absolute path: {image_url}")
                            # Prepare tool result
                            tool_result = {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": image_url
                                    }
                                ]
                            }
                            # Add tool result to conversation history
                            if self.add_message_to_history("user", tool_result["content"]):
                                print('added tool result to history')
                
                # Make another API call with the tool result
                data["messages"] = self.conversation_history
                data["system"] = "use this image_url to response the user with markup image link"
                print(data["messages"])
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data
                )
                response_data = response.json()
                print(response_data)
                if response.status_code != 200:
                    raise Exception(f"API request failed with status {response.status_code}: {response_data}")
                response_data['content'] = response_data.get('content', [{"type": "text", "text": f"![{image_url}]"}])

            # Add the assistant's response to the conversation history
            self.add_message_to_history("assistant", response_data.get('content', []))

            # Extract and return the text response
            assistant_response = ""
            for content_block in response_data.get('content', []):
                if content_block.get('type') == 'text':
                    assistant_response += content_block.get('text', '')
            return assistant_response

        except Exception as e:
            logging.error(f"Error in get_chat_response_text: {str(e)}")
            return str({"error": str(e)})
    
    def get_chat_response_recording(self, audio_data):
        """
        Placeholder for audio response processing.
        """
        return "Audio processing is not implemented yet."

    def process_image(self, image_data):
        """
        Placeholder for image processing.
        """
        return "Image processing is not implemented yet."

    def reset_chat_history(self):
        self.conversation_history.clear()

# Instantiate ChatBot
chatbot = ChatBot()

# Example usage
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            break
        response = chatbot.get_chat_response_text(user_input)
        print("ChatBot:", response)