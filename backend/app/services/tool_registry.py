from app.utils.logger import get_logger
import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import StructuredTool

load_dotenv()

logger = get_logger("Tool_Registry")


class ToolRegistry:
    def __init__(self):

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            task_type="semantic_similarity"
        )

        self.vector_store = Chroma(
            collection_name="agent_tools",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db"
        )

        self._tool_map: Dict[str, StructuredTool] = {}

    def register_tools(self, tools: List[StructuredTool]):
        """
        Takes a list of LangChain/MCP tools, indexes them, and stores them.
        """
        if not tools:
            logger.warning("No tools provided to register.")
            return

        documents = []
        new_tools_count = 0

        for tool in tools:
            self._tool_map[tool.name] = tool

            doc_content = f"Tool Name: {tool.name}\nDescription: {tool.description}"

            documents.append(Document(
                page_content=doc_content,
                metadata={"tool_name": tool.name}
            ))
            new_tools_count += 1

        if documents:
            logger.info(f"Indexing {len(documents)} tools into Vector DB...")
            self.vector_store.add_documents(documents)
            logger.info("Indexing complete.")

    def search_tools(self, query: str, k: int = 5) -> List[StructuredTool]:
        """
        Semantic search: 'Add user' -> finds 'create_contact'
        """
        logger.info(f"Searching tools for query: '{query}'")

        results = self.vector_store.similarity_search(query, k=k)

        found_tools = []
        seen_names = set()

        for doc in results:
            tool_name = doc.metadata["tool_name"]

            if tool_name not in seen_names and tool_name in self._tool_map:
                found_tools.append(self._tool_map[tool_name])
                seen_names.add(tool_name)

        logger.info(
            f"Found {len(found_tools)} relevant tools: {[t.name for t in found_tools]}")
        return found_tools
