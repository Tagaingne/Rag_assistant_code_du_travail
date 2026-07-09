# src/decomposition_agent.py

import json
from pathlib import Path

from src.agent import Agent
from src.config import LLM_MODEL


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class DecompositionAgent(Agent):
    def __init__(self):
        super().__init__()

    def decompose_question(self, question: str) -> list[str]:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": Agent.read_file(str(PROMPTS_DIR / "decomposition_prompt_system.txt"))
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

        result = json.loads(chat_completion.choices[0].message.content)
        sous_questions = result.get("sous_questions", [])
        return sous_questions if sous_questions else [question]
