# Chatbot API

A FastAPI application for a chatbot with multiple LLM integrations (Groq, Gemini, Deepseek), user authentication system, and admin management features.

## Features

- FastAPI-based REST API and interactive chat UI
- Modular LLM integration (Groq, Gemini, Deepseek)
- Complete user authentication system with JWT
- Admin dashboard for user management
- PostgreSQL database integration
- Docker and Docker Compose setup for easy deployment
- Environment-based configuration via `.env`
- Responsive Jinja2 templated UI with light/dark mode
- DRY template structure (navbar and footer partials)
- Streaming LLM responses with proper handling
- Model selection in chat UI

## Prerequisites

- Docker and Docker Compose
- An `.env` file with your API keys (see `.env.example`)

## Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/zakryz/chatbot.git
   cd chatbot
   ```

2. **Create a `.env` file with your configuration:**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your API keys and other settings
   ```

3. **Run the application with Docker Compose:**
   ```bash
   docker-compose up -d      # Build and run the services
   docker-compose logs -f    # View logs
   docker-compose down       # Stop the services
   ```

4. **Access the application:**
   - Web interface: http://localhost:8009
   - API documentation: http://localhost:8009/docs

## User Management

- **Registration:** Users can register but require admin approval
- **Authentication:** JWT-based authentication with secure cookie storage
- **Admin Dashboard:** Admins can approve new users, suspend/activate accounts, and grant admin privileges
- **Session Management:** Token expiration and secure session handling

## API Endpoints

### Authentication & User Management
- `GET /login` — Login page
- `POST /login` — Login endpoint for form submission
- `GET /logout` — Logout endpoint
- `GET /register` — Registration page
- `POST /register` — Registration endpoint
- `POST /token` — OAuth2 token endpoint
- `GET /admin/users` — Admin user management page
- `GET /api/admin/users` — API endpoint for user data
- `GET /users/pending` — API endpoint for pending users
- `POST /users/approve` — API endpoint to approve users
- `POST /users/admin` — API endpoint to manage admin privileges
- `POST /users/activate` — API endpoint to activate/suspend users

### Chat & LLM Integration
- `GET /chat` — Chat interface
- `POST /chat` — Chat endpoint (send messages to LLMs)
- `GET /` — Landing page
- `GET /health` — Health check endpoint
- `GET /static/*` — Static files (CSS, JS, images)

## Project Structure

```
chatbot/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── schemas.py              # Pydantic models
│   ├── db/                     # Database components
│   │   ├── crud.py             # Database operations
│   │   ├── database.py         # Database connection
│   │   ├── init_db.py          # Database initialization
│   │   └── models.py           # SQLAlchemy models
│   ├── llm_service/            # LLM integrations
│   │   ├── deepseek.py         # Deepseek API integration
│   │   ├── gemini.py           # Google Gemini API integration
│   │   ├── groq.py             # Groq API integration
│   │   └── router.py           # Router for LLM service selection
│   ├── static/                 # Static files
│   │   ├── css/
│   │   │   ├── code-block.css
│   │   │   └── mode-toggle.css
│   │   └── js/
│   │       ├── chat.js         # Chat functionality
│   │       ├── code-copy.js    # Code block copy functionality
│   │       ├── mode-toggle.js  # Dark/light mode toggle
│   │       └── model-selector.js # Model selection
│   └── templates/              # Jinja2 templates
│       ├── admin/
│       │   └── users.html      # Admin user management
│       ├── _footer.html        # Footer partial
│       ├── _navbar.html        # Navigation bar partial
│       ├── chat.html           # Chat interface
│       ├── index.html          # Landing page
│       ├── login.html          # Login page
│       └── register.html       # Registration page
├── .env                        # Environment variables (gitignored)
├── .env.example                # Example environment variables
├── .gitignore                  # Git ignore file
├── Dockerfile                  # Docker build instructions
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Development

For local development without Docker:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8009
```

## Security Notes

- User passwords are hashed using bcrypt
- JWT tokens are used for authentication
- CORS protection is implemented
- Admin privileges are protected with proper authorization
- Always use a strong SECRET_KEY in production

## Customization

- **Chat UI:** Edit `app/templates/chat.html` for the chat interface
- **Navbar/Footer:** Edit `app/templates/_navbar.html` and `app/templates/_footer.html`
- **Color Palette:** Adjust CSS variables in templates or `static/css/mode-toggle.css`
- **LLM Integrations:** Add or modify providers in `app/llm_service/`
- **Database Models:** Extend `app/db/models.py` for additional data structures

---

## Credits

Developed by **Muhammad Zakry Zoekruf**
