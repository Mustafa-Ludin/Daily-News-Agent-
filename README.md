# Daily AI News Workflow

This project fetches news from public RSS feeds, uses OpenAI to research, analyze, and edit a daily newsletter, then sends it by Gmail SMTP.

## Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Copy the example environment file:

```bash
cp .env.example .env
```

3. Add your own credentials to `.env`:

```bash
OPENAI_API_KEY=your_openai_api_key
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

Use a Gmail app password for `EMAIL_PASSWORD`, not your normal Gmail account password.

## Running

Run the workflow once:

```bash
python main.py
```

Run the scheduler:

```bash
python scheduler.py
```

## Security

Never commit `.env`. It contains private credentials and is intentionally ignored by `.gitignore`.

Commit `.env.example` instead so other users can see which environment variables are required without exposing secrets.
