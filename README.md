# BillKaro - GST Billing Software

**BillKaro** is a self-hosted GST billing and invoice management application built specifically for Indian small businesses. It handles GST calculations, invoice generation, PDF export, and customer/item management — all running on your own server with no monthly SaaS fees.

---

## What is BillKaro?

BillKaro is a complete billing solution for small manufacturing and trading businesses in India. It was built to replace manual billing (paper/Excel) with a fast, professional, digital system that:

- Generates proper **GST Tax Invoices** (compliant format)
- Automatically calculates **CGST + SGST** (intra-state) or **IGST** (inter-state) based on customer GSTIN
- Prints professional invoices with company letterhead, bank details, terms & conditions, and authorized signature line
- Exports invoices as **PDF** for sharing with customers or CA
- Manages your **customers, items/products, and invoice history** in one place
- Works on **desktop, mobile, and tablet** (responsive design)
- Can be installed as a **PWA** (Progressive Web App) on phone home screen

---

## Who is it for?

- Small manufacturers, job workers, traders
- Businesses that receive Purchase Orders (POs) from larger companies
- Any GST-registered business needing to issue Tax Invoices
- Businesses that want to avoid expensive SaaS billing software (Tally, Zoho, etc.)

---

## What does it do?

### Core Features
- ✅ **Tax Invoice generation** with auto invoice numbering (INV-2026-27-0001 format, resets each financial year)
- ✅ **Automatic GST calculation** — detects intra/inter state from GSTIN, applies CGST+SGST or IGST
- ✅ **PDF download** — professional invoice PDF with one click
- ✅ **Print support** — clean print layout, hides UI chrome
- ✅ **Customer management** — store GSTIN, address, vendor code, state auto-detection
- ✅ **Item/product management** — store HSN code, unit, price, custom columns (Drawing No, Material ID, etc.)
- ✅ **PO Number** — attach customer's Purchase Order number to each invoice
- ✅ **Amount in Words** — Indian numbering system (Lakh, Crore) on every invoice
- ✅ **Terms & Conditions** — configurable, printed on every invoice
- ✅ **Vendor Code** — display customer's supplier code on invoice (required by large companies)
- ✅ **Invoice cancellation** — cancel and restore invoices, excluded from dashboard totals
- ✅ **Dashboard** — monthly/custom date range revenue summary with CGST/SGST/IGST breakdown
- ✅ **Bulk PDF export** — download all invoices for a date range as one PDF (for CA/accountant)
- ✅ **CSV export** — export invoice list for Excel/accounting
- ✅ **Dark mode** — full dark/light theme support
- ✅ **Mobile responsive** — works on phone browser
- ✅ **PWA** — installable on Android/iOS home screen

### Business Settings
- Company name, GSTIN, address, phone, email
- About/description (shown on invoice)
- Bank details (bank name, account number, IFSC)
- Default GST rate
- Invoice prefix and numbering
- Terms & Conditions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Database | MySQL 8.0 |
| Frontend | Vue 3 + Vite |
| PDF Generation | WeasyPrint |
| Containerization | Docker + Docker Compose |
| Auth | JWT tokens (python-jose + passlib bcrypt) |

---

## Project Structure

```
billkaro-py/
├── app/
│   ├── main.py              # FastAPI app entry, serves API + built frontend
│   ├── database.py          # SQLAlchemy engine/session
│   ├── models.py            # ORM models (User, Customer, Item, Invoice, etc.)
│   ├── schemas.py           # Pydantic request/response models
│   ├── pdf.py               # WeasyPrint invoice PDF generator
│   └── routers/
│       ├── auth.py          # Login, register, JWT
│       ├── customers.py     # Customer CRUD
│       ├── items.py         # Item/product CRUD
│       ├── custom_columns.py # Dynamic invoice columns
│       ├── settings.py      # Business settings
│       ├── invoices.py      # Invoice CRUD, PDF, export
│       └── dashboard.py     # Revenue summary
├── frontend/                # Vue 3 app (built into static files)
│   ├── src/
│   │   ├── pages/           # Login, Dashboard, Invoices, Customers, Items, Settings
│   │   ├── css/app.css      # All styles + dark mode + mobile responsive
│   │   ├── store.js         # Pinia state management
│   │   └── router.js        # Vue Router
│   └── public/
│       └── manifest.json    # PWA manifest
├── docker/Dockerfile        # Multi-stage: builds Vue, then Python image
├── compose.yml              # Docker Compose config
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variables template
```

