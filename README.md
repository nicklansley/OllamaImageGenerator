# Ollama Image Generator
![oig.png](oig.png)

## Overview
This project is a simple proxy server for the Ollama Image Generator, which serves an HTML interface and forwards API requests to the Ollama API. The purpose of this is to overcome the CORS policy of many browserswhich prevents direct access to the Ollama API from a local HTML file. The main components include:
- **`server.py`**: The backend server that handles API requests and serves the HTML interface.
- **`index.html`**: The frontend interface for users to interact with the image generation functionality.

## Architecture
- The server listens on port **8080** and forwards requests to the Ollama API located at **`http://localhost:11434/api/generate`**.
- The server acts as a proxy, forwarding requests from the HTML interface to the Ollama API and returning the generated images to the HTML interface in 'stream' format so that the progress of the image generation is displayed as it is being generated.
- The HTML interface is served directly from the server, allowing users to generate images through a web interface.
- **Model Selection**: Users can select from available image generation models via a dropdown menu. The selected model is automatically saved to the browser's localStorage and will be remembered on subsequent visits.
- The `/models` API endpoint returns a filtered list of available image generation models from the Ollama API.
- Tested to work with Python 3.9 and later

## To set up and start the server
- Clone the repository.
- From the terminal run: 
<pre>ollama pull x/z-image-turbo:bf16
ollama pull x/flux2-klein:latest</pre>
- Run `python3 server.py` in the terminal.
- Open `http://localhost:8080` in your web browser.
- Type your prompt into the 'Prompt' field, adjust the controls (click 'Random' to generate a random seed) then click 'Generate' to generate an image. You will see message 'Step N of X' as the image is being generated.
- Right-click the image and select 'Save image as...' to save the image (or drag and drop the image into a folder to save it)
- Images are alo saved to a 'history' list on the left side of the interface. Double-click an image to load it into the interface, or single-click the image then click the 'x' button to remove it from the history. The history is saved to your web browser'slocalStorage and will be remembered on subsequent visits.

## Key Files
- **`server.py`**: Main server logic and API handling.
- **`index.html`**: User interface for image generation.

## Maintenance Notes
- server.py filters the model list to only include models capable of image generation. You will need to add any new models to the IMAGE_GEN_MODEL_LIST in server.py as well as use 'ollama pull model_name' to pull the model from the Ollama registry. Only successfully pulled models will be included in the model list on the web interface.

## Author
- Nick Lansley
- [GitHub](https://github.com/nicklansley)

## License
- MIT License


