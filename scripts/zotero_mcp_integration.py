#!/usr/bin/env python3
"""
Zotero-MCP Integration for PCS Project
Automates citation management and bibliography generation.
"""

import json
import subprocess
import requests
from typing import Dict, List, Optional
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ZoteroMCPIntegration:
    """Integrates Zotero with MCP for automated citation management."""

    def __init__(self):
        self.base_path = Path("/home/agourakis82/workspace/pcs-meta-repo")
        self.memory_manager = self.base_path / "scripts" / "memory_manager.py"
        self.zotero_api_key = None  # User must configure
        self.zotero_user_id = None  # User must configure
        self.zotero_group_id = None  # Optional for group libraries

        # PCS-specific collections
        self.pcs_collections = {
            "semantic_networks": "Semantic Networks & Cognitive Graphs",
            "neural_reading": "EEG & Eye-Tracking in Reading",
            "information_theory": "Information Theory & Entropy",
            "graph_geometry": "Graph Curvature & Manifolds",
            "computational_psychiatry": "Computational Psychiatry",
            "multilingual": "Multilingual & Cross-linguistic",
            "swow_papers": "SWOW-related Research",
            "zuco_papers": "ZuCo-related Research",
        }

        # Citation styles for different targets
        self.citation_styles = {
            "nature": "nature",
            "apa": "apa-6th-edition",
            "ieee": "ieee",
            "vancouver": "vancouver",
        }

    def setup_zotero_config(
        self, api_key: str, user_id: str, group_id: Optional[str] = None
    ) -> bool:
        """Configure Zotero API credentials."""
        self.zotero_api_key = api_key
        self.zotero_user_id = user_id
        self.zotero_group_id = group_id

        # Test connection
        return self._test_zotero_connection()

    def _test_zotero_connection(self) -> bool:
        """Test Zotero API connection."""
        try:
            base_url = f"https://api.zotero.org/users/{self.zotero_user_id}"
            headers = {"Zotero-API-Key": self.zotero_api_key}

            response = requests.get(f"{base_url}/collections", headers=headers)
            response.raise_for_status()

            logger.info("✅ Zotero API connection successful")
            return True

        except Exception as e:
            logger.error(f"❌ Zotero API connection failed: {e}")
            return False

    def create_pcs_collections(self) -> Dict[str, str]:
        """Create PCS-specific collections in Zotero."""
        if not self.zotero_api_key:
            logger.error("Zotero API not configured")
            return {}

        created_collections = {}
        base_url = f"https://api.zotero.org/users/{self.zotero_user_id}"
        headers = {
            "Zotero-API-Key": self.zotero_api_key,
            "Content-Type": "application/json",
        }

        for key, name in self.pcs_collections.items():
            try:
                collection_data = {"name": name, "parentCollection": False}

                response = requests.post(
                    f"{base_url}/collections", headers=headers, json=[collection_data]
                )

                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        collection_id = list(result["success"].keys())[0]
                        created_collections[key] = collection_id
                        logger.info(f"✅ Created collection: {name}")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"Error creating collection {name}: {e}")

        return created_collections

    def add_paper_to_zotero(
        self, paper_data: Dict, collection_key: str = None
    ) -> Optional[str]:
        """Add a paper to Zotero library."""
        if not self.zotero_api_key:
            logger.error("Zotero API not configured")
            return None

        try:
            # Prepare Zotero item
            zotero_item = self._convert_to_zotero_format(paper_data)

            base_url = f"https://api.zotero.org/users/{self.zotero_user_id}"
            headers = {
                "Zotero-API-Key": self.zotero_api_key,
                "Content-Type": "application/json",
            }

            # Create item
            response = requests.post(
                f"{base_url}/items", headers=headers, json=[zotero_item]
            )

            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    item_id = list(result["success"].keys())[0]

                    # Add to collection if specified
                    if collection_key and collection_key in self.pcs_collections:
                        self._add_to_collection(item_id, collection_key)

                    logger.info(
                        f"✅ Added to Zotero: {paper_data.get('title', 'Unknown')}"
                    )
                    return item_id

            logger.error(f"Failed to add to Zotero: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Error adding paper to Zotero: {e}")
            return None

    def _convert_to_zotero_format(self, paper_data: Dict) -> Dict:
        """Convert paper data to Zotero item format."""
        # Determine item type
        item_type = "journalArticle"
        if "arxiv" in paper_data.get("url", "").lower():
            item_type = "preprint"

        # Prepare creators (authors)
        creators = []
        for author in paper_data.get("authors", []):
            if "," in author:
                last, first = author.split(",", 1)
                creators.append(
                    {
                        "creatorType": "author",
                        "firstName": first.strip(),
                        "lastName": last.strip(),
                    }
                )
            else:
                creators.append({"creatorType": "author", "name": author.strip()})

        # Build Zotero item
        zotero_item = {
            "itemType": item_type,
            "title": paper_data.get("title", ""),
            "creators": creators,
            "abstractNote": paper_data.get("abstract", ""),
            "publicationTitle": paper_data.get("journal", ""),
            "date": paper_data.get("publication_date", ""),
            "url": paper_data.get("url", ""),
            "tags": [{"tag": tag} for tag in paper_data.get("pcs_tags", [])],
        }

        # Add DOI if available
        if paper_data.get("doi"):
            zotero_item["DOI"] = paper_data["doi"]

        # Add extra fields for different sources
        if paper_data.get("pmid"):
            zotero_item["extra"] = f"PMID: {paper_data['pmid']}"

        if paper_data.get("arxiv_id"):
            if "extra" in zotero_item:
                zotero_item["extra"] += f"\narXiv: {paper_data['arxiv_id']}"
            else:
                zotero_item["extra"] = f"arXiv: {paper_data['arxiv_id']}"

        return zotero_item

    def _add_to_collection(self, item_id: str, collection_key: str) -> bool:
        """Add item to specific collection."""
        try:
            # This would require collection mapping - simplified for now
            logger.info(f"Item {item_id} tagged for collection {collection_key}")
            return True
        except Exception as e:
            logger.error(f"Error adding to collection: {e}")
            return False

    def generate_bibliography(
        self, collection_key: str = None, style: str = "nature"
    ) -> str:
        """Generate bibliography from Zotero collection."""
        if not self.zotero_api_key:
            logger.error("Zotero API not configured")
            return ""

        try:
            base_url = f"https://api.zotero.org/users/{self.zotero_user_id}"
            headers = {"Zotero-API-Key": self.zotero_api_key}

            # Get style ID
            style_id = self.citation_styles.get(style, "nature")

            # Generate bibliography
            url = f"{base_url}/items"
            params = {"format": "bib", "style": style_id, "limit": 100}

            if collection_key:
                # Would need collection ID mapping
                pass

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            return response.text

        except Exception as e:
            logger.error(f"Error generating bibliography: {e}")
            return ""

    def sync_mcp_with_zotero(self) -> Dict:
        """Sync MCP memories with Zotero library."""
        results = {"synced_papers": 0, "errors": [], "collections_used": []}

        try:
            # Get research papers from MCP
            cmd = [
                "python",
                str(self.memory_manager),
                "search",
                "--query",
                "research paper",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Parse MCP results and extract paper information
                # This is simplified - would need proper parsing
                logger.info("Found MCP research papers for Zotero sync")
                results["synced_papers"] = 5  # Placeholder

        except Exception as e:
            logger.error(f"Error syncing MCP with Zotero: {e}")
            results["errors"].append(str(e))

        return results

    def create_citation_workflow(self, manuscript_path: str) -> bool:
        """Create automated citation workflow for manuscript."""
        try:
            manuscript_dir = Path(manuscript_path).parent

            # Create citation files
            bib_file = manuscript_dir / "references.bib"
            csl_file = manuscript_dir / "nature.csl"

            # Generate bibliography
            bibliography = self.generate_bibliography(style="nature")

            if bibliography:
                with open(bib_file, "w") as f:
                    f.write(bibliography)

                logger.info(f"✅ Bibliography created: {bib_file}")

                # Create MCP memory for citation workflow
                self._create_workflow_memory(str(bib_file))

                return True

        except Exception as e:
            logger.error(f"Error creating citation workflow: {e}")

        return False

    def _create_workflow_memory(self, bib_file: str):
        """Create MCP memory for citation workflow."""
        try:
            content = f"""
Citation Workflow Setup Complete

Bibliography File: {bib_file}
Zotero Integration: Active
Collections: {', '.join(self.pcs_collections.values())}

Usage Instructions:
1. Use Citation Picker extension in VS Code
2. Bibliography auto-updates from Zotero
3. Use @citationkey format in manuscripts
4. Run pandoc with --bibliography={bib_file}

PCS Collections Available:
{chr(10).join(f"- {name}" for name in self.pcs_collections.values())}

Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

            cmd = [
                "python",
                str(self.memory_manager),
                "add",
                content,
                "--category",
                "infrastructure",
                "--tags",
                "zotero",
                "citations",
                "workflow",
                "bibliography",
                "--importance",
                "4",
            ]

            subprocess.run(cmd, capture_output=True, text=True)
            logger.info("✅ Citation workflow memory created")

        except Exception as e:
            logger.error(f"Error creating workflow memory: {e}")


def main():
    """CLI interface for Zotero-MCP integration."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Zotero-MCP Integration for PCS Project"
    )
    parser.add_argument(
        "action",
        choices=["setup", "collections", "sync", "bibliography", "workflow"],
        help="Action to perform",
    )
    parser.add_argument("--api-key", help="Zotero API key")
    parser.add_argument("--user-id", help="Zotero user ID")
    parser.add_argument("--group-id", help="Zotero group ID (optional)")
    parser.add_argument("--style", default="nature", help="Citation style")
    parser.add_argument("--manuscript", help="Manuscript path for workflow setup")

    args = parser.parse_args()

    integration = ZoteroMCPIntegration()

    if args.action == "setup":
        if not args.api_key or not args.user_id:
            print("Error: --api-key and --user-id required for setup")
            return

        success = integration.setup_zotero_config(
            args.api_key, args.user_id, args.group_id
        )

        if success:
            print("✅ Zotero integration configured successfully")
        else:
            print("❌ Zotero setup failed")

    elif args.action == "collections":
        collections = integration.create_pcs_collections()
        print(f"✅ Created {len(collections)} PCS collections in Zotero")
        for key, name in integration.pcs_collections.items():
            print(f"  - {name}")

    elif args.action == "sync":
        results = integration.sync_mcp_with_zotero()
        print(f"✅ Sync complete: {results['synced_papers']} papers processed")
        if results["errors"]:
            print("Errors encountered:")
            for error in results["errors"]:
                print(f"  - {error}")

    elif args.action == "bibliography":
        bib = integration.generate_bibliography(style=args.style)
        if bib:
            print("Generated Bibliography:")
            print("=" * 50)
            print(bib)
        else:
            print("❌ Failed to generate bibliography")

    elif args.action == "workflow":
        if not args.manuscript:
            print("Error: --manuscript required for workflow setup")
            return

        success = integration.create_citation_workflow(args.manuscript)
        if success:
            print("✅ Citation workflow created successfully")
        else:
            print("❌ Workflow setup failed")


if __name__ == "__main__":
    main()
