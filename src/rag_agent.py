# src/rag_agent.py

import re
from pathlib import Path

from src.agent import Agent
from src.config import (
    DEFAULT_TOP_K,
    LEGIFRANCE_CLIENT_ID,
    LEGIFRANCE_CLIENT_SECRET,
    LLM_MODEL,
    MAX_CONTEXT_CHUNKS,
)
from src.legifrance.legifrance_client import LegifranceClient
from src.legifrance.oauth_client import LegifranceOAuthClient
from src.question_formatter_agent import QuestionFormatterAgent
from src.reference_retriever_agent import ReferenceRetrieverAgent


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
ARTICLE_REFERENCE_PATTERN = re.compile(r"L\d+(?:-\d+)*")


class RagAgent(Agent):
    def __init__(self, vector_db_object):
        super().__init__()
        self.vector_db_object = vector_db_object
        self.question_formatter_agent = QuestionFormatterAgent()
        self.reference_retriever_agent = self._build_reference_retriever_agent()

    def _build_reference_retriever_agent(self):
        if not (LEGIFRANCE_CLIENT_ID and LEGIFRANCE_CLIENT_SECRET):
            return None
        oauth_client = LegifranceOAuthClient(LEGIFRANCE_CLIENT_ID, LEGIFRANCE_CLIENT_SECRET)
        legifrance_client = LegifranceClient(oauth_client)
        return ReferenceRetrieverAgent(legifrance_client)

    def build_context(self, question):
        requetes_recherche = self.question_formatter_agent.format_question(question)
        documents, metadatas = self._retrieve_for_queries(requetes_recherche)

        chunks_formates = [
            self._format_chunk(doc, meta) for doc, meta in zip(documents, metadatas)
        ]

        prompt_system = Agent.read_file(str(PROMPTS_DIR / "rag_prompt_system.txt"))
        prompt_system = prompt_system.replace("{{CHUNKS}}", "\n\n".join(chunks_formates))

        return prompt_system, documents, metadatas

    def _retrieve_for_queries(self, requetes_recherche):
        candidats = []
        articles_vus = set()

        for requete in requetes_recherche:
            sous_documents, sous_metadatas = self.vector_db_object.retrieve(
                requete, n=DEFAULT_TOP_K
            )
            for doc, meta in zip(sous_documents, sous_metadatas):
                article = meta.get("article")
                if article in articles_vus:
                    continue
                articles_vus.add(article)
                candidats.append((doc, meta))

        candidats.sort(key=lambda item: item[1].get("distance", float("inf")))
        candidats = candidats[:MAX_CONTEXT_CHUNKS]

        documents = [doc for doc, _ in candidats]
        metadatas = [meta for _, meta in candidats]
        return documents, metadatas

    def _format_chunk(self, doc, meta):
        article = meta.get("article", "Article inconnu")
        theme = meta.get("theme", "")
        return f"[Article {article} - {theme}]\n{doc}"

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
        documents, metadatas = self._keep_cited_sources(response, documents, metadatas)
        metadatas = self._check_sources_freshness(documents, metadatas)
        return response, documents, metadatas

    def _check_sources_freshness(self, documents, metadatas):
        if self.reference_retriever_agent is None:
            return metadatas
        return self.reference_retriever_agent.check_freshness(documents, metadatas)

    def _keep_cited_sources(self, response, documents, metadatas):
        articles_cites = set(ARTICLE_REFERENCE_PATTERN.findall(response))
        paires_citees = [
            (doc, meta)
            for doc, meta in zip(documents, metadatas)
            if meta.get("article") in articles_cites
        ]
        documents = [doc for doc, _ in paires_citees]
        metadatas = [meta for _, meta in paires_citees]
        return documents, metadatas
