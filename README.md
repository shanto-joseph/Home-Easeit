# Home Easeit

A full-stack property rental platform built with Django. Supports three user roles — Admin, Landlord, and Customer — with a complete workflow covering property listings, visit scheduling, bookings, payments, and reviews.

---

![Screenshot 1](screenshots/Screenshot%202026-03-22%20134842.png)

![Screenshot 2](screenshots/Screenshot%202026-03-22%20134855.png)

![Screenshot 3](screenshots/Screenshot%202026-03-22%20134926.png)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Project](#running-the-project)
- [User Roles & Workflows](#user-roles--workflows)
- [Apps Overview](#apps-overview)
- [URL Reference](#url-reference)
- [Known Issues](#known-issues)

---

## Features

- Role-based access control (Admin, Landlord, Customer)
- Property listings with images, amenities, and search/filter
- Visit scheduling with time slot management and fee payment
- Rental booking workflow with landlord approval
- Payment tracking for visit fees, rent, security deposits, and refunds
- Automatic refunds on rejection or cancellation
- PDF booking receipt generation
- Real-time notification system with unread badge
- Admin dashboard for managing all entities
- Review system tied to completed bookings

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2.7 |
| Database | MySQL |
| Frontend | Tailwind CSS (CDN), Alpine.js (CDN) |
| Icons | Font Awesome 6 |
| Forms | django-crispy-forms + crispy-bootstrap5, widget-tweaks |
| PDF | ReportLab 4.0.4 |
| Images | Pillow 10.1.0 |
| Environment | python-dotenv |
| CORS | django-cors-headers |

---

## Project Structure

```
home_easeit/
├── accounts/           # User auth, registration, profiles
├── properties/         # Property CRUD, images, amenities, search
├── bookings/           # Booking lifecycle, PDF receipts
├── visits/             # Visit scheduling, time slots, reschedule flow
├── payments/           # Payment processing, refunds, transaction history
├── reviews/            # Post-booking property reviews
├── notifications/      # Event-driven notification system
├── admin_panel/        # Admin management dashboard
├── home_easeit/        # Django project settings and root URLs
├── templates/          # All HTML templates
├── static/             # CSS and JS
├── media/              # Uploaded images (profile pics, property images)
├── migrations/         # All app migrations (centralized)
├── manage.py
├── requirements.txt
└── .env
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- MySQL 8.0+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/your-username/home-easeit.git
cd home-easeit
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

See [Environment Variables](#environment-variables) for details.

---

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

DB_NAME=home_easeit
DB_USER=root
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=3306


```

> For production: set `DEBUG=False`, restrict `ALLOWED_HOSTS`, and use a strong `SECRET_KEY`.

---

## Database Setup

### 1. Create the MySQL database

```sql
CREATE DATABASE home_easeit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

This will also seed:
- 9 property types (1BHK, 2BHK, 3BHK, 4BHK, Studio, Villa, Independent House, Penthouse, Duplex)
- 15 amenities (Parking, AC, Gym, Pool, WiFi, etc.)

### 3. Create roles

Open the Django shell and create the required roles:

```bash
python manage.py shell
```

```python
from accounts.models import Role
Role.objects.get_or_create(name='ADMIN')
Role.objects.get_or_create(name='LANDLORD')
Role.objects.get_or_create(name='CUSTOMER')
```

### 4. Create a superuser (Admin)

```bash
python manage.py createsuperuser
```

> **If you modify any model**, run `python manage.py makemigrations` before `migrate`. This project uses a centralized `migrations/` folder mapped via `MIGRATION_MODULES` in settings, so a single command detects changes across all apps.

---

## Running the Project

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## User Roles & Workflows

### Customer

1. Register at `/accounts/register/`
2. Browse properties at `/properties/`
3. Schedule a visit → pay visit fee → wait for landlord approval
4. After a completed visit, create a booking → pay rent + security deposit
5. Visit fee is deducted from first month's rent
6. Manage bookings, visits, payments, and reviews from the navbar

### Landlord

1. Register at `/accounts/register/landlord/`
2. Create and manage property listings
3. Approve or reject visit requests and booking requests
4. Reschedule visits if needed
5. View transaction history and revenue

### Admin

1. Login with superuser credentials
2. Access management dashboard at `/admin-panel/manage/`
3. Manage users, properties, bookings, visits, payments, and reviews
4. Toggle user active status, change roles, hide reviews

---

## Apps Overview

### accounts
- Custom `AbstractBaseUser` with role-based access
- Separate registration flows for customers and landlords
- Profile view and update

### properties
- Full CRUD for property listings
- Multiple image upload (max 6, 5MB each)
- Amenity management via M2M through model
- Advanced search: keyword, property type, rent range, city, amenities
- Slug-based SEO-friendly URLs

### visits
- Time slot availability (9 AM – 6 PM, hourly)
- Session-based flow: schedule → pay → create visit
- Landlord can approve, reject, or request reschedule
- Customer can confirm reschedule with new date/time
- Visit fee refunded on rejection or if customer not interested

### bookings
- Session-based flow: fill form → pay → create booking
- Visit fee deducted from first month's rent if applicable
- Landlord approves/rejects with reason
- Customer can cancel (full refund)
- PDF receipt download via ReportLab

### payments
- Records for: VISIT_FEE, RENT, SECURITY_DEPOSIT, REFUND
- Payment methods: Credit Card, Debit Card, UPI, Net Banking, PayPal
- Refunds created as separate REFUND payment records
- Customer payment history and landlord transaction view

### reviews
- Only customers with COMPLETED bookings can review
- Rating 1–5 with comment
- One review per booking (OneToOne constraint)
- Admin can hide/show reviews

### notifications
- 17 notification types covering all visit, booking, payment, and review events
- Unread badge in navbar, live polling every 30 seconds
- Mark individual or all as read

### admin_panel
- Dashboard with platform-wide stats
- Manage users: search, filter by role/status, toggle active, change role, delete
- Manage properties: search, filter by type/availability, view details
- Manage bookings, visits, payments, reviews
- All detail views exposed as JSON endpoints

---

## URL Reference

| Prefix | App |
|---|---|
| `/accounts/` | Registration, login, logout, profile |
| `/properties/` | Property list, detail, create, edit, delete |
| `/bookings/` | Create, approve, reject, cancel, PDF |
| `/visits/` | Schedule, approve, reject, reschedule |
| `/payments/` | Booking payment, visit payment, history |
| `/reviews/` | Create review |
| `/notifications/` | List, mark read, unread API |
| `/admin-panel/` | Admin management dashboard |
| `/admin/` | Django built-in admin |

---

## Known Issues

- **Review submission crashes** — `reviews/views.py` imports from `utils.notifications` which does not exist. Fix: replace with `from notifications.models import Notification` and create notifications directly.
- **Cancel booking bug** — property availability is not restored on cancellation due to a status check ordering issue.
- **Visit time not submitted** — `VisitForm` has `visit_time` as a hidden input with no JavaScript to populate it. Visit scheduling will fail form validation.
- **Negative payment possible** — no guard when visit fee is greater than or equal to monthly rent.
- **`SYSTEM` payment method missing from model choices** — refund payments use `payment_method='SYSTEM'` which is not in `PAYMENT_METHOD_CHOICES`, causing a DB strict mode violation.
- **Missing template** — `admin_panel/dashboard.html` does not exist; the `admin_dashboard` view will return a 500 error.
- **`REJECTED` not in Visit.STATUS_CHOICES** — used in code but not declared as a valid choice on the model.
- **No booking date overlap validation** — two customers could book the same property for overlapping date ranges.
- **Stripe not integrated** — keys are configured but never used; all payments are marked completed immediately.

---

## Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

