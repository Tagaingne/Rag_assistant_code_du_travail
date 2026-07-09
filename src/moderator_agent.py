# src/moderator_agent.py

from agent import Agent
from config import LLM_MODEL
from pathlib import Path

import json

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class ModeratorAgent(Agent):
    def __init__(self):
        super().__init__()

    def moderate_question(self, question):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": Agent.read_file(str(PROMPTS_DIR / "moderator_prompt_system.txt"))
                },
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            temperature=0,
        )

        moderation = json.loads(chat_completion.choices[0].message.content)
        return moderation