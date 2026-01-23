#!/bin/bash
# Test script for DELETE endpoint

echo "Testing DELETE endpoint for history images"
echo "==========================================="
echo ""

# Test 1: Try to delete a non-existent image
echo "Test 1: Deleting non-existent image (should fail)"
echo "Request: DELETE /history/99999999999999"
curl -X DELETE http://localhost:8080/history/99999999999999 2>/dev/null | python3 -m json.tool
echo ""
echo ""

# Test 2: Create a test image and delete it
echo "Test 2: Create and delete a test image"
echo "---------------------------------------"

# First, let's check what's in the history
echo "Current history:"
curl -s http://localhost:8080/history/index | python3 -m json.tool | head -5
echo ""

# Note: To properly test deletion, you would need to:
# 1. Generate an actual image through the UI
# 2. Note its timestamp ID
# 3. Then run: curl -X DELETE http://localhost:8080/history/<timestamp>
echo ""
echo "To test deletion of a real image:"
echo "1. Generate an image through the web UI"
echo "2. Get the image ID from: curl http://localhost:8080/history/index"
echo "3. Delete it with: curl -X DELETE http://localhost:8080/history/<image_id>"
echo ""
echo "Expected success response: {\"SUCCESS\": true}"
echo "Expected failure response: {\"SUCCESS\": false, \"error\": \"...\"}"
