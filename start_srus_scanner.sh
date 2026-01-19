#!/bin/bash
# Start SRUS Scanner

echo "🎯 Starting SRUS Scanner..."
echo "📊 Opening browser..."
echo ""
echo "The scanner will open in your default browser."
echo "This is a paper trading simulation - not real money."
echo ""

# Try to open file in default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open index.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open index.html
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    start index.html
else
    # Fallback - start a simple HTTP server
    echo "Starting HTTP server on port 8000..."
    python3 -m http.server 8000
fi
