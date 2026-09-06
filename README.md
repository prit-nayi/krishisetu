# KrishiLink AI

KrishiLink AI is a full-stack agri-market intelligence platform for Gujarat farmers, buyers, and administrators. It helps farmers compare markets, estimate realistic net value for crop lots, forecast price movements, and receive SELL/HOLD/PARTIAL SELL recommendations backed by structured market analysis and AI explanations.

## Overview

The platform combines:
- a Django REST API for authentication, crop lot management, market intelligence, pricing, forecasting, and decision logic
- a React + Vite frontend for farmer and buyer workflows
- role-based access for farmers, buyers, and admins
- direct crop marketplace and inquiry flow
- deterministic financial calculations and AI-style explanation layer

## Project Goals

- help farmers choose the best mandi or buyer option for their crop lot
- compare current market value with transport and storage costs
- generate short-term crop price forecasts using historical market data
- recommend whether to sell now, hold, or partially sell
- provide transparent AI explanations grounded in structured numbers
- support regional market intelligence for Gujarat commodities, especially cotton and groundnut

## Current Features

### Farmer and account features
- JWT-based authentication and registration
- farmer profile creation and update
- crop lot creation, edit, list, and deletion
- commodity support for cotton and groundnut
- ownership-scoped access to farmer data

### Market intelligence
- market listing and market detail APIs
- price and history endpoints for commodity pricing
- nearby market lookup and ranking
- Gujarat APMC market seed data with coordinate metadata
- commodity normalization and market data sync support

### Financial and forecasting engine
- transport cost estimation
- revenue and net value calculations
- forecast confidence and market trend analysis
- SELL / HOLD / PARTIAL SELL recommendation rules
- recommendation persistence and retrieval

### Marketplace and buyer workflow
- direct crop listing marketplace
- buyer inquiry flows
- accept/reject listing decisions
- stats dashboard for marketplace activity

### AI explanation layer
- mock/demo Granite-style explanation support
- structured decision reasoning connected to computed outputs
- explanation service designed for future IBM Watsonx/Granite integration

## Tech Stack

### Backend
- Python 3.11
- Django 4.2
- Django REST Framework
- JWT authentication
- Celery + Redis
- SQLite for local development
- PostgreSQL-ready configuration for production

### Frontend
- React 18
- Vite
- JavaScript
- React Router
- React Query
- Axios
- Recharts
- Leaflet / React Leaflet

### Data and ML
- Pandas
- NumPy
- scikit-learn
- statsmodels
- xgboost

## Repository Structure

```text
krishisetu/
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── agents/
│   │   ├── common/
│   │   ├── crops/
│   │   ├── decisions/
│   │   ├── forecasting/
│   │   ├── markets/
│   │   └── marketplace/
│   ├── krishilink/
│   ├── tests/
│   ├── tools/
│   ├── manage.py
│   ├── requirements.txt
│   └── db.sqlite3
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── architecture.md
├── project_status.md
├── README.md
├── Gujarat APMC_data/
├── KrishiLink_AI_Complete_System_Specification.pdf
└── .gitignore
```

## Local Development Setup

### 1. Clone and open the project

```bash
git clone <repository-url>
cd krishisetu
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file inside the `backend` folder if needed for local settings and AI credentials.

Example:

```env
DATA_GOV_API_KEY=your_key_here
IBM_WATSONX_URL=
IBM_WATSONX_API_KEY=
IBM_WATSONX_PROJECT_ID=
IBM_GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
IBM_GRANITE_MODE=mock
AI_DEMO_MODE=true
```

### 5. Run database migrations

```bash
cd backend
python manage.py migrate
```

### 6. Seed demo data (optional but recommended)

```bash
python manage.py seed_demo_data
```

This creates sample users such as farmer, buyer, and admin accounts plus demo crop lots and marketplace records.

## Run the app

### Backend

```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

API base URL:
- http://localhost:8000/api/v1/

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server:
- http://localhost:5173

## Key API Areas

The backend exposes the main API endpoints under `/api/v1/`:

- Auth: register, login, refresh, me
- Farmer profile: profile management
- Crop lots: create/list/update/delete crop lots
- Markets: markets, prices, history, nearby markets
- Forecasting: forecast information and decision support
- Decisions: analysis and recommendation endpoints
- Marketplace: listings, inquiries, and buyer flows

## Demo Accounts

When demo data is seeded, common sample accounts include:
- Farmer: `farmer_demo@krishilink.in`
- Buyer: `buyer_demo@krishilink.in`
- Admin: `admin_demo@krishilink.in`

Password:
- `Password123!`

