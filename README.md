# 🏥 CareVoice AI — Hospital Appointment Management Platform

> An AI-powered hospital workflow automation platform that enables patients to book appointments through conversational voice agents, with integrated scheduling, billing, payments, notifications, and administrative dashboards.

## Architecture

```
Patient Phone Call
       ↓
Twilio Voice Gateway (PSTN → WebSocket)
       ↓
FastAPI Voice Server (Media Stream Handler)
       ↓  ← G.711 μ-law bidirectional audio →
OpenAI Realtime API (GPT-4o Speech-to-Speech)
       ↓
Conversation Orchestrator (Finite State Machine)
       ↓
Business Logic Services (Appointments, Billing, Payments)
       ↓
PostgreSQL + Redis
       ↓
Celery Workers → Notifications (WhatsApp, SMS, Email)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Celery |
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, ShadCN UI, TanStack Query, Zustand |
| **AI Voice** | OpenAI Realtime API, Twilio Voice + Media Streams |
| **Payments** | Razorpay (UPI, Payment Links, Webhooks) |
| **Notifications** | WhatsApp, SMS, Email via Twilio |
| **Monitoring** | Prometheus, Grafana, Sentry |
| **DevOps** | Docker, Docker Compose, GitHub Actions |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/carevoice.git
cd carevoice
cp .env.example .env
# Edit .env with your API keys (OpenAI, Twilio, Razorpay)
```

### 2. Start with Docker Compose
```bash
docker-compose up -d
```

This starts: PostgreSQL, Redis, FastAPI backend, Celery workers, Next.js frontend, Prometheus, Grafana.

### 3. Development Mode (without Docker)

**Backend:**
```bash
cd backend
uv venv
# Activate virtual environment: source .venv/bin/activate (Windows: .venv\Scripts\activate)
uv pip install -r requirements.txt
cp ../.env.example .env
uv run alembic upgrade head
uv run python scripts/seed_data.py
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### 4. Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/carevoice_grafana)

## Core Modules

### 🎙️ AI Voice Agent
- Answers incoming calls via Twilio
- Conversational booking through OpenAI Realtime API
- Emergency detection (chest pain, stroke, seizures, etc.)
- Automatic department/doctor recommendation
- Payment link generation during call

### 📅 Appointment Management
- Dynamic doctor schedules & slot generation
- Real-time slot locking (Redis, 5-min TTL)
- Booking, rescheduling, cancellation workflows
- Holiday calendar support

### 💳 Billing & Payments
- Automated invoice generation with GST
- Razorpay payment links (UPI, cards)
- Webhook-verified payment confirmation
- Refund handling

### 📊 Admin Dashboard
- Real-time call monitoring with live transcripts
- Appointment management & manual override
- Revenue analytics & doctor utilization
- System health monitoring (Twilio, OpenAI, DB status)

## Project Structure
```
carevoice/
├── backend/          # FastAPI + SQLAlchemy + Voice Agent
├── frontend/         # Next.js 15 Admin Dashboard
├── monitoring/       # Prometheus + Grafana configs
├── .github/          # CI/CD workflows
├── docker-compose.yml
└── README.md
```

## API Documentation

Once running, visit http://localhost:8000/docs for the interactive Swagger UI.

## Security
- JWT authentication with RBAC (Super Admin, Admin, Receptionist, Doctor)
- Razorpay webhook HMAC signature verification
- Twilio request signature validation
- Rate limiting on all endpoints
- HIPAA-ready architecture with audit logging

## License
Proprietary — All rights reserved.
