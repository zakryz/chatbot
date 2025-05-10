# Chatbot API

A FastAPI application for a chatbot with multiple LLM integrations (Groq, Gemini, Deepseek) and a modern, customizable landing page.

## Features

- FastAPI-based REST API
- Modular LLM integration (Groq, Gemini, Deepseek)
- Docker and Docker Compose setup
- Environment-based configuration
- Jinja2 templated landing page with custom color palette
- DRY template structure (navbar and footer partials)
- Static files support (for CSS, JS, images)

## Prerequisites

- Docker and Docker Compose
- An `.env` file with your API keys

## Setup

1. Ensure you have Docker and Docker Compose installed.
2. Clone this repository.
3. Create a `.env` file with the necessary API keys (see `.env.example`).
4. Run the application with Docker Compose.

## Running the application

```bash
# Build and run the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the services
docker-compose down
```

## API Endpoints

- `GET /` — Landing page (Jinja2 template)
- `GET /health` — Health check endpoint
- `POST /chat` — Chat endpoint (send messages to LLMs)
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
│   │   └── template.py
│   ├── static/
│   │   └── ... (CSS, JS, images)
│   └── templates/
│       ├── index.html
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
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

## Customization

- **Landing Page:** Edit `app/templates/index.html` for your homepage content and style.
- **Navbar/Footer:** Edit `app/templates/_navbar.html` and `app/templates/_footer.html` for DRY, reusable layout.
- **Color Palette:** Adjust CSS variables in your templates for branding.
- **LLM Integrations:** Add or modify providers in `app/llm_service/`.

---

## Credits

Developed by **Muhammad Zakry Zoekruf**