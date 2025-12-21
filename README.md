# 🔐 The Vault

A relationship journal app for couples featuring a daily shared prompt system, real-time activity ideas, and a "Wrapped" style year-in-review analytics engine.

## Features

- **✨ Spark**: Browse date ideas, conversation starters, would-you-rather questions, and quick games for when you're together
- **✏️ Daily Shared Journal**: One prompt per day for both partners to answer async
- **🔓 Reveal Mechanic**: Journal entries unlock only after both partners respond
- **📊 Data Capsule**: Analytics fields designed for year-end "Wrapped" insights
- **📱 PWA Ready**: Mobile-first, installable on home screen
- **🚀 Production Ready**: Configured for Render + Neon.tech + Cloudinary

## The Duality

| Mode | Feature | When to Use |
|------|---------|-------------|
| **Together** | Spark ✨ | When you're in person—draw date ideas, conversation starters, games |
| **Apart** | Write ✏️ | Async daily prompts—answer separately, unlock together |

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

### 2. Environment Variables

Create a `.env` file:

```bash
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=your-postgres-url  # or use SQLite for local dev
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Seed Content

```bash
# Seed daily journal prompts (30 days of prompts)
python manage.py seed_prompts

# Seed Spark content (date ideas, conversation starters, etc.)
python manage.py seed_sparks
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000`

### 6b. Run with Gunicorn (optional)

```bash
./run_gunicorn
```

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
- `category`: Wholesome, Lore, Chaos, Spicy, Grind, Plot, Intellectual, Wildcard
- `active_date`: Which day this prompt appears

### Entry
- `user`: Who wrote it
- `prompt`: Which prompt it answers
- `couple`: Which vault this entry belongs to
- `text_content`: The response
- `photo`: Optional Cloudinary image
- **Analytics Fields** (auto-populated):
  - `word_count`: For "Total Words Written"
  - `sentiment_score`: Placeholder for NLP
  - `location_tag`: For "Places We Connected"

### Spark ✨ (NEW)
- `text`: The main idea/question
- `category`: Date Idea, Conversation, Would You Rather, Quick Game
- `option_b`: For "Would You Rather"—the second option
- `vibe`: Wholesome, Spicy, Chaos, etc. (same as prompts)
- `subtitle`: Optional extra context

## Spark Categories

| Category | Icon | Description |
|----------|------|-------------|
| 💕 Date Ideas | Heart | Activities to do together |
| 💬 Conversation | Chat | Deeper questions for in-person talks |
| ⚖️ Would You Rather | Scale | Quick fun decisions to debate |
| 🧩 Quick Games | Puzzle | Mini activities & challenges |

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
├── core/                       # Main app
│   ├── models.py              # Prompt, Entry, Spark + analytics
│   ├── views.py               # Journal + Spark views
│   ├── forms.py               # Entry form
│   ├── admin.py               # Admin interface
│   ├── urls.py                # App routes
│   └── management/commands/
│       ├── seed_prompts.py    # Seed journal prompts
│       └── seed_sparks.py     # Seed spark content
├── templates/
│   ├── base.html              # Design system (fonts, Tailwind, PWA)
│   ├── auth/                  # Login/Register
│   ├── journal/               # Daily journal UI
│   ├── spark/                 # ✨ Spark feature
│   │   ├── index.html         # Category selection
│   │   ├── card.html          # Single spark view
│   │   └── partials/card.html # HTMX card swap
│   ├── history/               # Past entries
│   ├── settings/              # User settings
│   └── partials/
│       └── bottom_nav.html    # Mobile tab bar
├── static/
│   ├── manifest.json          # PWA manifest
│   └── icons/                 # Favicon + app icons
├── vault/
│   ├── settings.py            # Production config
│   ├── urls.py                # Root routes
│   └── wsgi.py                # WSGI entry
├── build.sh                   # Render build script
├── requirements.txt           # Dependencies
└── render.yaml                # Render blueprint
```

## Navigation

The app uses a mobile-style bottom tab bar:

| Tab | Route | Description |
|-----|-------|-------------|
| ✨ Spark | `/spark/` | Browse ideas for together time |
| ✏️ Write | `/journal/` | Today's daily prompt |
| 📖 History | `/history/` | Past journal entries |
| ⚙️ Settings | `/settings/` | Profile & vault management |

## License

Private project.
