"""
Vector Store for Long-term Memory
"""
from typing import List, Dict, Any, Optional
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import settings
from app.utils.logger import logger


class VectorStore:
    """Vector store for managing event memories and context"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        if settings.VECTOR_STORE_TYPE == "chroma":
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY
            )
            
            self.vectorstore = Chroma(
                client=self.client,
                embedding_function=self.embeddings
            )
        
        logger.info(f"Vector store initialized: {settings.VECTOR_STORE_TYPE}")
    
    def add_event_memory(
        self,
        event_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add event memory to vector store
        
        Args:
            event_id: Event identifier
            content: Content to store
            metadata: Additional metadata
        """
        try:
            metadata = metadata or {}
            metadata["event_id"] = event_id
            metadata["type"] = "event_memory"
            
            # Split content into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(content)
            
            # Add to vector store
            self.vectorstore.add_texts(
                texts=chunks,
                metadatas=[metadata] * len(chunks)
            )
            
            logger.info(f"Added event memory for event {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to add event memory: {e}")
    
    def add_marketing_template(
        self,
        template_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add marketing template to vector store
        
        Args:
            template_name: Template identifier
            content: Template content
            metadata: Additional metadata
        """
        try:
            metadata = metadata or {}
            metadata["template_name"] = template_name
            metadata["type"] = "marketing_template"
            
            self.vectorstore.add_texts(
                texts=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Added marketing template: {template_name}")
            
        except Exception as e:
            logger.error(f"Failed to add marketing template: {e}")
    
    def add_user_preference(
        self,
        user_id: str,
        preference_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add user preference to vector store
        
        Args:
            user_id: User identifier
            preference_type: Type of preference
            content: Preference content
            metadata: Additional metadata
        """
        try:
            metadata = metadata or {}
            metadata["user_id"] = user_id
            metadata["preference_type"] = preference_type
            metadata["type"] = "user_preference"
            
            self.vectorstore.add_texts(
                texts=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Added user preference for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to add user preference: {e}")
    
    def search_similar(
        self,
        query: str,
        filter_metadata: Optional[Dict[str, Any]] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content in vector store
        
        Args:
            query: Search query
            filter_metadata: Metadata filters
            k: Number of results to return
            
        Returns:
            List of similar documents with metadata
        """
        try:
            # Perform similarity search
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_metadata
            )
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                })
            
            logger.info(f"Found {len(formatted_results)} similar documents")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return []
    
    def get_event_context(
        self,
        event_id: str,
        query: Optional[str] = None,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get relevant context for an event
        
        Args:
            event_id: Event identifier
            query: Optional specific query
            k: Number of results
            
        Returns:
            List of relevant context documents
        """
        filter_metadata = {"event_id": event_id, "type": "event_memory"}
        
        if query:
            return self.search_similar(
                query=query,
                filter_metadata=filter_metadata,
                k=k
            )
        else:
            # Return recent event memories
            try:
                results = self.vectorstore.get(
                    where=filter_metadata,
                    limit=k
                )
                return results if results else []
            except Exception as e:
                logger.error(f"Failed to get event context: {e}")
                return []
    
    def get_marketing_examples(
        self,
        event_type: Optional[str] = None,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get marketing template examples
        
        Args:
            event_type: Optional event type filter
            k: Number of examples
            
        Returns:
            List of marketing examples
        """
        filter_metadata = {"type": "marketing_template"}
        if event_type:
            filter_metadata["event_type"] = event_type
        
        query = f"marketing content for {event_type}" if event_type else "marketing content"
        
        return self.search_similar(
            query=query,
            filter_metadata=filter_metadata,
            k=k
        )
    
    def get_user_preferences(
        self,
        user_id: str,
        preference_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            preference_type: Optional preference type filter
            
        Returns:
            List of user preferences
        """
        filter_metadata = {
            "user_id": user_id,
            "type": "user_preference"
        }
        
        if preference_type:
            filter_metadata["preference_type"] = preference_type
        
        try:
            results = self.vectorstore.get(where=filter_metadata)
            return results if results else []
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return []
    
    def delete_event_memories(self, event_id: str) -> None:
        """
        Delete all memories for an event
        
        Args:
            event_id: Event identifier
        """
        try:
            self.vectorstore.delete(
                where={"event_id": event_id}
            )
            logger.info(f"Deleted memories for event {event_id}")
        except Exception as e:
            logger.error(f"Failed to delete event memories: {e}")


# Create singleton instance
vector_store = VectorStore()