# 🏗️ Project Structure

```
home_easeit/
├── 📄 manage.py                          # Django's command-line utility
├── 📄 requirements.txt                   # Project dependencies
├── 📄 .env                               # Environment variables (gitignored)
├── 📄 .env.example                       # Safe template for .env
├── 📄 .gitignore
├── 📄 README.md
├── 📄 PROJECT_STRUCTURE.md
│
├── 📁 home_easeit/                       # Main project directory
│   ├── __init__.py
│   ├── settings.py                       # Project settings and configuration
│   ├── urls.py                           # Root URL routing
│   └── wsgi.py                           # WSGI configuration
│
├── 📁 accounts/                          # User authentication app
│   ├── apps.py
│   ├── models.py                         # User, Role
│   ├── views.py                          # Register, login, logout, profile
│   ├── forms.py                          # UserRegistrationForm, UserProfileForm
│   └── urls.py
│
├── 📁 properties/                        # Property management app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                         # Property, PropertyType, Amenity, PropertyImage, PropertyAmenity
│   ├── views.py                          # List, detail, create, edit, delete, toggle availability
│   ├── forms.py                          # PropertyForm, PropertySearchForm
│   └── urls.py
│
├── 📁 bookings/                          # Booking management app
│   ├── apps.py
│   ├── models.py                         # Booking
│   ├── views.py                          # Create, approve, reject, cancel, end rental, PDF
│   ├── forms.py                          # BookingForm
│   └── urls.py
│
├── 📁 visits/                            # Visit scheduling app
│   ├── apps.py
│   ├── models.py                         # Visit
│   ├── views.py                          # Schedule, approve, reject, reschedule, refund
│   ├── forms.py                          # VisitForm
│   └── urls.py
│
├── 📁 payments/                          # Payment processing app
│   ├── apps.py
│   ├── models.py                         # Payment
│   ├── views.py                          # Booking payment, visit payment, history, transactions
│   ├── forms.py                          # PaymentForm
│   └── urls.py
│
├── 📁 reviews/                           # Reviews and ratings app
│   ├── apps.py
│   ├── models.py                         # Review
│   ├── views.py                          # Create review
│   ├── forms.py                          # ReviewForm
│   └── urls.py
│
├── 📁 notifications/                     # Notification system
│   ├── apps.py
│   ├── models.py                         # Notification
│   ├── views.py                          # List, mark read, unread count API
│   └── urls.py
│
├── 📁 admin_panel/                       # Custom admin interface
│   ├── apps.py
│   ├── views.py                          # Dashboard, manage users/properties/bookings/visits/payments/reviews
│   ├── urls.py
│   └── templatetags/
│       ├── __init__.py
│       └── admin_filters.py              # Custom template filter: subtract
│
├── 📁 migrations/                        # Centralized migrations for all apps
│   ├── __init__.py
│   ├── accounts/
│   │   ├── 0001_initial.py
│   │   ├── 0002_alter_user_options_alter_user_username.py
│   │   └── 0003_alter_user_managers.py
│   ├── properties/
│   │   ├── 0001_initial.py
│   │   ├── 0002_add_property_types.py    # Seeds 9 property types
│   │   ├── 0003_add_amenities.py         # Seeds 15 amenities with icons
│   │   └── 0004_alter_amenity_options_alter_property_options_and_more.py
│   ├── bookings/
│   │   ├── 0001_initial.py
│   │   ├── 0002_add_payment_status_reject_reason.py
│   │   ├── 0003_remove_payment_status.py
│   │   └── 0004_add_visit_reference.py
│   ├── visits/
│   │   ├── 0001_initial.py
│   │   └── 0002_remove_visit_feedback_visit_reason.py
│   ├── payments/
│   │   └── 0001_initial.py
│   ├── reviews/
│   │   ├── 0001_initial.py
│   │   └── 0002_review_is_hidden.py
│   └── notifications/
│       ├── 0001_initial.py
│       └── 0002_alter_notification_notification_type.py
│
├── 📁 templates/                         # All HTML templates
│   ├── base.html                         # Base layout: navbar, notifications, footer
│   ├── home.html                         # Landing page
│   ├── 404.html
│   ├── 500.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── register_landlord.html
│   │   ├── profile.html
│   │   └── profile_update.html
│   ├── properties/
│   │   ├── property_list.html            # Browse & search properties
│   │   ├── customer_property_detail.html
│   │   ├── landlord_property_detail.html
│   │   ├── landlord_properties.html
│   │   ├── landlord_bookings.html
│   │   ├── landlord_home.html
│   │   ├── property_create.html
│   │   └── property_edit.html
│   ├── bookings/
│   │   ├── create_booking.html
│   │   ├── customer_bookings.html
│   │   ├── landlord_bookings.html
│   │   └── booking_detail.html
│   ├── visits/
│   │   ├── schedule_visit.html
│   │   ├── customer_visits.html
│   │   └── landlord_visits.html
│   ├── payments/
│   │   ├── booking_payment.html
│   │   ├── visit_payment.html
│   │   ├── payment_history.html
│   │   └── landlord_transactions.html
│   ├── reviews/
│   │   └── create_review.html
│   ├── notifications/
│   │   └── notification_list.html
│   ├── components/                       # Reusable UI components
│   └── admin_panel/
│       ├── home.html
│       ├── manage_dashboard.html
│       ├── manage_users.html
│       ├── manage_properties.html
│       ├── manage_bookings.html
│       ├── manage_visits.html
│       ├── manage_payments.html
│       ├── manage_reviews.html
│       └── includes/
│           └── sidebar.html
│
├── 📁 static/                            # Static files
│   ├── css/
│   │   └── styles.css                    # Custom utility overrides
│   └── js/
│       └── scripts.js                    # Gallery, rating, map, form validation
│
└── 📁 media/                             # User-uploaded files (gitignored)
    ├── logo/
    │   └── icon.png
    ├── profile_pics/
    └── property_images/
```

