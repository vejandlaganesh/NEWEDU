# NEWEDU Platform

A clean, scalable Django project foundation for the NEWEDU educational platform.

## Technology Stack
- **Backend:** Python, Django
- **Database:** MySQL
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Django Templates

## Project Structure
- `apps/`: Contains all Django applications (core, accounts, academics, etc.)
- `config/`: Main Django project configuration settings.
- `static/`: Global CSS and JS files.
- `templates/`: Global HTML templates.
- `media/`: Uploaded files directory.

## Installation & Setup

1. **Clone the repository.**
2. **Set up the virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in the required values.
   ```bash
   cp .env.example .env
   ```
5. **Database Setup (MySQL):**
   Ensure MySQL is running and create the database defined in your `.env` file.
6. **Apply Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
7. **Run Development Server:**
   ```bash
   python manage.py runserver
   ```

## Development seed data
Run `python manage.py seed_data` to create/update safe local demo accounts and Classes 10 learning data. Demo credentials are intended for local development only.
