# File: bots/chatbot/chatbot.py

class ChatBot:
    def __init__(self):
        self.name = "DummyBot"

    def get_chat_response_text(self, message):
        """
        Dummy implementation for text response.
        """
        return f"You said: '{message}'. This is a dummy response from {self.name}."

    def get_chat_response_recording(self, audio_data):
        """
        Dummy implementation for audio response.
        """
        return f"I received an audio recording. This is a dummy response from {self.name}."

    def get_image_generation(self, prompt):
        """
        Dummy implementation for image generation.
        """
        return f"You asked me to generate an image with the prompt: '{prompt}'. " \
               f"This is a dummy image generation response from {self.name}."

    def process_image(self, image_data):
        """
        Dummy implementation for image processing.
        """
        return f"I received an image. This is a dummy image processing response from {self.name}."

    def get_chat_response(self, message, additional_params=None):
        """
        General chat response method for compatibility with different bot implementations.
        """
        if additional_params:
            return f"Received message: '{message}' with additional parameters. " \
                   f"This is a dummy response from {self.name}."
        else:
            return self.get_chat_response_text(message)