---

## 📚 Key Components

### 🔐 Authentication System (accounts/)
- Custom `AbstractBaseUser` with FK-based role system (ADMIN, LANDLORD, CUSTOMER)
- Separate registration flows for customers and landlords
- Role-based login redirect: Admin → admin home, Landlord → landlord home, Customer → home
- Profile view and update with profile picture upload
- Remember me session control

### 🏠 Property Management (properties/)
- Full CRUD for property listings with slug-based URLs
- Multiple image upload (max 6 images, 5MB each) with primary image selection
- Amenity management via M2M through model (PropertyAmenity)
- Advanced search: keyword, property type, rent range, city, amenities
- 9 property types and 15 amenities seeded via migrations
- Availability toggle for landlords and admins

### 📅 Booking System (bookings/)
- Session-based flow: fill form → pay → booking created after payment
- Visit fee automatically deducted from first month's rent
- Landlord approve / reject (with reason) workflow
- Customer cancellation with full automatic refund
- End rental marks booking COMPLETED and restores property availability
- PDF receipt generation using ReportLab (A4, styled with property + contact details)

### 👥 Visit Management (visits/)
- Time slot availability: 9 AM – 6 PM, hourly (9 slots/day)
- Session-based flow: schedule → pay visit fee → visit created after payment
- Landlord can approve, reject (with refund), or request reschedule
- Customer confirms reschedule with new date and time
- Visit fee refunded on rejection or if customer not interested after visit
- AJAX endpoint for available/booked slots per date

### 💰 Payment Processing (payments/)
- Payment types: VISIT_FEE, RENT, SECURITY_DEPOSIT, REFUND
- Payment methods: Credit Card, Debit Card, UPI, Net Banking, PayPal
- Refunds created as separate REFUND payment records (not reversals)
- Customer payment history with totals and counts
- Landlord transaction view with net balance calculation
- JSON detail endpoint per payment

### ⭐ Review System (reviews/)
- Only customers with COMPLETED bookings can submit a review
- Rating 1–5 via range slider input
- One review per booking enforced at DB level (OneToOneField)
- Admin can hide/show reviews from the management panel
- No edit or delete after submission

### 🔔 Notifications (notifications/)
- 17 notification types covering all visit, booking, payment, and review events
- Custom manager with `unread()` method
- Unread badge in navbar with live polling every 30 seconds (Alpine.js + fetch)
- Mark individual or all notifications as read
- JSON API endpoint for unread count and latest 10 notifications

### 👨‍💼 Admin Panel (admin_panel/)
- Management dashboard with platform-wide stats (users, properties, bookings, revenue)
- Manage users: search, filter by role/status, toggle active, change role, delete
- Manage properties: search, filter by type/availability, toggle availability, delete
- Manage bookings and visits with status updates
- Manage payments overview
- Hide/show reviews
- All detail views exposed as JSON endpoints for modal popups
- Protected by `AdminRequiredMixin` (LoginRequired + UserPassesTest)

---

## 🔧 Configuration

### 📁 settings.py
- `AUTH_USER_MODEL = 'accounts.User'`
- `MIGRATION_MODULES` maps each app to `migrations/<app>/` (centralized, non-standard)
- MySQL database with `utf8mb4` charset and `STRICT_TRANS_TABLES`
- Static files from `static/`, media files from `media/`
- Templates centralized in `templates/`
- Crispy Forms with Bootstrap 5 pack
- Email backend: console only (development)
- Stripe keys loaded from `.env` (not yet integrated in views)

### 📁 urls.py
| URL Prefix | Destination |
|---|---|
| `/` | Home (TemplateView) |
| `/accounts/` | accounts app |
| `/properties/` | properties app |
| `/bookings/` | bookings app |
| `/visits/` | visits app |
| `/payments/` | payments app |
| `/reviews/` | reviews app |
| `/notifications/` | notifications app |
| `/admin-panel/` | admin_panel app |
| `/landlord-home/` | LandlordHomeView |
| `/admin-home/` | AdminHomeView |
| `/admin/` | Django built-in admin |

---

## 🛠️ Development Tools

### 📦 Static Files
- Tailwind CSS via CDN for all styling
- Alpine.js via CDN for dropdowns and interactive components
- Font Awesome 6 for icons
- Custom `styles.css` for property card animations, image preview, modal styles
- Custom `scripts.js` for gallery, rating slider, map init (Leaflet), form validation

### 🗃️ Templates
- Single `base.html` with full navbar (role-aware), notification dropdown, flash messages, and footer
- All app templates extend `base.html` via `{% extends 'base.html' %}`
- `components/` folder available for reusable partials
- Admin panel has its own `includes/sidebar.html`

### 🗄️ Database Models

```
Role ──< User
User ──< Property          (landlord)
User ──< Visit             (customer)
User ──< Booking           (customer)
User ──< Payment
User ──< Review            (reviewer)
User ──< Notification

PropertyType ──< Property
Property ──< PropertyImage
Property >──< Amenity      (through PropertyAmenity)
Property ──< Visit
Property ──< Booking
Property ──< Review

Visit ──| Booking          (OneToOne, optional)
Booking ──| Review         (OneToOne)
Payment >── Booking        (nullable FK)
Payment >── Visit          (nullable FK)
```

### 📱 Frontend
- Fully responsive with Tailwind utility classes
- Notification bell with real-time unread count (polls every 30s)
- Property image gallery with thumbnail switching
- AJAX time slot picker for visit scheduling
- Alpine.js `x-data` / `x-show` for dropdown menus and modals
