# Server.py Changes Summary

## Overview
Modified `server.py` to move image storage from browser local storage to server-side file storage, addressing the browser storage quota issue.

## Changes Made

### 1. **Added Imports**
- `datetime` - for timestamp generation
- `base64` - for encoding/decoding image data
- `os` - for file operations (imported but not strictly needed with Path)

### 2. **Added Constants and Helper Functions**
- `HISTORY_DIR` - Path to the history subfolder (`./history`)
- `ensure_history_dir()` - Creates the history directory if it doesn't exist

### 3. **Modified POST `/generate` Endpoint**
After successful image generation:
- Captures the final image data from the streaming response
- Generates a timestamp-based filename in format `YYYYMMDDhhmmss.png`
- Saves the PNG image to `history/YYYYMMDDhhmmss.png`
- Saves metadata to `history/YYYYMMDDhhmmss.json` with the following structure:
  ```json
  {
    "id": "20260123141028",
    "timestamp": "2026-01-23T14:10:28.123456",
    "image": "base64_encoded_image_data",
    "settings": {
      "model": "x/z-image-turbo:bf16",
      "prompt": "user prompt text",
      "seed": 12345,
      "width": 512,
      "height": 512,
      "steps": 12
    }
  }
  ```
- Logs successful saves to console

### 4. **Added GET `/history/index` Endpoint**
- Returns a JSON array containing all history items
- Reads all `.json` files from the history directory
- Returns them sorted by filename (newest first)
- Example response:
  ```json
  [
    {
      "id": "20260123141028",
      "timestamp": "2026-01-23T14:10:28.123456",
      "image": "base64_data...",
      "settings": { ... }
    },
    ...
  ]
  ```

### 5. **Added GET `/history/<image_name>` Endpoint**
- Retrieves a specific image by name (e.g., `/history/20260123141028`)
- Accepts both with and without `.png` extension
- Returns the image in base64 format matching the local storage structure
- Example response:
  ```json
  {
    "image": "base64_encoded_image_data",
    "settings": { ... },
    "timestamp": "2026-01-23T14:10:28.123456",
    "id": "20260123141028"
  }
  ```

## Data Format Compatibility
The JSON structure matches the existing `ollama_image_history` local storage format used by `index.html`, ensuring compatibility for the next phase when the frontend is updated.

## File Structure
```
OllamaImageGenerator/
├── server.py (modified)
├── index.html (to be modified in next task)
└── history/ (created automatically)
    ├── 20260123141028.png
    ├── 20260123141028.json
    ├── 20260123141129.png
    ├── 20260123141129.json
    └── ...
```

## Testing the New Endpoints

### Test `/history/index`:
```bash
curl http://localhost:8080/history/index
```

### Test `/history/<image_name>`:
```bash
curl http://localhost:8080/history/20260123141028
```

### Test DELETE `/history/<image_name>`:
```bash
# Delete a specific image
curl -X DELETE http://localhost:8080/history/20260123141028

# Expected success response:
# {"SUCCESS": true}

# Expected failure response (image not found):
# {"SUCCESS": false, "error": "Image not found: 20260123141028"}
```

## New Feature: Delete Individual History Images

### 6. **Added DELETE `/history/<image_name>` Endpoint**
- **Endpoint**: `DELETE /history/20260123141028` (example)
- **Action**: Deletes both the `.png` and `.json` files for the specified image
- **Accepts**: Image name with or without `.png` extension
- **Response Format**:
  - **Success**: `{"SUCCESS": true}`
  - **Failure**: `{"SUCCESS": false, "error": "error message"}`
- **HTTP Status Codes**:
  - `200`: Successful deletion
  - `404`: Image not found
  - `500`: Server error during deletion
- **Logging**: Logs successful deletions and errors to console

### CORS Support
- Updated `do_OPTIONS` to include `DELETE` in allowed methods
- All endpoints support CORS with `Access-Control-Allow-Origin: *`

## Notes
- The server must be restarted for changes to take effect
- The history directory will be created automatically on first image generation
- Images are stored both as PNG files and as base64 in JSON for compatibility
- Error handling is in place for file operations
