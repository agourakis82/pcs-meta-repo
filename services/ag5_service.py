"""AG5 data service for the PCS-HELIO MCP API."""

from typing import List, Optional

import pandas as pd

from api.config import settings
from api.logging import get_logger
from api.models import KECItem

logger = get_logger("ag5_service")


class AG5DataError(Exception):
    """Exception raised when AG5 data operations fail."""

    pass


class AG5Service:
    """Service for handling AG5 (Agroscope) data operations."""

    def __init__(self):
        """Initialize the AG5 service."""
        self._data_cache = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the service and validate data paths."""
        if self._initialized:
            return

        try:
            # Check if AG5 data path exists
            if not settings.ag5_data_path.exists():
                logger.warning(
                    "AG5 data path does not exist", path=str(settings.ag5_data_path)
                )
            else:
                logger.info("AG5 service initialized", path=str(settings.ag5_data_path))

            self._initialized = True

        except Exception as e:
            logger.error("Failed to initialize AG5 service", error=str(e))
            raise AG5DataError(f"AG5 service initialization failed: {e}")

    async def list_datasets(self) -> List[dict]:
        """
        List available AG5 datasets.

        Returns:
            List of dataset metadata dictionaries
        """
        if not self._initialized:
            await self.initialize()

        datasets = []

        try:
            # Look for data files in the AG5 data path
            for file_path in settings.ag5_data_path.glob("**/*"):
                if file_path.is_file() and file_path.suffix.lower() in [
                    ".csv",
                    ".parquet",
                    ".json",
                ]:
                    dataset_info = {
                        "name": file_path.stem,
                        "filename": file_path.name,
                        "path": str(file_path.relative_to(settings.ag5_data_path)),
                        "size_bytes": file_path.stat().st_size,
                        "format": file_path.suffix.lower().lstrip("."),
                        "modified": file_path.stat().st_mtime,
                    }
                    datasets.append(dataset_info)

            logger.debug("Listed AG5 datasets", count=len(datasets))
            return datasets

        except Exception as e:
            logger.error("Error listing AG5 datasets", error=str(e))
            raise AG5DataError(f"Failed to list datasets: {e}")

    async def load_dataset(
        self, dataset_name: str, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Load an AG5 dataset.

        Args:
            dataset_name: Name of the dataset to load
            limit: Optional limit on number of rows to return

        Returns:
            Pandas DataFrame with the dataset
        """
        if not self._initialized:
            await self.initialize()

        try:
            # Find the dataset file
            dataset_path = None
            for file_path in settings.ag5_data_path.glob("**/*"):
                if file_path.stem == dataset_name and file_path.is_file():
                    dataset_path = file_path
                    break

            if not dataset_path:
                raise AG5DataError(f"Dataset '{dataset_name}' not found")

            # Load based on file format
            if dataset_path.suffix.lower() == ".csv":
                df = pd.read_csv(dataset_path)
            elif dataset_path.suffix.lower() == ".parquet":
                df = pd.read_parquet(dataset_path)
            elif dataset_path.suffix.lower() == ".json":
                df = pd.read_json(dataset_path)
            else:
                raise AG5DataError(f"Unsupported file format: {dataset_path.suffix}")

            # Apply limit if specified
            if limit and limit > 0:
                df = df.head(limit)

            logger.info(
                "Loaded AG5 dataset",
                dataset=dataset_name,
                rows=len(df),
                columns=len(df.columns),
            )

            return df

        except Exception as e:
            logger.error(
                "Error loading AG5 dataset", dataset=dataset_name, error=str(e)
            )
            raise AG5DataError(f"Failed to load dataset '{dataset_name}': {e}")

    async def get_dataset_info(self, dataset_name: str) -> dict:
        """
        Get information about a specific AG5 dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dictionary with dataset information
        """
        if not self._initialized:
            await self.initialize()

        try:
            df = await self.load_dataset(dataset_name, limit=1000)  # Sample for info

            info = {
                "name": dataset_name,
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "sample_data": df.head(5).to_dict("records") if len(df) > 0 else [],
            }

            # Add summary statistics for numeric columns
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                info["summary_stats"] = df[numeric_cols].describe().to_dict()

            return info

        except Exception as e:
            logger.error(
                "Error getting AG5 dataset info", dataset=dataset_name, error=str(e)
            )
            raise AG5DataError(f"Failed to get info for dataset '{dataset_name}': {e}")

    async def search_datasets(self, query: str) -> List[dict]:
        """
        Search for datasets matching a query.

        Args:
            query: Search query string

        Returns:
            List of matching dataset metadata
        """
        if not self._initialized:
            await self.initialize()

        try:
            all_datasets = await self.list_datasets()

            # Simple text-based search
            query_lower = query.lower()
            matching_datasets = []

            for dataset in all_datasets:
                if (
                    query_lower in dataset["name"].lower()
                    or query_lower in dataset["filename"].lower()
                ):
                    matching_datasets.append(dataset)

            logger.debug(
                "Search AG5 datasets", query=query, matches=len(matching_datasets)
            )
            return matching_datasets

        except Exception as e:
            logger.error("Error searching AG5 datasets", query=query, error=str(e))
            raise AG5DataError(f"Failed to search datasets: {e}")

    async def health_check(self):
        """
        Check the health of the AG5 service.

        Returns:
            Dictionary with health status
        """
        health_status = {
            "ag5_service": "unknown",
            "data_path": "unknown",
            "datasets_available": 0,
        }

        try:
            if not self._initialized:
                await self.initialize()

            # Check data path accessibility
            if settings.ag5_data_path.exists() and settings.ag5_data_path.is_dir():
                health_status["data_path"] = "accessible"
            else:
                health_status["data_path"] = "not_found"

            # Count available datasets
            datasets = await self.list_datasets()
            health_status["datasets_available"] = len(datasets)

            health_status["ag5_service"] = "ready"

        except Exception as e:
            logger.error("AG5 service health check failed", error=str(e))
            health_status["ag5_service"] = "error"

        return health_status


# Global AG5 service instance
ag5_service = AG5Service()
