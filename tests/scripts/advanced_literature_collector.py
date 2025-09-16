"""
Shim to make tests import the real collector from repository scripts/.
The test suite expects advanced_literature_collector.py under tests/scripts.
"""

import os
import importlib.util

REPO_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
TARGET = os.path.join(REPO_SCRIPTS, "advanced_literature_collector.py")

spec = importlib.util.spec_from_file_location("repo_adv_lit_collector", TARGET)
if spec is None or spec.loader is None:
    raise ImportError("Cannot load advanced_literature_collector from scripts/")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

AdvancedLiteratureCollector = getattr(module, "AdvancedLiteratureCollector")
Paper = getattr(module, "Paper")

__all__ = ["AdvancedLiteratureCollector", "Paper"]