## Project Status

This repository is a working MVP-style implementation with the following completed areas:
- authentication and role-based access
- farmer and buyer profiles
- crop lot management
- market intelligence for Gujarat commodity data
- pricing and analysis logic
- forecasting and recommendation engine
- direct crop marketplace workflow
- React frontend for user-facing interactions

The project status and more detailed progress are tracked in [project_status.md](project_status.md).

## Important Notes

- The project is designed for local development with SQLite by default.
- IBM Granite integrations are set up with a demo/mock mode by default to allow local development without external credentials.
- The app is tailored to Gujarat agriculture use cases, especially cotton and groundnut market decisions.
- If you want to enable real market sync or AI capabilities, add valid env variables and configure the related providers.

## Useful commands

```bash
# backend migrations
cd backend
python manage.py migrate

# backend tests
python manage.py test

# optional: create superuser
python manage.py createsuperuser

# frontend build
cd frontend
npm run build
```

## License

This project is for internal/demo use unless a separate license is added by the project owner.

## Contributing

For local development, keep updates aligned with the current structure and avoid breaking the role-based flow and decision engine logic. Documentation and project status are maintained across the repo, including [architecture.md](architecture.md) and [project_status.md](project_status.md).

## 11. Final Decision Engine

The decision engine must be deterministic and auditable.

Conceptual calculation:

`Expected Future Net Value = Forecasted Future Revenue - Storage Cost - Expected Quality Loss - Additional Transport/Market Cost - Capital/Opportunity Cost - Risk Adjustment`

Compare with:

`Current Net Selling Value`

Possible decisions:
- SELL_NOW
- HOLD
- PARTIAL_SELL

Do not hard-code final numerical demo results. Results must come from prototype data and calculations.

## 12. Data Model — MVP

### User
- id
- name
- phone/email
- role
- authentication fields
- created_at

### FarmerProfile
- user_id
- district
- village
- latitude
- longitude

### CropLot
- id
- farmer_id
- commodity
- variety
- quantity
- unit
- moisture
- quality_grade
- harvest_date
- storage_status
- location
- created_at
- updated_at

### Market
- id
- name
- district
- latitude
- longitude

### MarketPrice
- id
- market_id
- commodity
- min_price
- max_price
- modal_price
- arrival_quantity
- price_date
- source
- source_timestamp

### Forecast
- id
- commodity
- market_id
- forecast_date
- predicted_price
- lower_bound
- upper_bound
- model_name
- model_version
- generated_at

### Recommendation
- id
- crop_lot_id
- recommendation
- current_net_value
- expected_future_net_value
- confidence
- reasoning_factors
- generated_at
- model/rule version

## 13. Data Rules

- Price must never be negative.
- Quantity must be greater than zero.
- min_price <= modal_price <= max_price.
- Missing data is NOT the same as zero.
- Every market record must have a source and timestamp.
- Forecasts must identify the model/version.
- Stale data must be clearly marked.
- Recommendations require evidence.
- Numerical values shown to users must originate from backend calculations/data.
- No fabricated buyer, market or forecast data.

## 14. Security

Implement:
- JWT authentication
- Role-based authorization
- Server-side permission checks
- Password hashing
- Input validation
- ORM/parameterized queries
- Rate limiting
- Secure secrets/environment variables
- No secrets in logs
- Audit logging for sensitive operations
- Object-level ownership checks
- Tool allow-list
- Prompt-injection-aware tool boundaries
- No arbitrary SQL from Granite
- No arbitrary Python execution from Granite

## 15. Performance Principles

Target:
- Normal read APIs preferably <500 ms p95.
- Simple CRUD should be fast and synchronous.
- Long-running forecasting/agent workflows should use background jobs.
- Cache reusable market/forecast data.
- Avoid repeated LLM calls.
- Prefer one final Granite generation over many unnecessary LLM calls.
- Use structured tool outputs.
- Batch database queries where possible.

## 16. Agent Token Optimization Rules

1. Never send entire database tables to Granite.
2. Retrieve only relevant records.
3. Summarize large datasets before sending to Granite.
4. Use structured JSON.
5. Keep tool descriptions short and precise.
6. Give each agent only relevant tools.
7. Avoid repeated tool calls.
8. Cache stable results.
9. Perform arithmetic outside the LLM.
10. Perform filtering/sorting outside the LLM.
11. Perform forecasting outside the LLM.
12. Ask Granite primarily for intent interpretation and final explanation.
13. Use deterministic workflows whenever the path is known.
14. Set maximum agent iterations.
15. Log token usage and latency if available.

## 17. Development Rules for the AI Coding Agent

