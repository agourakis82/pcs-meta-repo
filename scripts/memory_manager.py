#!/usr/bin/env python3
"""
PCS Memory Management Utility
Provides memory functionality while MCP server connection is being established.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse


class PCSMemoryManager:
    """Simple memory manager for PCS project context"""

    def __init__(self, memory_file: str = "~/.pcs-memory.json"):
        self.memory_file = Path(memory_file).expanduser()
        self.memories = self._load_memories()

    def _load_memories(self) -> List[Dict[str, Any]]:
        """Load existing memories from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r") as f:
                    data = json.load(f)
                    return data.get("memories", [])
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    def _save_memories(self):
        """Save memories to file"""
        data = {
            "memories": self.memories,
            "last_updated": datetime.now().isoformat(),
            "version": "pcs-v4.3",
        }
        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=2)

    def list_memories(self, category: Optional[str] = None) -> List[Dict]:
        """List all memories, optionally filtered by category"""
        memories = self.memories
        if category:
            memories = [m for m in memories if m.get("category") == category]

        print(f"\n📋 **PCS Project Memories** ({len(memories)} found)")
        print("=" * 60)

        for i, memory in enumerate(memories, 1):
            title = memory.get("title", "Untitled")
            category = memory.get("category", "uncategorized")
            importance = memory.get("importance", 3)
            created = memory.get("created_at", "Unknown")

            print(f"{i}. **{title}**")
            print(f"   Category: {category} | Importance: {importance}/5")
            print(f"   Created: {created}")

            # Show content preview
            content = memory.get("content", "")
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"   Preview: {preview}")
            print()

        return memories

    def search_memories(self, query: str) -> List[Dict]:
        """Search memories by content, title, or tags"""
        query_lower = query.lower()
        results = []

        for memory in self.memories:
            # Search in title, content, tags, and category
            searchable_text = " ".join(
                [
                    memory.get("title", ""),
                    memory.get("content", ""),
                    memory.get("category", ""),
                    " ".join(memory.get("tags", [])),
                ]
            ).lower()

            if query_lower in searchable_text:
                results.append(memory)

        print(f"\n🔍 **Search Results for '{query}'** ({len(results)} found)")
        print("=" * 60)

        for i, memory in enumerate(results, 1):
            title = memory.get("title", "Untitled")
            category = memory.get("category", "uncategorized")
            print(f"{i}. **{title}** (Category: {category})")

            # Highlight matching content
            content = memory.get("content", "")
            if query_lower in content.lower():
                # Find context around the match
                idx = content.lower().find(query_lower)
                start = max(0, idx - 50)
                end = min(len(content), idx + len(query) + 50)
                context = content[start:end]
                print(f"   Match: ...{context}...")
            print()

        return results

    def add_memory(
        self,
        title: str,
        content: str,
        category: str = "general",
        importance: int = 3,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Add a new memory"""
        import uuid

        memory_id = str(uuid.uuid4())
        memory = {
            "id": memory_id,
            "title": title,
            "content": content,
            "category": category,
            "importance": importance,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self.memories.append(memory)
        self._save_memories()

        print(f"✅ **Memory Added Successfully**")
        print(f"   Title: {title}")
        print(f"   Category: {category}")
        print(f"   ID: {memory_id}")

        return memory_id

    def get_project_context(self) -> Dict[str, Any]:
        """Get comprehensive project context"""
        context = {
            "project_name": "PCS Meta-Repo v4.3",
            "total_memories": len(self.memories),
            "categories": {},
            "recent_activity": [],
            "key_datasets": ["SWOW", "ZuCo", "DERCo", "GECO", "OneStop", "LPP"],
            "analysis_methods": ["AG5/KEC", "Curvature Analysis", "SEA/VAR/ARIMAX"],
            "publication_targets": ["Nature Human Behaviour", "Scientific Reports"],
        }

        # Count memories by category
        for memory in self.memories:
            category = memory.get("category", "uncategorized")
            context["categories"][category] = context["categories"].get(category, 0) + 1

        # Get recent memories (last 5)
        recent = sorted(
            self.memories, key=lambda x: x.get("updated_at", ""), reverse=True
        )[:5]
        context["recent_activity"] = [
            {
                "title": m.get("title", "Untitled"),
                "category": m.get("category", "uncategorized"),
                "updated": m.get("updated_at", "Unknown"),
            }
            for m in recent
        ]

        return context

    def show_context(self):
        """Display project context summary"""
        context = self.get_project_context()

        print("\n🧠 **PCS Project Context Summary**")
        print("=" * 50)
        print(f"Project: {context['project_name']}")
        print(f"Total Memories: {context['total_memories']}")
        print()

        print("📊 **Memory Categories:**")
        for category, count in context["categories"].items():
            print(f"   • {category}: {count} memories")
        print()

        print("🔬 **Key Datasets:**")
        for dataset in context["key_datasets"]:
            print(f"   • {dataset}")
        print()

        print("📈 **Analysis Methods:**")
        for method in context["analysis_methods"]:
            print(f"   • {method}")
        print()

        print("📝 **Publication Targets:**")
        for target in context["publication_targets"]:
            print(f"   • {target}")
        print()

        if context["recent_activity"]:
            print("🕒 **Recent Activity:**")
            for activity in context["recent_activity"]:
                print(f"   • {activity['title']} ({activity['category']})")


def main():
    parser = argparse.ArgumentParser(description="PCS Memory Management Utility")
    parser.add_argument(
        "action", choices=["list", "search", "add", "context"], help="Action to perform"
    )
    parser.add_argument("content", nargs="?", help="Memory content (for add action)")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument(
        "--category", "-c", help="Filter by category or set category for add"
    )
    parser.add_argument("--title", "-t", help="Memory title (for add)")
    parser.add_argument(
        "--importance", "-i", type=int, default=3, help="Importance level 1-5 (for add)"
    )
    parser.add_argument("--tags", nargs="*", help="Tags (for add)")

    args = parser.parse_args()

    manager = PCSMemoryManager()

    if args.action == "list":
        manager.list_memories(category=args.category)

    elif args.action == "search":
        if not args.query:
            print("Error: Search requires --query parameter")
            return
        manager.search_memories(args.query)

    elif args.action == "add":
        content = args.content
        title = args.title

        if not content:
            print("Error: Add requires content as positional argument")
            return

        # Generate title from content if not provided
        if not title:
            title = content[:50] + "..." if len(content) > 50 else content

        manager.add_memory(
            title=title,
            content=content,
            category=args.category or "general",
            importance=args.importance,
            tags=args.tags or [],
        )

    elif args.action == "context":
        manager.show_context()


if __name__ == "__main__":
    main()
