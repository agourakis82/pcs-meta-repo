"""
Path configuration for DX-CODEX pipeline.
Loads paths from config/paths.yaml and provides convenient access.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_paths():
    """Load data_root and datasets configs with @data_root.* substitution."""
    try:
        dr = yaml.safe_load(Path("config/data_root.yaml").read_text())
        ds = yaml.safe_load(Path("config/datasets.yaml").read_text())
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file not found: {e}")
    
    layout = dr["layout"].copy()
    data_root = dr["data_root"]
    
    def _sub(v: str) -> str:
        if isinstance(v, str) and v.startswith("@data_root."):
            key = v.split(".",1)[1]
            if key in layout:
                return layout[key].format(data_root=data_root)
            else:
                # Handle paths like "raw_external/geco" by combining with data_root
                return f"{data_root}/{key}"
        return v
    
    for k,v in ds.items():
        if isinstance(v, dict):
            for fld in ("raw_dir","processed_dir"):
                if fld in v: 
                    ds[k][fld] = _sub(v[fld])
    return dr, ds


def get_paths() -> Dict[str, str]:
    """
    Load and return paths configuration.
    
    Returns:
        Dictionary with path configurations
    """
    config_path = Path(__file__).parent / "paths.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Paths config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Flatten the configuration and resolve relative paths
    paths = {}
    
    # Data paths
    if 'data' in config:
        for key, value in config['data'].items():
            paths[key] = value
            # Also create full path keys
            paths[f"{key}_data"] = value
    
    # Set specific keys expected by the pipeline
    paths['raw_data'] = config['data']['raw_zuco'].replace('data/raw_public/zuco', 'scripts/data/raw_public/zuco')
    paths['processed_data'] = config['data']['processed']
    paths['figures'] = config['data']['figures']
    paths['reports'] = config['data']['reports']
    
    # Language-specific paths
    if 'languages' in config:
        paths['languages'] = config['languages']
    
    # Model paths
    if 'models' in config:
        paths['models'] = config['models']
    
    return paths


def get_data_paths() -> Dict[str, str]:
    """Get only data-related paths."""
    all_paths = get_paths()
    return {k: v for k, v in all_paths.items() if 'data' in k or k in ['raw_data', 'processed_data', 'figures', 'reports']}


def get_zuco_path(version: str = "v1") -> str:
    """
    Get path to ZuCo data for specific version.
    
    Args:
        version: "v1" or "v2"
        
    Returns:
        Path to ZuCo data directory
    """
    paths = get_paths()
    base_path = paths['raw_data']
    return f"{base_path}/{version}"


if __name__ == "__main__":
    # Test the paths
    paths = get_paths()
    print("Available paths:")
    for key, value in paths.items():
        print(f"  {key}: {value}")
