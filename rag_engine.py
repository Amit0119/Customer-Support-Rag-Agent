import os
import logging
from typing import List, Dict, Any

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# Configure logging to monitor system operations and errors
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RAGEngine:
    """
    RAGEngine is responsible for orchestrating the Retrieval-Augmented Generation pipeline.
    It manages the FAISS vector store, OpenAI LLM integrations, and LangChain memory retrieval.
    """
    def __init__(self, data_path: str = "data/mock_faq.txt"):
        """
        Initializes the RAG Engine, loads the vector store and sets up the chains.
        """
        self.data_path = data_path
        
        # Initialize FastEmbed embeddings (avoids PyTorch meta tensor bugs on Windows)
        self.embeddings = FastEmbedEmbeddings()
        self.llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
        
        self.vector_store = None
        self.rag_chain = None
        
        # Safely initialize the core components during object creation
        self._initialize_system()

    def _initialize_system(self):
        """Loads data, creates FAISS index, and builds the retrieval chain."""
        try:
            self.vector_store = self._get_or_create_vector_store()
            if self.vector_store:
                self.rag_chain = self._build_rag_chain()
                logging.info("RAG Engine initialized successfully.")
            else:
                logging.error("Failed to initialize vector store. Please check the data source.")
        except Exception as e:
            logging.error(f"Error during initialization: {str(e)}")

    def _get_or_create_vector_store(self) -> FAISS:
        """
        Loads the text document, splits it into chunks, and creates a FAISS vector store.
        """
        if not os.path.exists(self.data_path):
            logging.error(f"Data file not found at {self.data_path}")
            return None

        try:
            loader = TextLoader(self.data_path, encoding="utf-8")
            documents = loader.load()

            # Split the document into chunks to allow for granular semantic search
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len
            )
            splits = text_splitter.split_documents(documents)

            # Create and return the FAISS vector store
            vector_store = FAISS.from_documents(splits, self.embeddings)
            return vector_store
        except Exception as e:
            logging.error(f"Error creating vector store: {str(e)}")
            return None

    def _build_rag_chain(self):
        """
        Constructs the LangChain conversational retrieval chain with memory support.
        """
        # Retrieve the top 3 most relevant context chunks
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        # 1. Contextualize question prompt
        # This prompt helps the LLM rephrase the user's question into a standalone query,
        # resolving any pronouns or references based on the chat history.
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # 2. Answer question prompt
        # This prompt is used to generate the final answer using the retrieved context.
        system_prompt = (
            "You are a helpful and professional customer support assistant for GigaCorp. "
            "Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer or the information is not in the context, "
            "politely say that you don't know and advise them to contact support@gigacorp.com. "
            "Do not make up information. Keep your answers clear and concise.\n\n"
            "Context:\n{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)

        # 3. Combine into a final retrieval chain that returns the generated answer and the source documents
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        return rag_chain

    def get_response(self, user_query: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Processes a user query and returns the AI response along with source documents.
        Handles formatting the chat history for LangChain.
        """
        if not self.rag_chain:
            return {
                "answer": "System is currently unavailable due to an initialization error. Please check backend logs.",
                "sources": []
            }

        try:
            # Convert UI history format to LangChain message format
            formatted_history = []
            for msg in chat_history:
                if msg["role"] == "user":
                    formatted_history.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_history.append(AIMessage(content=msg["content"]))

            # Execute the RAG chain
            response = self.rag_chain.invoke({
                "input": user_query,
                "chat_history": formatted_history
            })

            return {
                "answer": response.get("answer", "I could not generate an answer."),
                "sources": response.get("context", [])
            }
        except Exception as e:
            logging.error(f"Error during LLM generation: {str(e)}")
            return {
                "answer": "I apologize, but I am having trouble connecting to my knowledge base right now. Please try again later.",
                "sources": []
            }
