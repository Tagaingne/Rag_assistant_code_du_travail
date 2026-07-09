# src/agent.py

from groq import Groq

from src.config import GROQ_API_KEY


class MissingGroqApiKey(Exception):
    def __init__(self):
        super().__init__("La variable GROQ_API_KEY est absente du fichier .env")


class Agent:
    def __init__(self):
        if not GROQ_API_KEY:
            raise MissingGroqApiKey()
        self.client = Groq(api_key=GROQ_API_KEY)

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
