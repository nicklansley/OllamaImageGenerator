# Model Selection Feature - User Flow

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Opens Page                          │
│                 http://localhost:8080                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              index.html Loads                               │
│         JavaScript executes loadModels()                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Fetch GET /models from server                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│    Server queries Ollama API at /api/tags                   │
│    Filters models based on IMAGE_GEN_MODEL_LIST             │
│    Returns JSON array: ["model1", "model2"]                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         JavaScript receives model list                      │
│         Populates <select> dropdown                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│    Check localStorage for 'ollama_selected_model'           │
└────────────────────────┬────────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
                ▼                 ▼
    ┌──────────────────┐  ┌──────────────────┐
    │ Model found in   │  │ No saved model   │
    │ localStorage     │  │                  │
    └────────┬─────────┘  └────────┬─────────┘
             │                     │
             │                     ▼
             │         ┌──────────────────────┐
             │         │ Select first model   │
             │         │ from list (default)  │
             │         └────────┬─────────────┘
             │                  │
             └──────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Model is selected in dropdown                  │
│              User sees the interface ready                  │
└─────────────────────────────────────────────────────────────┘


## User Interaction Flow

┌─────────────────────────────────────────────────────────────┐
│         User selects different model from dropdown          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         'change' event listener triggered                   │
│    localStorage.setItem('ollama_selected_model', value)     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Model preference saved                         │
│         (persists across browser sessions)                  │
└─────────────────────────────────────────────────────────────┘


## Image Generation Flow

┌─────────────────────────────────────────────────────────────┐
│         User enters prompt and clicks Generate              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      generateImage() function called                        │
│      Reads modelSelect.value (current selection)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      POST /generate with JSON body:                         │
│      {                                                      │
│        "model": "x/z-image-turbo:bf16",  ← from dropdown   │
│        "prompt": "...",                                     │
│        "seed": 0,                                           │
│        "width": 1024,                                       │
│        "height": 1024,                                      │
│        "steps": 12                                          │
│      }                                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│      Server forwards to Ollama API                          │
│      Streams response back to client                        │
│      Image generated and displayed                          │
└─────────────────────────────────────────────────────────────┘
```

## localStorage Structure

```javascript
// Key
'ollama_selected_model'

// Value (example)
'x/z-image-turbo:bf16'

// Storage Location
// Browser's localStorage for domain: localhost:8080
```

## Code Integration Points

### 1. HTML (index.html)
- **Line 590-593**: Model selection dropdown
- **Line 661**: modelSelect element reference
- **Line 693**: MODEL_STORAGE_KEY constant
- **Line 696-733**: loadModels() function
- **Line 736-740**: Change event listener
- **Line 743**: loadModels() called on page load
- **Line 822**: modelSelect.value used in API request

### 2. Server (server.py)
- **Line 15**: IMAGE_GEN_MODEL_LIST configuration
- **Line 34-82**: /models endpoint handler
- **Line 44-46**: Model filtering logic

### 3. CSS (index.html)
- **Line 195-227**: Select element styling
