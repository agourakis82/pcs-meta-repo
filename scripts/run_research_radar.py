#!/usr/bin/env python3
"""
Run the continuous research radar once (intended for scheduling/cron).

Usage:
  python -m scripts.run_research_radar --config config/research_radar.yaml
"""

import argparse
import logging
import sys

from services.research_radar import update_knowledge_base_from_feeds


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run research radar update")
    parser.add_argument(
        "--config",
        default="config/research_radar.yaml",
        help="Path to radar YAML configuration",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    stats = update_knowledge_base_from_feeds(args.config)
    print(f"Radar update complete. Added: {stats['added']} Skipped: {stats['skipped']}")


if __name__ == "__main__":
    sys.exit(main())

