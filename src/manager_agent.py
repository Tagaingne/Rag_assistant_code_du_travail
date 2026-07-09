# src/manager_agent.py

from moderator_agent import ModeratorAgent
from rag_agent import RagAgent


class PromptInjectionDetected(Exception):
    def __init__(self, raison: str):
        self.raison = raison
        super().__init__(raison)


class ManagerAgent:
    def __init__(self, vector_db_object):
        self.moderator_agent = ModeratorAgent()
        self.rag_agent = RagAgent(vector_db_object)

    def ask(self, question):
        # 1) Modération
        moderation = self.moderator_agent.moderate_question(question)

        if moderation.get("prompt_injection"):
            raise PromptInjectionDetected(moderation.get("raison", ""))

        # 2) Génération RAG
        response, documents, metadatas = self.rag_agent.ask(question)
        return response, documents, metadatas