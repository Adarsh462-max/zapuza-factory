# zapuza-factory
Django-based Factory Operations and Quality Control System

# Zapuza Factory Operations & Quality Control System

A Django-based web application designed to manage factory operations, raw material verification, quality inspections, approval workflows, and dispatch clearance.

## Overview

The Zapuza Factory Operations & Quality Control System aims to improve traceability and quality control throughout factory workflows. It provides a centralized interface for recording raw material intake, inspecting products, reviewing inspection results, and managing dispatch clearance.

## Features

### 1. Dashboard
- Centralized factory dashboard.
- Access to the application's operational modules.

### 2. Machine Management
- View and manage factory machines.
- Create machine records.
- Update machine active status.

### 3. Quality Inspection
- Record inspection measurements.
- Automatically evaluate measurements against configured tolerances.
- Generate PASS/FAIL results.
- Require defect photos for failed inspections.

### 4. Supervisor Approval
- Review inspection results.
- Approve or reject inspections.
- Record review remarks.

### 5. Raw Material Management
- Record supplier, purchase order, material grade, heat number, and received quantity.
- Upload Material Test Certificates (MTCs).
- Verify MTCs and heat numbers.
- Record laboratory test results.
- Release eligible materials or place them in supplier quarantine.

### 6. Dispatch Clearance
- Manage dispatch clearance records.
- Support inspection-based dispatch eligibility checks.

### 7. Authentication and Role-Based Access
- User login and logout.
- Factory role groups:
  - Admin
  - Quality Engineer
  - Quality Manager
  - Shift Supervisor
  - Dispatch Operator
- Role-based restrictions for factory operations.

## Technology Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, Bootstrap, Django Templates
- **Database:** SQLite
- **Authentication:** Django Authentication System
- **File Handling:** Django media uploads
- **Version Control:** Git and GitHub

## Project Structure

```text
zapuza_factory/
├── config/
│   ├── settings.py
│   └── urls.py
├── factory/
│   ├── management/
│   ├── templates/
│   │   ├── factory/
│   │   └── registration/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── media/
├── manage.py
├── db.sqlite3
└── README.md
```

*Note: The structure above is representative; actual files may differ.*

## Local Installation

### Prerequisites

- Python installed
- Git installed
- pip package manager

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/zapuza-factory.git
cd zapuza-factory
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

After creating `requirements.txt` in the project root:

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Configure factory roles

```bash
python manage.py setup_factory_roles
python manage.py setup_factory_permissions
```

### 7. Start the development server

```bash
python manage.py runserver
```

Open the application at:

`http://127.0.0.1:8000/`

Django Admin:

`http://127.0.0.1:8000/admin/`

## Environment Configuration

Before deployment, configure sensitive settings using environment variables. Do not commit production secret keys, passwords, or other credentials.

For production, configure `DEBUG=False`, appropriate `ALLOWED_HOSTS`, HTTPS, persistent database storage, and persistent media storage.

## Current Project Scope

This project implements core factory management and quality-control workflows. Additional capabilities such as QR-based station scanning, production routing, preventive maintenance scheduling, calibration locks, and advanced audit traceability may require further development.

## Future Enhancements

- QR-code-based inspection and job tracking.
- Production routing and traveler traceability.
- Preventive maintenance and calibration controls.
- Detailed audit logs.
- PostgreSQL integration.
- Automated testing and production deployment improvements.

## Project Status

**Development stage:** Core workflows implemented; deployment preparation and further validation are in progress.

## Author

**Adarsh Kumar Ray**

GitHub: https://github.com/Adarsh462-max

---

This project is developed for learning, demonstration, and factory workflow management experimentation. It should undergo further security, reliability, and operational validation before use in a real production environment.

