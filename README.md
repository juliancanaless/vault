# 🔐 The Vault

A relationship journal app for couples featuring a daily shared prompt system and a "Wrapped" style year-in-review analytics engine.

## Features

- **Daily Shared Journal**: One prompt per day for both partners
- **Reveal Mechanic**: Entries unlock only after both partners respond
- **Data Capsule**: Analytics fields designed for year-end "Wrapped" insights
- **PWA Ready**: Mobile-first, installable on home screen
- **Production Ready**: Configured for Render + Neon.tech + Cloudinary

## Tech Stack

- **Backend**: Django 5.x
- **Frontend**: Django Templates + Tailwind CSS (CDN) + HTMX
- **Database**: PostgreSQL (Neon.tech)
- **Media**: Cloudinary
- **Deployment**: Render (stateless)

## Local Development

### 1. Clone and Setup

```bash
cd vault
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Create Superuser

```bash
python manage.py createsuperuser
```

### 4. Add Sample Prompts

```bash
python manage.py shell
```

```python
from core.models import Prompt, PromptCategory
from datetime import date

# Create today's prompt
Prompt.objects.create(
    text="What's one thing you're grateful for about our relationship?",
    category=PromptCategory.WHOLESOME,
    active_date=date.today()
)
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000`

### 5b. Run with Gunicorn (optional)

```bash
./run_gunicorn
```

Visit `http://localhost:8000`

## Production Deployment (Render)

### Environment Variables

Set these in your Render dashboard:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (auto-generated) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app.onrender.com` |
| `DATABASE_URL` | Neon.tech PostgreSQL connection string |
| `CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |

### Deploy

1. Connect your repo to Render
2. Set Build Command: `./build.sh`
3. Set Start Command: `gunicorn vault.wsgi:application`
4. Add environment variables

## Data Models

### Prompt
- `text`: The daily question
- `category`: Wholesome, Lore, Chaos, Spicy, Grind, Plot, Intellectual, Wildcard (for Wrapped charts)
- `active_date`: Which day this prompt appears

### Entry
- `user`: Who wrote it
- `prompt`: Which prompt it answers
- `text_content`: The response
- `photo`: Optional Cloudinary image
- **Analytics Fields** (auto-populated):
  - `word_count`: For "Total Words Written"
  - `sentiment_score`: Placeholder for NLP
  - `location_tag`: For "Places We Connected"

## Wrapped Analytics Queries

```python
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from core.models import Entry

# Total words written in 2025
Entry.objects.filter(
    user=user, 
    created_at__year=2025
).aggregate(total=Sum('word_count'))

# Category breakdown (Top Vibe)
Entry.objects.filter(
    user=user, 
    created_at__year=2025
).values('prompt__category').annotate(
    count=Count('id')
).order_by('-count')

# Monthly activity
Entry.objects.filter(
    user=user, 
    created_at__year=2025
).annotate(
    month=TruncMonth('created_at')
).values('month').annotate(count=Count('id'))
```

## Project Structure

```
vault/
├── core/                   # Main app
│   ├── models.py          # Prompt & Entry with analytics fields
│   ├── views.py           # Journal logic (3 states)
│   ├── forms.py           # Entry form
│   ├── admin.py           # Admin interface
│   └── urls.py            # App routes
├── templates/
│   ├── base.html          # Design system (fonts, Tailwind, PWA)
│   ├── auth/              # Login/Register
│   └── journal/           # Daily journal UI
├── static/
│   ├── manifest.json      # PWA manifest
│   └── icons/             # App icons
├── vault/
│   ├── settings.py        # Production config
│   ├── urls.py            # Root routes
│   └── wsgi.py            # WSGI entry
├── build.sh               # Render build script
├── requirements.txt       # Dependencies
└── render.yaml            # Render blueprint
```

## License

Private project.

