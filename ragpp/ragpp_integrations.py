#!/usr/bin/env python3
"""
RAG++ Universal Integration CLI
Setup RAG++ with ChatGPT, Codex, and GitHub Copilot
"""

import argparse
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from integrations.copilot_integration import CopilotRAGEnhancer
from integrations.openai_integration import OpenAIRAGIntegration


def setup_chatgpt_integration():
    """Setup ChatGPT/GPT-4 integration."""
    print("🤖 Setting up ChatGPT + RAG++ integration...")

    openai_integration = OpenAIRAGIntegration()

    # Export Custom GPT instructions
    gpt_instructions = openai_integration.export_for_custom_gpt()

    print("\n✅ ChatGPT integration ready!")
    print(f"📄 Custom GPT instructions: {gpt_instructions}")
    print("\n🎯 Next steps:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Import instructions into Custom GPT")
    print("3. Use python ragpp/integrations/openai_integration.py --action chat")


def setup_copilot_integration():
    """Setup GitHub Copilot integration."""
    print("🚀 Setting up GitHub Copilot + RAG++ integration...")

    enhancer = CopilotRAGEnhancer()

    # Setup complete workspace
    created_files = enhancer.setup_copilot_workspace(
        project_description="PCS Meta-Repo: Computational psychiatry research with RAG++ system",
        research_areas=[
            "computational psychiatry",
            "machine learning mental health",
            "digital phenotyping",
            "neuroimaging analysis",
        ],
    )

    # Create chat context
    chat_context = enhancer.create_copilot_chat_context()
    created_files["chat_context"] = chat_context

    print("\n✅ GitHub Copilot integration complete!")
    print("📁 Created files:")
    for file_type, path in created_files.items():
        print(f"  - {file_type}: {path}")

    print("\n🎯 Next steps:")
    print("1. Restart VS Code to load new settings")
    print("2. Copilot will now use research context automatically")
    print("3. Use @workspace in Copilot Chat for project-specific help")


def setup_all_integrations():
    """Setup all integrations."""
    print("🌟 Setting up ALL RAG++ integrations...")
    print("=" * 50)

    # Setup ChatGPT
    setup_chatgpt_integration()
    print("\n" + "=" * 50)

    # Setup Copilot
    setup_copilot_integration()
    print("\n" + "=" * 50)

    print("🎉 ALL INTEGRATIONS COMPLETE!")
    print("\n📋 Summary:")
    print("✅ ChatGPT/GPT-4: Custom GPT instructions created")
    print("✅ GitHub Copilot: Workspace enhanced with research context")
    print("✅ VS Code: Settings optimized for RAG++ development")

    print("\n🚀 You can now use:")
    print("1. Custom ChatGPT with research knowledge")
    print("2. Enhanced Copilot code suggestions")
    print("3. Research-informed development workflow")


def test_integrations():
    """Test all integrations."""
    print("🧪 Testing RAG++ integrations...")

    # Test OpenAI integration
    print("\n🤖 Testing ChatGPT integration...")
    try:
        openai_integration = OpenAIRAGIntegration()
        if openai_integration.client:
            print("✅ OpenAI client initialized")
        else:
            print("⚠️ OpenAI client not ready (need API key)")
    except Exception as e:
        print(f"❌ OpenAI integration error: {e}")

    # Test Copilot integration
    print("\n🚀 Testing Copilot integration...")
    try:
        enhancer = CopilotRAGEnhancer()
        comment = enhancer.generate_research_comment(
            "test_function", "machine learning analysis"
        )
        print("✅ Copilot enhancement ready")
        print(f"📝 Sample comment: {comment.split()[0]}...")
    except Exception as e:
        print(f"❌ Copilot integration error: {e}")

    print("\n🎯 Test complete!")


def interactive_setup():
    """Interactive setup wizard."""
    print("🧙 RAG++ Integration Wizard")
    print("=" * 30)

    print("\nWhich integrations would you like to setup?")
    print("1. ChatGPT/GPT-4 only")
    print("2. GitHub Copilot only")
    print("3. All integrations")
    print("4. Test existing integrations")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1":
        setup_chatgpt_integration()
    elif choice == "2":
        setup_copilot_integration()
    elif choice == "3":
        setup_all_integrations()
    elif choice == "4":
        test_integrations()
    else:
        print("❌ Invalid choice. Please run again.")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="RAG++ Universal Integration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ragpp_integrations.py --setup all          # Setup all integrations
  python ragpp_integrations.py --setup chatgpt      # Setup ChatGPT only
  python ragpp_integrations.py --setup copilot      # Setup Copilot only
  python ragpp_integrations.py --test               # Test integrations
  python ragpp_integrations.py --interactive        # Interactive wizard
        """,
    )

    parser.add_argument(
        "--setup",
        choices=["chatgpt", "copilot", "all"],
        help="Setup specific integration",
    )
    parser.add_argument("--test", action="store_true", help="Test all integrations")
    parser.add_argument(
        "--interactive", action="store_true", help="Run interactive setup wizard"
    )

    args = parser.parse_args()

    if args.setup == "chatgpt":
        setup_chatgpt_integration()
    elif args.setup == "copilot":
        setup_copilot_integration()
    elif args.setup == "all":
        setup_all_integrations()
    elif args.test:
        test_integrations()
    elif args.interactive:
        interactive_setup()
    else:
        # Default to interactive if no arguments
        interactive_setup()


if __name__ == "__main__":
    main()
    main()
