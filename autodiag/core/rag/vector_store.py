"""Local persistent vector store manager for multi-project diagnostic collections."""

import os
from typing import List, Optional
from autodiag.api.schemas import CitationResult, DiagnosticDatabase


class VectorStoreManager:
    """Manages project-isolated vector collections."""

    def __init__(self, storage_dir: str = ".autodiag_vector_store"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.active_collection = "default_ecu"

    def index_database(self, db: DiagnosticDatabase, collection_name: Optional[str] = None):
        """Index database into local collection."""
        self.active_collection = collection_name or db.ecu_name
        # Fallback local in-memory index
        pass
