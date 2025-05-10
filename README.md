# Chatbot API

A FastAPI application for a chatbot with multiple LLM integrations (Groq, Gemini, Deepseek) and a modern, customizable landing page.

## Features

- FastAPI-based REST API and interactive chat UI
- Modular LLM integration (Groq, Gemini, Deepseek)
- Docker and Docker Compose setup
- Environment-based configuration via `.env`
- Jinja2 templated landing page and chat UI with custom color palette
- DRY template structure (navbar and footer partials)
- Static files support (for CSS, JS, images)
- Model selection in chat UI

## Prerequisites

- Docker and Docker Compose
- An `.env` file with your API keys (see `.env.example`)

## Setup

1. Ensure you have Docker and Docker Compose installed.
2. Clone this repository.
3. Create a `.env` file with the necessary API keys (see `.env.example`).
4. Run the application with Docker Compose.

## Running the application

```bash
docker-compose up -d      # Build and run the services
docker-compose logs -f    # View logs
docker-compose down       # Stop the services
```

## API Endpoints

- `GET /` — Landing page (Jinja2 template)
- `GET /chat` — Interactive chat UI (model selection supported)
- `GET /health` — Health check endpoint
- `POST /chat` — Chat endpoint (send messages to LLMs, streaming response)
- `GET /docs` — Interactive API documentation (Swagger UI)
- `GET /static/*` — Static files (CSS, JS, images)

## Project Structure

```
chatbot/
├── app/
│   ├── main.py
│   ├── llm_service/
│   │   ├── deepseek.py
│   │   ├── gemini.py
│   │   ├── groq.py
│   │   ├── router.py
│   ├── static/
│   │   ├── css/
│   │   │   └── mode-toggle.css
│   │   └── js/
│   │       ├── chat.js
│   │       ├── mode-toggle.js
│   │       └── model-selector.js
│   └── templates/
│       ├── index.html
│       ├── chat.html
│       ├── _navbar.html
│       └── _footer.html
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Development

For local development without Docker:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Customization

- **Landing Page:** Edit `app/templates/index.html` for your homepage content and style.
- **Chat UI:** Edit `app/templates/chat.html` for the chat interface.
- **Navbar/Footer:** Edit `app/templates/_navbar.html` and `app/templates/_footer.html` for DRY, reusable layout.
- **Color Palette:** Adjust CSS variables in your templates or `static/css/mode-toggle.css` for branding.
- **LLM Integrations:** Add or modify providers in `app/llm_service/`.
- **Model Options:** Update model lists in `groq.py`, `gemini.py`, or `deepseek.py`.

---

## Credits

Developed by **Muhammad Zakry Zoekruf**