---

## How it Works

1. Docker builds the Vue 3 frontend (Node stage) → static files
2. Copies static files into the Python/FastAPI image
3. FastAPI serves both `/api/v1/*` API endpoints AND the Vue app (catch-all route)
4. MySQL runs as a separate container with a named volume for data persistence
5. Tables auto-created on first startup via SQLAlchemy
6. Default settings auto-seeded on first run

The app container exposes port **8000**. In production, Nginx sits in front as a reverse proxy handling SSL.

---

## Setup & Installation

### Requirements
- A Linux VPS (Ubuntu 22.04+ recommended)
- Docker + Docker Compose installed
- A domain name (optional but recommended for SSL)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR/billkaro-py.git
cd billkaro-py

# 2. Create environment file
cp .env.example .env
nano .env   # Set your DB_PASSWORD, DB_ROOT_PASSWORD, SECRET_KEY

# 3. Build and start
docker compose -f compose.yml up -d --build

# 4. Open in browser
# http://your-server-ip:8000

# 5. Register your account (first time)
# Go to /register, create your account, then log in
```

### Environment Variables (.env)

```env
DB_PASSWORD=your_strong_password
DB_ROOT_PASSWORD=your_strong_root_password
SECRET_KEY=your_random_secret_key_min_32_chars
```

### Production Setup with Nginx + SSL

```bash
# Install Nginx
apt update && apt install nginx certbot python3-certbot-nginx -y

# Create Nginx config
nano /etc/nginx/sites-available/billkaro
```

Paste this config:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    access_log /var/log/nginx/billkaro_access.log;
    error_log /var/log/nginx/billkaro_error.log;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }
}
```

```bash
# Enable site and get SSL
ln -s /etc/nginx/sites-available/billkaro /etc/nginx/sites-enabled/
certbot --nginx -d yourdomain.com
systemctl restart nginx
```

---

## Database Backup & Restore

### Manual Backup
```bash
docker compose -f compose.yml exec -T db mysqldump -u billkaro -p'YOUR_PASSWORD' --no-tablespaces billkaro > backup_$(date +%Y%m%d).sql
```

### Automated Daily Backup (cron)
```bash
crontab -e
# Add this line (runs at 2am daily):
0 2 * * * docker compose -f /srv/billkaro-py/compose.yml exec -T db mysqldump -u billkaro -p'YOUR_PASSWORD' --no-tablespaces billkaro > /srv/backups/billkaro_$(date +\%Y\%m\%d).sql
```

### Restore from Backup
```bash
cat backup_20260614.sql | docker compose -f compose.yml exec -T db mysql -u billkaro -p'YOUR_PASSWORD' billkaro
```

---

## Updating the Application

```bash
cd /srv/billkaro-py
git pull
docker compose -f compose.yml build app --no-cache
docker compose -f compose.yml up -d
```

---

## Useful Commands

```bash
# View live logs
docker compose -f compose.yml logs -f app

# Restart app only (no rebuild)
docker compose -f compose.yml restart app

# Access MySQL directly
docker compose -f compose.yml exec db mysql -u billkaro -p'YOUR_PASSWORD' billkaro

# Check running containers
docker ps

# Stop everything
docker compose -f compose.yml down

# Stop and delete all data (DANGER)
docker compose -f compose.yml down -v
```

---

## Local Development (without Docker)

**Backend:**
```bash
pip install -r requirements.txt
export DB_HOST=localhost DB_USER=billkaro DB_PASSWORD=yourpass DB_NAME=billkaro SECRET_KEY=devsecret
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev   # Runs on :5173, proxies /api to :8000
```

---

## Screenshots

*Invoice with GST breakdown, amount in words, vendor code, terms & conditions, and authorized signature*

---


