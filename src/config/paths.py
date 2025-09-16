"""
Configuration paths resolver for PCS-Meta-Repo v4.4
Handles @data_root.* substitutions and path resolution
"""

from pathlib import Path
from typing import Any, Dict, Union

import yaml


class PathsConfig:
    """Resolve configuration paths with substitutions."""

    def __init__(self, config_dir: Union[str, Path, None] = None):
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_dir = Path(config_dir)
        self._data_root = None
        self._paths = None

    @property
    def data_root(self) -> Dict[str, str]:
        """Load and cache data_root configuration."""
        if self._data_root is None:
            with open(self.config_dir / "data_root.yaml") as f:
                self._data_root = yaml.safe_load(f)
            # Inject canonical defaults if missing (centralized)
            # These are repo-relative fallbacks ensuring pipeline keys exist
            canonical_defaults = {
                "L1_tidy": "data/L1_tidy",
                "L2_derived": "data/L2_derived",
                "processed": "data/processed",
                "reports": "reports",
            }
            for k, v in canonical_defaults.items():
                if k not in self._data_root:
                    self._data_root[k] = v
        return self._data_root

    def resolve_path(self, path_template: str) -> str:
        """Resolve @data_root.* references in path templates."""
        if not path_template.startswith("@data_root."):
            return path_template

        # Extract the key after @data_root.
        key = path_template.replace("@data_root.", "")
        base_key = key.split("/")[0]  # Get first part for lookup

        if base_key in self.data_root:
            base_path = self.data_root[base_key]
            # Handle nested paths like @data_root.raw_public/swow
            if "/" in key:
                suffix = "/".join(key.split("/")[1:])
                return f"{base_path}/{suffix}"
            return base_path

        # Handle legacy layout references
        if (
            "layout" in self.data_root
            and isinstance(self.data_root["layout"], dict)
            and base_key in self.data_root["layout"]
        ):
            base_path = self.data_root["layout"][base_key]  # type: ignore[index]
            if "/" in key:
                suffix = "/".join(key.split("/")[1:])
                return f"{base_path}/{suffix}"
            return base_path

        raise ValueError(f"Unknown data_root key: {base_key}")

    def ensure_dir(self, path: str) -> Path:
        """Ensure directory exists and return Path object."""
        resolved_path = Path(self.resolve_path(path))
        resolved_path.mkdir(parents=True, exist_ok=True)
        return resolved_path

    def get_dataset_paths(self, dataset_name: str) -> Dict[str, str]:
        """Get resolved paths for a specific dataset."""
        datasets_file = self.config_dir / "datasets.yaml"
        with open(datasets_file) as f:
            config = yaml.safe_load(f)

        # Look in different sections
        for section in ["swow", "datasets_rt", "datasets_eeg"]:
            if section in config:
                if section == "swow" and dataset_name == "swow":
                    dataset_config = config[section]
                elif section in ["datasets_rt", "datasets_eeg"]:
                    if dataset_name in config[section]:
                        dataset_config = config[section][dataset_name]
                    else:
                        continue
                else:
                    continue

                # Resolve all path fields
                resolved: Dict[str, Any] = {}
                for key, value in dataset_config.items():
                    if key.endswith("_dir") and isinstance(value, str):
                        resolved[key] = self.resolve_path(value)
                    else:
                        resolved[key] = value

                return resolved

        raise ValueError(f"Dataset {dataset_name} not found in configuration")

    def get_canonical_paths(self) -> Dict[str, str]:
        """Return canonical root paths (L1_tidy, L2_derived, processed, reports)."""
        dr = self.data_root
        required = ["L1_tidy", "L2_derived", "processed", "reports"]
        result: Dict[str, str] = {}
        for k in required:
            v = dr.get(k)
            if not isinstance(v, str):  # enforce non-None string
                raise ValueError(f"Canonical path key '{k}' missing or not a string")
            result[k] = v
        return result


# Singleton instance
paths_config = PathsConfig()


def get_paths() -> PathsConfig:
    """Get global paths configuration instance."""
    return paths_config


def resolve_path(path_template: str) -> str:
    """Convenience function to resolve a single path."""
    return paths_config.resolve_path(path_template)


def ensure_dir(path: str) -> Path:
    """Convenience function to ensure directory exists."""
    return paths_config.ensure_dir(path)
