"""Configuration loader for OpenMun eCH library.

This module provides configuration loading from:
1. Environment variables (highest priority)
2. config.yaml file (if present)
3. No defaults - returns None if not configured

This prevents hardcoded paths from leaking into version control.
"""

import os
from pathlib import Path
from typing import List, Optional


def get_production_data_paths() -> List[Path]:
    """Get production data paths from config or environment.

    Priority:
    1. Environment variable OPENMUN_PRODUCTION_DATA (comma-separated paths)
    2. config.yaml file in project root
    3. Returns empty list if not configured

    Returns:
        List of Path objects to production data directories (only existing paths)

    Environment Variable:
        OPENMUN_PRODUCTION_DATA: Single path or comma-separated list of paths
            Example: /path/to/sedex/data
            Example: /path/one,/path/two,/path/three

    Config File:
        config.yaml in project root with structure:
            production_data_paths:
              - /path/to/sedex/data/processed
              - /path/to/another/location
    """
    paths = []

    # Priority 1: Environment variable
    env_paths = os.getenv("OPENMUN_PRODUCTION_DATA")
    if env_paths:
        # Support comma-separated list
        for path_str in env_paths.split(','):
            path_str = path_str.strip()
            if path_str:
                path = Path(path_str)
                if path.exists() and path.is_dir():
                    paths.append(path)

    # Priority 2: config.yaml file
    if not paths:
        # Search for config.yaml in multiple locations:
        # 1. Current working directory (where user runs commands)
        # 2. Project root (for src/ layout: 3 levels up from this file)
        search_paths = [
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",  # Project root for src/ layout
        ]

        config_file = None
        for candidate in search_paths:
            if candidate.exists():
                config_file = candidate
                break

        if config_file:
            try:
                import yaml
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)

                if config and 'production_data_paths' in config:
                    for path_str in config['production_data_paths']:
                        path = Path(path_str)
                        if path.exists() and path.is_dir():
                            paths.append(path)

            except ImportError:
                # PyYAML not installed - skip config file
                pass
            except Exception:
                # Invalid YAML or other error - skip config file
                pass

    return paths


def get_primary_production_data_path() -> Optional[Path]:
    """Get the primary (first) production data path.

    This is a convenience function for code that expects a single path.

    Returns:
        First configured production data path, or None if not configured
    """
    paths = get_production_data_paths()
    return paths[0] if paths else None
