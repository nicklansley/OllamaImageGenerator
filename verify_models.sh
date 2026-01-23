#!/bin/bash

echo "==================================="
echo "Model Selection Feature Verification"
echo "==================================="
echo ""

echo "1. Testing /models API endpoint..."
echo "-----------------------------------"
MODELS=$(curl -s http://localhost:8080/models)
echo "Response: $MODELS"
echo ""

echo "2. Checking if models are returned as JSON array..."
echo "-----------------------------------"
if echo "$MODELS" | python3 -c "import sys, json; json.load(sys.stdin); print('✓ Valid JSON array')" 2>/dev/null; then
    echo "Status: PASS"
else
    echo "Status: FAIL"
fi
echo ""

echo "3. Counting available models..."
echo "-----------------------------------"
MODEL_COUNT=$(echo "$MODELS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")
echo "Number of models: $MODEL_COUNT"
echo ""

echo "4. Listing available models..."
echo "-----------------------------------"
echo "$MODELS" | python3 -m json.tool
echo ""

echo "==================================="
echo "Verification Complete!"
echo "==================================="
echo ""
echo "To test the full implementation:"
echo "1. Open http://localhost:8080 in your browser"
echo "2. Check that the 'Select Model' dropdown appears"
echo "3. Verify it contains the models listed above"
echo "4. Select a model and generate an image"
echo "5. Refresh the page and verify your model selection is remembered"
echo ""
echo "To test with the test page:"
echo "Open http://localhost:8080/test.html"
