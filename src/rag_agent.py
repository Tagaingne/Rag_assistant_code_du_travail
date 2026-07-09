# src/rag_agent.py

from pathlib import Path

from src.agent import Agent
from src.config import DEFAULT_TOP_K, LLM_MODEL


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class RagAgent(Agent):
    def __init__(self, vector_db_object):
        super().__init__()
        self.vector_db_object = vector_db_object

    def build_context(self, question):
        documents, metadatas = self.vector_db_object.retrieve(question, n=DEFAULT_TOP_K)

        chunks_formates = []
        for doc, meta in zip(documents, metadatas):
            article = meta.get("article", "Article inconnu")
            theme = meta.get("theme", "")
            chunk = f"[Article {article} - {theme}]\n{doc}"
            chunks_formates.append(chunk)

        prompt_system = Agent.read_file(str(PROMPTS_DIR / "rag_prompt_system.txt"))
        prompt_system = prompt_system.replace("{{CHUNKS}}", "\n\n".join(chunks_formates))

        return prompt_system, documents, metadatas

    def ask(self, question):
        prompt_system, documents, metadatas = self.build_context(question)

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt_system
                },
                {
                    "role": "user",
                    "content": question,
                }
            ],
            model=LLM_MODEL,
            temperature=0,
        )

        response = chat_completion.choices[0].message.content
        return response, documents, metadatas
