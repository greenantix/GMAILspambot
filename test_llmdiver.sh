#!/bin/bash
# Simple test script for LLMdiver functionality

echo "🧪 Testing LLMdiver Automation"
echo "================================="

# Check if daemon is running
if ./start_llmdiver.sh status >/dev/null 2>&1; then
    echo "✅ Daemon is running"
else
    echo "❌ Daemon not running - starting it..."
    ./start_llmdiver.sh start
    sleep 2
fi

echo ""
echo "📝 Creating test file with TODOs and issues..."

# Create a test file with obvious issues
cat > test_llmdiver_trigger.py << 'EOF'
#!/usr/bin/env python3
"""
Test file to trigger LLMdiver analysis
Contains various code issues for testing
"""

# TODO: This needs to be implemented properly
def broken_function():
    """This function has issues"""
    # FIXME: Infinite loop risk
    while True:
        pass

# Mock implementation - needs real code  
def mock_data_processor():
    """Stub - replace with real implementation"""
    return {"mock": "data"}

# Dead code - this function is never used
def unused_helper():
    """This function is never called"""
    print("Dead code detected")

# TODO: Add error handling
def risky_operation():
    result = 10 / 0  # Division by zero!
    return result

if __name__ == "__main__":
    # FIXME: Add proper main logic
    print("Test file created - LLMdiver should detect issues")
EOF

echo "✅ Test file created: test_llmdiver_trigger.py"
echo ""
echo "🔍 Monitoring daemon logs (watch for file detection)..."
echo "   Press Ctrl+C to stop monitoring"
echo ""

# Show real-time logs
timeout 30 tail -f llmdiver_daemon.log || echo ""

echo ""
echo "📊 Checking results..."

# Check if analysis was created
if [ -d ".llmdiver" ] && [ -f ".llmdiver/latest_analysis.md" ]; then
    echo "✅ Analysis completed"
    echo "📁 Latest analysis:"
    ls -la .llmdiver/analysis_*.md | tail -n 1
    echo ""
    echo "📋 Analysis content:"
    echo "===================="
    head -n 20 .llmdiver/latest_analysis.md
else
    echo "⏳ Analysis still in progress or failed"
fi

echo ""
echo "🔄 Recent git commits:"
git log --oneline -3

echo ""
echo "🧹 Cleaning up test file..."
rm -f test_llmdiver_trigger.py

echo ""
echo "✅ Test completed! Check the logs above for automation results."