You are a senior full-stack + AI engineer working on KrishiLink AI.

Before writing code:
1. Inspect the existing project structure.
2. Identify what is already implemented.
3. Do not overwrite working code unnecessarily.
4. Follow existing conventions.
5. Implement one phase/module at a time.
6. Keep backend and frontend contracts synchronized.
7. Write testable functions.
8. Avoid unnecessary dependencies.
9. Never add a technology without a clear reason.
10. Keep configuration in environment variables.
11. Never hard-code secrets.
12. Never hard-code fake final recommendations.
13. Clearly mark mock/demo data when real data is unavailable.
14. Maintain API documentation.
15. Maintain a clear README.
16. Run relevant tests/build checks after implementation.
17. Report exactly what changed and what remains.

## 18. MVP Development Order

Follow this exact priority unless explicitly changed:

1. Project setup + Git + environments
2. Django + DRF + PostgreSQL/PostGIS
3. Authentication + Farmer profile
4. Crop Lot CRUD
5. Market + MarketPrice models
6. Market data ingestion/mock ingestion abstraction
7. Market price APIs
8. Market comparison
9. Transport and net-profit calculation tools
10. Historical price analytics
11. Price forecasting
12. SELL/HOLD/PARTIAL SELL engine
13. Agent/tool orchestration
14. IBM Granite integration
15. Farmer dashboard
16. End-to-end testing
17. Demo hardening

Do NOT begin advanced buyer/credit/fraud/traceability features before these steps work.

## 19. MVP Acceptance Criteria

The MVP is complete only when:
- A farmer can register and log in.
- A farmer can create a Cotton or Groundnut crop lot.
- The system displays valid current market data.
- The system compares multiple relevant markets.
- The system calculates transport-adjusted net value.
- The system displays historical price movement.
- The system generates a short-term forecast.
- The system produces SELL/HOLD/PARTIAL SELL.
- The recommendation is reproducible from stored inputs and deterministic rules.
- Granite provides a clear explanation based only on structured backend results.
- Granite cannot change numerical market/financial values.
- Errors and missing data produce graceful fallback messages.
- Protected APIs enforce authentication and authorization.
- The complete workflow can be demonstrated from login -> crop lot -> analysis -> recommendation.

## 20. Hackathon Demo Strategy

Ideal demo scenario:

A farmer has Groundnut, 40 quintals, near Gondal, and asks:

> "Where should I sell and should I sell now or wait?"

The system demonstrates:
1. Current market prices
2. Nearby market comparison
3. Historical trend
4. Forecast
5. Transport cost
6. Net value
7. Sell/Hold recommendation
8. Evidence
9. Granite explanation

The judge should understand the value without needing to inspect the code.

## 21. Product Differentiator

The key principle is:

> **Highest price is not always highest profit.**

KrishiLink AI provides:

> **Net-value-based, evidence-backed selling decisions.**

## 22. What NOT to Do

Do NOT:
- Build all 10 agents before MVP.
- Make every operation an LLM call.
- Let Granite generate arbitrary Python.
- Let Granite calculate financial values.
- Hard-code demo answers.
- Build a fake marketplace and call it real.
- Add banking integrations during MVP.
- Add WhatsApp/IVR before the core decision workflow works.
- Over-engineer microservices.
- Add unnecessary frameworks.
- Optimize raw API speed before functionality works.
- Spend most development time on UI animations.
- Build features that do not improve the core farmer decision.

## 23. Priority

**P0 — MVP:** Market intelligence + net-value calculation + forecasting + SELL/HOLD decision + Granite explanation.

**P1:** Quality + weather risk.

**P2:** Buyer marketplace.

**P3:** Trust + logistics + traceability.

**P4:** Government/finance/regulator ecosystem.

**P5:** Voice/WhatsApp/offline/multi-crop scale.

## 24. AI Agent Working Mode

When asked to implement something:
1. Identify which phase it belongs to.
2. Check dependencies.
3. Check whether MVP is complete.
4. Prefer incomplete P0 work over starting P1/P2.
5. Provide a short implementation plan.
6. Make the smallest safe change.
7. Test it.
8. Report files changed.
9. Report how to run/test it.
10. Do not silently redesign the architecture.

If a requested feature conflicts with MVP priority, explain the conflict and recommend the smallest compatible implementation.

## 25. North-Star Question

Every feature should answer:

> **"Does this help a cotton/groundnut farmer make a better selling decision, find a better buyer, reduce risk, or increase net income?"**

If NO, it is not an MVP priority.

---

# END OF KRISHILINK AI AGENT INSTRUCTIONS
