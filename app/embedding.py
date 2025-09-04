"""
Embedding module for the GenAI SMS Chatbot.

This module handles the generation of vector embeddings for job-related
information and stores them in a Chroma vector database.
"""

import os
import logging
import glob
from typing import List, Dict, Any, Optional
import openai

from pathlib import Path


from config.project_config import BaseConfigurable


class EmbeddingManager(BaseConfigurable):
    """
    Manages the generation and storage of embeddings for job-related information.
    """
    
    def __init__(self, persist_directory: str = "./data/chroma_db", data_directory: str = "./data"):
        """
        Initialize the embedding manager.
        
        Args:
            persist_directory: Directory to persist the vector database
            data_directory: Directory containing job description PDFs
        """
        super().__init__()
        self.persist_directory = persist_directory
        self.data_directory = data_directory
        
        # Initialize OpenAI embeddings and ChromaDB
        try:
            api_key = self.config.get_api_key()
            if not api_key:
                raise ValueError("OpenAI API key not found in environment")
            
            # Initialize ChromaDB directly
            import chromadb
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Create or get collection
            try:
                self.collection = self.client.get_collection("job_descriptions")
            except:
                self.collection = self.client.create_collection("job_descriptions")
            
            # Initialize OpenAI embeddings
            self.openai_client = openai.OpenAI(api_key=api_key)
            
            self.logger.info("Embedding manager initialized with OpenAI embeddings and ChromaDB")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings: {e}")
            self.client = None
            self.collection = None
            self.openai_client = None
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        if not self.openai_client:
            return []
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Error getting embedding: {e}")
            return []
    
    def find_job_description_pdfs(self) -> List[str]:
        """Find all PDF job description files in the data directory."""
        try:
            pdf_files = glob.glob(os.path.join(self.data_directory, "*.pdf"))
            self.logger.info(f"Found {len(pdf_files)} PDF files")
            return pdf_files
        except Exception as e:
            self.logger.error(f"Error finding PDFs: {e}")
            return []
    
    def extract_position_info_from_filename(self, pdf_path: str) -> Dict[str, str]:
        """Extract position information from PDF filename."""
        filename = os.path.basename(pdf_path).lower()
        
        # Simple position mapping
        position_mapping = {
            'python': 'Python Developer',
            'java': 'Java Developer', 
            'frontend': 'Frontend Developer',
            'backend': 'Backend Developer',
            'fullstack': 'Full Stack Developer',
            'data scientist': 'Data Scientist',
            'data engineer': 'Data Engineer',
            'devops': 'DevOps Engineer',
            'qa': 'QA Engineer',
            'product manager': 'Product Manager',
            'project manager': 'Project Manager'
        }
        
        title = 'Unknown Position'
        for keyword, pos_title in position_mapping.items():
            if keyword in filename:
                title = pos_title
                break
        
        return {
            'title': title,
            'company': 'TechCorp Solutions',
            'location': 'Remote/Hybrid',
            'type': 'Full-time'
        }
    
    def process_pdf_document(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Process a PDF document and extract text."""
        try:
            # Read PDF content
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception:
                # Fallback to text file
                with open(pdf_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            
            # Extract position info
            position_info = self.extract_position_info_from_filename(pdf_path)
            
            # Create document
            doc = {
                'content': text,
                'metadata': {
                    'source': 'pdf_job_description',
                    'file': os.path.basename(pdf_path),
                    'position_title': position_info['title'],
                    'company': position_info['company'],
                    'location': position_info['location'],
                    'type': position_info['type']
                }
            }
            
            self.logger.info(f"Processed PDF: {position_info['title']}")
            return [doc]
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            return []
    
    def create_generic_job_information_documents(self) -> List[Dict[str, Any]]:
        """Create generic job information documents."""
        generic_docs = [
            {
                'content': """General Benefits and Perks:
1. Competitive salary based on experience
2. Comprehensive health, dental, and vision insurance
3. 401(k) with company matching
4. Flexible work hours and remote work options
5. Professional development budget
6. Unlimited PTO and paid holidays
7. Stock options and equity participation
8. Modern tech stack and development tools""",
                'metadata': {
                    'category': 'benefits',
                    'source': 'generic_job_information',
                    'position_title': 'All Positions',
                    'company': 'TechCorp Solutions',
                    'location': 'Various',
                    'type': 'Full-time'
                }
            },
            {
                'content': """General Interview Process:
1. Initial screening call with HR (30 minutes)
2. Technical assessment - take-home coding project (1-2 days)
3. Technical interview with senior team members (1 hour)
4. System design and architecture discussion (1 hour)
5. Final interview with hiring manager (45 minutes)
6. Reference checks and background verification
7. Offer discussion and negotiation""",
                'metadata': {
                    'category': 'interview_process',
                    'source': 'generic_job_information',
                    'position_title': 'All Positions',
                    'company': 'TechCorp Solutions',
                    'location': 'Various',
                    'type': 'Full-time'
                }
            },
            {
                'content': """General Company Information:
Fast-growing technology company focused on innovation. Collaborative, remote-first culture with emphasis on work-life balance. Team members have autonomy to make technical decisions. Values continuous learning, open communication, and innovation. Emphasis on delivering high-quality, scalable solutions. Diverse and inclusive workplace environment.""",
                'metadata': {
                    'category': 'company_info',
                    'source': 'generic_job_information',
                    'position_title': 'All Positions',
                    'company': 'TechCorp Solutions',
                    'location': 'Various',
                    'type': 'Full-time'
                }
            }
        ]
        
        self.logger.info(f"Created {len(generic_docs)} generic job information documents")
        return generic_docs
    
    def add_documents_to_vectorstore(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store."""
        if not self.collection or not documents:
            return
        
        try:
            ids = []
            texts = []
            metadatas = []
            
            for i, doc in enumerate(documents):
                # Get embedding
                embedding = self.get_embedding(doc['content'])
                if not embedding:
                    continue
                
                # Prepare data for ChromaDB
                doc_id = f"doc_{i}_{hash(doc['content']) % 10000}"
                ids.append(doc_id)
                texts.append(doc['content'])
                metadatas.append(doc['metadata'])
            
            # Add to ChromaDB
            if ids:
                self.collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
                self.logger.info(f"Added {len(ids)} documents to vector store")
            
        except Exception as e:
            self.logger.error(f"Error adding documents to vector store: {e}")
    
    def search_similar_documents(self, query: str, n_results: int = 3, position_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity."""
        if not self.collection:
            return []
        
        try:
            # Search ChromaDB without filtering first
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 2  # Get more results to filter from
            )
            
            # Convert to our format and apply position filter if needed
            documents = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                    
                    # Apply position filter if specified
                    if position_filter:
                        position_title = metadata.get('position_title', '').lower()
                        if position_filter.lower() not in position_title:
                            continue
                    
                    documents.append({
                        'content': doc,
                        'metadata': metadata,
                        'score': 1.0  # ChromaDB doesn't return scores in this query mode
                    })
                    
                    # Stop if we have enough results
                    if len(documents) >= n_results:
                        break
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching vector store: {e}")
            return []
    
    def get_available_positions(self) -> List[Dict[str, str]]:
        """Get list of available positions from the vector store."""
        if not self.collection:
            return []
        
        try:
            # Get all documents to extract unique positions
            results = self.collection.get()
            positions = {}
            
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata:
                        position_title = metadata.get('position_title', 'Unknown')
                        if position_title not in positions:
                            positions[position_title] = {
                                'title': position_title,
                                'company': metadata.get('company', 'Unknown'),
                                'location': metadata.get('location', 'Unknown'),
                                'type': metadata.get('type', 'Unknown'),
                                'source': metadata.get('source', 'Unknown')
                            }
            
            return list(positions.values())
            
        except Exception as e:
            self.logger.error(f"Error getting available positions: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        if not self.collection:
            return {}
        
        try:
            results = self.collection.get()
            total_docs = len(results['documents']) if results['documents'] else 0
            
            # Count positions
            positions = {}
            if results['metadatas']:
                for metadata in results['metadatas']:
                    if metadata:
                        position = metadata.get('position_title', 'Unknown')
                        positions[position] = positions.get(position, 0) + 1
            
            return {
                'total_documents': total_docs,
                'positions': positions,
                'persist_directory': self.persist_directory
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def clear_vectorstore(self) -> None:
        """Clear all documents from the vector store."""
        if not self.client:
            return
        
        try:
            self.client.delete_collection("job_descriptions")
            self.collection = self.client.create_collection("job_descriptions")
            self.logger.info("Vector store cleared")
        except Exception as e:
            self.logger.error(f"Error clearing vector store: {e}")
    
    def run_embedding_pipeline(self, pdf_path: Optional[str] = None) -> None:
        """Run the complete embedding pipeline."""
        if not self.collection or not self.openai_client:
            self.logger.error("Embeddings or vector store not initialized")
            return
        
        try:
            documents = []
            
            # Process specific PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                pdf_documents = self.process_pdf_document(pdf_path)
                documents.extend(pdf_documents)
            else:
                # Find and process all job description PDFs
                pdf_files = self.find_job_description_pdfs()
                for pdf_file in pdf_files:
                    pdf_documents = self.process_pdf_document(pdf_file)
                    documents.extend(pdf_documents)
            
            # Create generic job information documents
            generic_documents = self.create_generic_job_information_documents()
            documents.extend(generic_documents)
            
            if not documents:
                self.logger.error("No documents to process")
                return
            
            # Add documents to vector store
            self.add_documents_to_vectorstore(documents)
            
            # Display basic stats
            stats = self.get_collection_stats()
            self.logger.info(f"Pipeline complete: {stats.get('total_documents', 0)} documents processed")
            
        except Exception as e:
            self.logger.error(f"Error in embedding pipeline: {e}")


def main():
    """Main function for running the embedding pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run embedding pipeline")
    parser.add_argument("--pdf", help="Path to specific PDF file to process")
    parser.add_argument("--persist-dir", default="./data/chroma_db", help="Vector store persist directory")
    parser.add_argument("--data-dir", default="./data", help="Data directory containing job description PDFs")
    parser.add_argument("--clear", action="store_true", help="Clear existing vector store")
    
    args = parser.parse_args()
    
    # Initialize embedding manager
    embedding_manager = EmbeddingManager(args.persist_dir, args.data_dir)
    
    # Clear vector store if requested
    if args.clear:
        embedding_manager.clear_vectorstore()
    
    # Run pipeline
    embedding_manager.run_embedding_pipeline(args.pdf)


if __name__ == "__main__":
    main() 