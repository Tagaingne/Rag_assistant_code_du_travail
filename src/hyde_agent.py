# src/hyde_agent.py

from pathlib import Path

from src.agent import Agent
from src.config import LLM_MODEL


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class HydeAgent(Agent):
    def __init__(self):
        super().__init__()

    def generate_hypothetical_answer(self, question: str) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": Agent.read_file(str(PROMPTS_DIR / "hyde_prompt_system.txt"))
                },
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model=LLM_MODEL,
            temperature=0,
        )

        return chat_completion.choices[0].message.content
