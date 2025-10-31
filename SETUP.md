# Quiz Hunt - Setup Guide

This guide will walk you through setting up the Quiz Hunt application from scratch.

## Prerequisites

- **Python 3.10+** (Python 3.11+ recommended)
- **pip** (Python package manager)
- **Git** (for cloning the repository, if applicable)

## Step-by-Step Setup

### 1. Clone or Navigate to Project Directory

If you have the project in a Git repository:
```bash
git clone <repository-url>
cd quiz_hunt
```

Or navigate to your project directory:
```bash
cd /path/to/quiz_hunt
```

### 2. Create Virtual Environment

Create and activate a virtual environment to isolate dependencies:

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

Install all required Python packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Database

The project uses SQLite by default (configured in `settings.py`). No additional database setup is required.

If you need to use PostgreSQL or MySQL, update `DATABASES` in `quiz_hunt/settings.py`.

### 5. Run Migrations

Create the database schema:

```bash
python manage.py makemigrations
python manage.py migrate
```

This will create all necessary database tables with UUID primary keys.

### 6. Create Superuser

Create an admin account to access the Django admin panel:

```bash
python manage.py createsuperuser
```

Follow the prompts to set username, email, and password.

### 7. Collect Static Files (Optional)

For production, collect static files:

```bash
python manage.py collectstatic
```

For development, static files are served automatically by Django.

### 8. Create Media Directory

Ensure the media directory exists for uploaded images:

```bash
mkdir -p media
```

Or create it manually. Django will create subdirectories automatically when files are uploaded.

### 9. Run Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

### 10. Access the Application

- **Home**: http://127.0.0.1:8000/
- **Django Admin**: http://127.0.0.1:8000/djadmin/
- **Custom Admin Dashboard**: http://127.0.0.1:8000/admin/overview/ (requires staff login)

## Initial Setup Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Migrations run (`python manage.py migrate`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Media directory exists
- [ ] Development server running

## Adding Your First Quiz Content

1. **Log into Django Admin**: Visit `/djadmin/` and log in with your superuser credentials.

2. **Ensure QuizConfig Exists**: The system automatically creates a `QuizConfig` on first use. You can view/edit it in the admin panel to adjust:
   - `total_allowed_answers_per_user` (default: 10)
   - `quiz_started_at` (quiz start timestamp)

3. **Create a Question**:
   - Go to "Questions" in the admin panel
   - Click "Add Question"
   - Fill in `title`, optional `body`, and set `is_active` to True
   - Save the question

4. **Add Choices**:
   - After saving the question, scroll down to the "Choices" inline
   - Add at least 4 choices
   - Set exactly **one** choice's `is_correct` to True
   - Save

5. **Add Images (Optional)**:
   - In the "Question images" inline, upload images
   - Images will be displayed in a grid on the question page

6. **Generate QR Code**:
   - Copy the question URL: `http://127.0.0.1:8000/question/<question-uuid>/`
   - Use any QR code generator to create a QR code pointing to this URL
   - Contestants scan the QR code and enter their nickname + PIN to access

## Testing the Flow

1. **Register a Contestant**:
   - Visit `/register/`
   - Fill in name, school name, and optional phone
   - Submit and **save the nickname and PIN** (shown only once!)

2. **Access a Question**:
   - Visit `/question/<uuid>/` (or scan QR code)
   - Enter nickname and PIN
   - If valid, you'll be redirected to the question view

3. **Submit an Answer**:
   - Select a choice and submit
   - You'll see a confirmation (correctness is never revealed)
   - Try accessing the same question again - you'll see the "already submitted" notice

4. **View Leaderboard** (Admin):
   - Log in as staff user
   - Visit `/admin/overview/`
   - View stats and leaderboard
   - Click a nickname to see detailed answer history

## Troubleshooting

### Database Errors

If you encounter migration errors:
```bash
python manage.py migrate --run-syncdb
```

Or reset (⚠️ **deletes all data**):
```bash
rm db.sqlite3
python manage.py migrate
```

### Media Files Not Showing

- Ensure `media/` directory exists
- Check `MEDIA_ROOT` and `MEDIA_URL` in `settings.py`
- Verify the media URL pattern is included in `quiz_hunt/urls.py`

### Static Files Issues

- Run `python manage.py collectstatic` (if using production server)
- Check `STATIC_URL` and `STATIC_ROOT` in settings

### Session Issues

- Clear browser cookies/session data
- Check `SECRET_KEY` in `settings.py` is set
- Verify session middleware is enabled

### Import Errors

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again
- Check Python version: `python --version` (should be 3.10+)

## Production Deployment

For production deployment:

1. **Set `DEBUG = False`** in `settings.py`
2. **Configure `ALLOWED_HOSTS`** with your domain
3. **Set a strong `SECRET_KEY`** (use environment variable)
4. **Use a production database** (PostgreSQL recommended)
5. **Configure static file serving** (WhiteNoise or separate web server)
6. **Set up media file serving** (CDN or dedicated storage)
7. **Use environment variables** for sensitive settings
8. **Enable HTTPS** for secure PIN transmission

## Environment Variables (Recommended)

Create a `.env` file (not committed to Git):

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

Load with `python-decouple` or `django-environ`.

## Support

For issues or questions, check the codebase comments or refer to Django documentation:
- [Django Documentation](https://docs.djangoproject.com/)
- [Django Tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/)

