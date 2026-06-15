# 🏥 CareVoice AI — Hospital Appointment Management Platform

> An AI-powered hospital workflow automation platform that enables patients to book appointments through conversational voice agents, with integrated scheduling, billing, payments, notifications, and a full administrative dashboard.

---

## Architecture

```
Patient Phone Call
       ↓
Twilio Voice Gateway (PSTN → WebSocket)
       ↓
FastAPI Voice Server (Media Stream Handler)
       ↓  ← G.711 μ-law bidirectional audio (resampled to 16kHz/24kHz PCM) →
Gemini Multimodal Live API (gemini-2.0-flash-exp Speech-to-Speech)
       ↓
Conversation Orchestrator (Finite State Machine)
       ↓
Business Logic Services (Appointments, Billing, Payments)
       ↓
PostgreSQL + Redis
       ↓
Celery Workers → Notifications (WhatsApp, SMS, Email)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **Database** | PostgreSQL 15, Redis 7 |
| **Task Queue** | Celery 5 (worker + beat scheduler) |
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS, ShadCN UI, Zustand |
| **AI Voice** | Gemini Multimodal Live API, Twilio Voice + Media Streams |
| **Payments** | Razorpay (UPI, Payment Links, Webhooks) |
| **Notifications** | WhatsApp, SMS, Email via Twilio / SMTP |
| **Monitoring** | Prometheus v2.53, Grafana 11.2 |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

---

## Docker Containers

The platform runs as **8 containers** managed by Docker Compose:

| Container | Image | Port | Description |
|-----------|-------|------|-------------|
| `carevoice-db` | `postgres:15-alpine` | `5433→5432` | Primary PostgreSQL database |
| `carevoice-redis` | `redis:7-alpine` | `6379` | Cache, session store & Celery broker |
| `carevoice-backend` | `anya-backend` (built) | `8000` | FastAPI REST + WebSocket server |
| `carevoice-celery-worker` | `anya-celery-worker` (built) | — | Async task processor (notifications, billing, slots) |
| `carevoice-celery-beat` | `anya-celery-beat` (built) | — | Periodic task scheduler |
| `carevoice-frontend` | `anya-frontend` (built) | `3000` | Next.js admin dashboard |
| `carevoice-prometheus` | `prom/prometheus:v2.53.0` | `9090` | Metrics collection |
| `carevoice-grafana` | `grafana/grafana:11.2.0` | `3001` | Metrics dashboards |

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose v2)
- Git

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/carevoice.git
cd carevoice
cp .env.example .env
```

