#!/bin/bash
# PCS AI Research Suite - Test All Shortcuts

echo "🧪 Testing PCS AI Research Suite Installation"
echo "============================================="

# Test PATH
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "📁 Checking installed files:"
echo "  Executables:"
ls -la ~/.local/bin/pcs-ai-suite* 2>/dev/null || echo "    ❌ No executables found"

echo "  Desktop entries:"
ls -la ~/.local/share/applications/pcs-ai-suite*.desktop 2>/dev/null || echo "    ❌ No desktop entries found"

echo "  Icon:"
ls -la ~/.local/share/icons/pcs-ai-suite.* 2>/dev/null || echo "    ❌ No icon found"

echo ""
echo "🎯 Testing commands:"

echo "  which pcs-ai-suite:"
which pcs-ai-suite 2>/dev/null && echo "    ✅ Found" || echo "    ❌ Not found"

echo "  which pcs-ai-suite-demo:"
which pcs-ai-suite-demo 2>/dev/null && echo "    ✅ Found" || echo "    ❌ Not found"

echo "  which pcs-ai-suite-full:"
which pcs-ai-suite-full 2>/dev/null && echo "    ✅ Found" || echo "    ❌ Not found"

echo ""
echo "📋 Available Makefile targets:"
cd /home/agourakis82/workspace/pcs-meta-repo
make -n gui-run 2>/dev/null && echo "  ✅ make gui-run" || echo "  ❌ make gui-run"
make -n gui-run-demo 2>/dev/null && echo "  ✅ make gui-run-demo" || echo "  ❌ make gui-run-demo"
make -n gui-run-full 2>/dev/null && echo "  ✅ make gui-run-full" || echo "  ❌ make gui-run-full"

echo ""
echo "🚀 Ready to use! Try:"
echo "  pcs-ai-suite          # Clean version (recommended)"
echo "  pcs-ai-suite-demo     # Demo version"
echo "  pcs-ai-suite-full     # Full version"
echo "  make gui-run          # Via Makefile"
