# 5S Management System

A Django-based management system for implementing and monitoring 5S workplace organization methodology.

## Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/5s-management.git
cd 5s-management
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run migrations
```bash
python manage.py migrate
```

5. Create superuser
```bash
python manage.py createsuperuser
```

6. Run development server
```bash
python manage.py runserver
```

## Features
- User role management (Admin, Zone Leader, Cell Leader)
- Zone and Cell management
- Issue tracking system
- Asset management
- Red tag system