Edit `.env` and fill in the required API keys (see [Environment Variables](#environment-variables) below).

### 2. Build & Start All Containers

```bash
docker compose up -d --build
```

This builds the backend, frontend, celery-worker, and celery-beat images, then starts all 8 containers. The database is automatically initialised and the admin user is seeded on first boot.

### 3. Verify Everything is Running

```bash
docker compose ps
```

All containers should show `Up` or `Up (healthy)`. The backend performs a health-check; give it ~30 seconds after first boot.

### 4. Access the Platform

| Service | URL | Credentials |
|---------|-----|-------------|
| **Admin Dashboard** | http://localhost:3000 | `admin@carevoice.ai` / `password123` |
| **Backend API** | http://localhost:8000 | — |
| **Swagger Docs** | http://localhost:8000/docs | — |
| **Prometheus** | http://localhost:9090 | — |
| **Grafana** | http://localhost:3001 | `admin` / `carevoice_grafana` |

> **First login:** Use `admin@carevoice.ai` / `password123`. The database starts completely empty — add departments, doctors, and patients through the dashboard UI.

---

## Common Operations

### Start / Stop

```bash
# Start all containers (foreground logs)
docker compose up

# Start all containers in background (detached)
docker compose up -d

# Stop all containers (preserves data volumes)
docker compose down

# Stop and remove all data volumes (full reset)
docker compose down -v
```

### Rebuild After Code Changes

```bash
# Rebuild and restart only changed services
docker compose up -d --build

# Rebuild a specific service
docker compose build backend
docker compose up -d backend
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f frontend
```

### Run Database Migrations (manual)

```bash
docker compose exec backend /app/.venv/bin/python -m alembic upgrade head
```

### Re-seed Admin User

```bash
docker compose exec backend /app/.venv/bin/python -m scripts.seed_data
```

### Open a Shell Inside a Container

```bash
# Backend Python shell
docker compose exec backend /app/.venv/bin/python

# Database psql shell
docker compose exec db psql -U postgres
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET_KEY` | ✅ | Secret key for JWT signing (min 32 chars) |
| `GEMINI_API_KEY` | ✅ | Gemini API key (for AI voice agent) |
| `TWILIO_ACCOUNT_SID` | ✅ | Twilio account SID (for voice calls) |
| `TWILIO_AUTH_TOKEN` | ✅ | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | ✅ | Twilio phone number (E.164 format) |
| `TWILIO_WEBHOOK_URL` | ✅ | Public URL Twilio posts call events to |
| `RAZORPAY_KEY_ID` | ✅ | Razorpay key ID (for payments) |
| `RAZORPAY_KEY_SECRET` | ✅ | Razorpay key secret |
| `RAZORPAY_WEBHOOK_SECRET` | ✅ | Razorpay webhook HMAC secret |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | ⚠️ | SMTP credentials for email notifications |
| `HOSPITAL_NAME` | ⚙️ | Display name for the hospital |
| `GST_PERCENTAGE` | ⚙️ | GST rate applied to invoices (default `18.0`) |

> The `DATABASE_URL` and `REDIS_URL` are automatically injected by `docker-compose.yml` and **do not** need to be set in `.env` for Docker deployments.

---

## Project Structure

```
carevoice/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # FastAPI route handlers
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic layer
│   │   ├── tasks/           # Celery async tasks
│   │   └── main.py          # FastAPI application entry point
│   ├── scripts/
│   │   └── seed_data.py     # Database initialisation & admin seed
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # Data-fetching React hooks
│   │   └── lib/             # API client & utilities
│   └── Dockerfile
├── monitoring/
│   └── prometheus/
│       └── prometheus.yml   # Prometheus scrape config
├── .env.example             # Environment variable template
├── docker-compose.yml       # Full stack orchestration
└── README.md
```

---

## Core Modules

### 🎙️ AI Voice Agent
- Answers incoming patient calls via Twilio
- Conversational appointment booking through Gemini Multimodal Live API (gemini-2.0-flash-exp)
- Emergency detection (chest pain, stroke, seizures, etc.)
- Automatic department and doctor recommendation
- Payment link generation during the call

### 📅 Appointment Management
- Dynamic doctor schedules and slot generation
- Real-time slot locking (Redis, 5-minute TTL)
- Booking, rescheduling, and cancellation workflows
- Holiday calendar support

### 💳 Billing & Payments
- Automated GST invoice generation (amounts stored in paise)
- Razorpay payment links (UPI, cards, net banking)
- Webhook-verified payment confirmation
- Refund handling

### 📊 Admin Dashboard
- Patient EHR directory with register / edit / delete
- Doctor directory with department assignment
- Appointment booking console with live slot picker
- Real-time call monitoring with live transcripts
- Revenue analytics and doctor utilisation charts
- System health monitoring

---

## API Documentation

Interactive Swagger UI is available at **http://localhost:8000/docs** once the backend container is running.

---

## Security

- JWT authentication with RBAC (Super Admin, Admin, Receptionist, Doctor)
- Razorpay webhook HMAC signature verification
- Twilio request signature validation
- Rate limiting on all endpoints
- HIPAA-ready architecture with audit logging

---

## License

Proprietary — All rights reserved.
