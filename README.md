# ToDoGemini 🚀

ToDoGemini is a premium, AI-powered task management application built with **FastAPI**, **SQLAlchemy**, and **Google Gemini AI**. It transforms your simple tasks into comprehensive plans using state-of-the-art AI.

## ✨ Features

- **AI Task Enhancement**: Automatically generates detailed descriptions and actionable subtasks using Gemini Flash.
- **Smart Priority**: AI suggests target priorities for your tasks.
- **AI Sidebar Assistant**: Interactive AI assistant to help you manage your tasks and stay motivated.
- **Modern UI**: Clean, responsive, and aesthetic design with dark mode and smooth transitions.
- **User Authentication**: Secure login and registration system.
- **Dockerized Deployment**: Easily run the entire stack with a single command.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: SQLite with SQLAlchemy ORM
- **AI**: Google Gemini Flash (via `google-generativeai`)
- **Frontend**: HTML5, Vanilla JS, CSS3
- **DevOps**: Docker, Docker Compose

## 🚀 Quick Start

### 1. Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)

### 2. Setup
Clone the repository and create your environment file:
```bash
cp .env.example .env
```
Edit `.env` and add your `GOOGLE_API_KEY`.

### 3. Run with Docker
```bash
docker compose up --build
```
The application will be available at `http://localhost:80`.

## 💻 Local Development

If you prefer to run without Docker:

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## 📂 Project Structure

- `app/main.py`: Application entry point.
- `app/models.py`: Database models (Todo, Subtask, User).
- `app/database.py`: Database configuration.
- `app/routers/`: API route handlers (Auth, Todo).
- `app/templates/`: Jinja2 HTML templates.
- `app/static/`: CSS and JS assets.

## 📄 License
MIT License. Feel free to use and contribute!
