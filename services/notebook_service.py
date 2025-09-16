"""Notebook service for the PCS-HELIO MCP API."""

from pathlib import Path
from typing import List, Optional

from api.config import settings
from api.logging import get_logger

logger = get_logger("notebook_service")


class NotebookService:
    """Service for handling Jupyter notebook operations."""

    def __init__(self):
        """Initialize the notebook service."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service."""
        if self._initialized:
            return

        try:
            logger.info(
                "Notebook service initialized", path=str(settings.notebooks_path)
            )
            self._initialized = True

        except Exception as e:
            logger.error("Failed to initialize notebook service", error=str(e))
            raise

    async def list_notebooks(self) -> List[dict]:
        """List available notebooks."""
        if not self._initialized:
            await self.initialize()

        notebooks = []
        try:
            for notebook_path in settings.notebooks_path.glob("**/*.ipynb"):
                if notebook_path.is_file():
                    notebook_info = {
                        "name": notebook_path.stem,
                        "filename": notebook_path.name,
                        "path": str(notebook_path.relative_to(settings.notebooks_path)),
                        "size_bytes": notebook_path.stat().st_size,
                        "modified": notebook_path.stat().st_mtime,
                    }
                    notebooks.append(notebook_info)

            logger.debug("Listed notebooks", count=len(notebooks))
            return notebooks

        except Exception as e:
            logger.error("Error listing notebooks", error=str(e))
            raise

    async def health_check(self):
        """Check service health."""
        return {"notebook_service": "ready"}


# Global notebook service instance
notebook_service = NotebookService()
