# Copilot Instructions for Ollama Image Generator

## Overview
This project is a simple proxy server for the Ollama Image Generator, which serves an HTML interface and forwards API requests to the Ollama API. The main components include:
- **`server.py`**: The backend server that handles API requests and serves the HTML interface.
- **`index.html`**: The frontend interface for users to interact with the image generation functionality.

## Architecture
- The server listens on port **8080** and forwards requests to the Ollama API located at **`http://localhost:11434/api/generate`**.
- The HTML interface is served directly from the server, allowing users to generate images through a web interface.

## Developer Workflows
- **Running the Server**: Execute `python3 server.py` to start the server. Ensure that the Ollama API is running on the specified port.
- **Testing**: Use tools like Postman or curl to send requests to the API endpoint and verify responses.
- **Debugging**: Check the console output of the server for any errors or logs related to incoming requests.

## Project Conventions
- Follow PEP 8 for Python code style in `server.py`.
- HTML and CSS should adhere to standard practices, with a focus on responsive design.

## Integration Points
- The server communicates with the Ollama API for image generation. Ensure that the API is accessible and running before testing the application.

## Examples
- To generate an image, navigate to the HTML interface in a web browser and fill out the required fields. The server will handle the request and display the generated image.

## Key Files
- **`server.py`**: Main server logic and API handling.
- **`index.html`**: User interface for image generation.