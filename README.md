# Chatbot API

A FastAPI application for a chatbot with multiple LLM integrations (Groq, Gemini, Deepseek) and a modern, customizable landing page.

## Features

- FastAPI-based REST API and interactive chat UI
- Modular LLM integration (Groq, Gemini, Deepseek)
- Docker and Docker Compose setup
- Nginx reverse proxy with HTTPS support (template-based config)
- Environment-based configuration via `.env`
- Jinja2 templated landing page and chat UI with custom color palette
- DRY template structure (navbar and footer partials)
- Static files support (for CSS, JS, images)
- Model selection in chat UI

## Prerequisites

- Docker and Docker Compose
- An `.env` file with your API keys (see `.env.example`)
- (For HTTPS) A domain name and access to DNS settings

## Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/your-repo/chatbot.git
   cd chatbot
   ```

2. **Create a `.env` file with your API keys:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your keys
   ```

3. **(Optional) Adjust Nginx template for your domain:**
   - Edit `nginx/conf.d/default.conf.template` and set `${DOMAIN}` and `${UPSTREAM}` as needed.
   - The Docker Compose setup uses this template for Nginx configuration.

4. **Run the application with Docker Compose:**
   ```bash
   docker-compose up -d      # Build and run the services
   docker-compose logs -f    # View logs
   docker-compose down       # Stop the services
   ```

## Setting up Nginx with HTTPS (Let's Encrypt)

This project uses Nginx as a reverse proxy for HTTPS support. The configuration is template-based for easy reuse.

### 1. Prepare your domain

- Point your domain's A record to your server's public IP.

### 2. Obtain SSL certificates with Certbot

On your server, install Certbot and request certificates:

```bash
sudo apt update
sudo apt install certbot
sudo apt install python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com
```

Certificates will be saved in `/etc/letsencrypt/live/yourdomain.com/`.

### 3. Configure Nginx

- The Nginx container uses `nginx/conf.d/default.conf.template` as a template.
- Docker Compose mounts your certificates into the container:
  ```yaml
  volumes:
    - ./nginx/conf.d:/etc/nginx/conf.d:ro
    - /etc/letsencrypt/live/yourdomain.com/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
    - /etc/letsencrypt/live/yourdomain.com/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
  ```
- Update `${DOMAIN}` in the template or use environment substitution.

### 4. Reload Nginx

- Restart the Nginx container to apply changes:
  ```bash
  docker-compose restart nginx
  ```

### 5. Automatic Certificate Renewal

- Certbot certificates renew automatically. Add a cron job to reload Nginx after renewal:
  ```bash
  0 3 * * * certbot renew --post-hook "docker-compose restart nginx"
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
├── nginx/
│   └── conf.d/
│       ├── default.conf.template
│       └── default.conf (gitignored)
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