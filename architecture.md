# KrishiLink AI — Architecture Document

**Version:** 0.1 (Initial)
**Date:** 2025-07-14
**Status:** Pre-implementation — designed from project instructions

---

## 1. System Overview

KrishiLink AI is an AI-powered cotton and groundnut market intelligence and decision platform for Gujarat farmers. It combines real-time market data, deterministic financial calculations, ML-based price forecasting, and IBM Granite natural-language explanations to recommend SELL / HOLD / PARTIAL SELL for a farmer's crop lot.

```
Farmer → React UI → Django REST API → Decision Pipeline → IBM Granite → Dashboard
                                             ↕
                                       PostgreSQL
                                             ↕
                                      Background Jobs
                                     (Celery + Redis)
```

---

## 2. Architecture Principles

1. **LLM for reasoning and language. Python for computation. PostgreSQL for data. Agents for orchestration.**
2. Granite never performs deterministic calculations or generates arbitrary Python/SQL.
3. All numerical results shown to farmers originate from backend tools.
4. Every agent receives only the tools it needs (minimum-privilege tool access).
5. All calculations are deterministic and auditable (same inputs → same result).
6. Stale, mock, or demo data is always clearly labelled.
7. System degrades gracefully when Granite or external services are unavailable.

---

## 3. Repository / Monorepo Structure (Target)

```
krishisetu/
├── backend/                    # Django project
│   ├── krishilink/             # Django project settings package
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── accounts/           # User + FarmerProfile
│   │   ├── crops/              # CropLot
│   │   ├── markets/            # Market + MarketPrice
│   │   ├── forecasting/        # Forecast models + ML services
│   │   ├── decisions/          # SELL/HOLD engine + Recommendation
│   │   ├── agents/             # IBM Granite + tool orchestration
│   │   └── common/             # Shared utilities, validators, mixins
│   ├── tools/                  # Deterministic tool functions (called by agents)
│   │   ├── market_tools.py
│   │   ├── forecast_tools.py
│   │   ├── financial_tools.py
│   │   ├── farmer_tools.py
│   │   └── logistics_tools.py
│   ├── tasks/                  # Celery tasks
│   │   ├── market_data_tasks.py
│   │   └── forecast_tasks.py
│   ├── tests/                  # Test suite
│   ├── manage.py
│   └── requirements.txt
├── frontend/                   # React + Vite application
│   ├── src/
│   │   ├── api/                # Axios clients + React Query hooks
│   │   ├── components/         # Shared UI components
│   │   ├── context/            # AuthContext, useAuth hook
│   │   ├── pages/              # Page-level components
│   │   │   ├── Auth/
│   │   │   ├── Dashboard/
│   │   │   ├── FarmerProfile/
│   │   │   ├── CropLot/
│   │   │   ├── Market/
│   │   │   └── Analysis/
│   │   ├── styles/             # global.css (CSS custom properties)
│   │   └── main.jsx
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── scripts/
│   └── seed_data.py
├── architecture.md             # This file
├── project_status.md
└── README.md
```

---

## 4. Backend Architecture (Django + DRF)

### 4.1 Django Apps

| App | Responsibility |
|-----|---------------|
| `accounts` | User registration, JWT auth, FarmerProfile CRUD |
| `crops` | CropLot CRUD, commodity validation |
| `markets` | Market registry, MarketPrice ingestion, price APIs |
| `forecasting` | ML model wrappers, Forecast storage, trend analytics |
| `decisions` | Financial engine, SELL/HOLD/PARTIAL SELL, Recommendation |
| `agents` | IBM Granite client, orchestrator, tool registry |
| `common` | Pagination, validation mixins, error formatters |

### 4.2 URL Structure

```
/api/v1/
├── auth/
│   ├── register/
│   ├── login/
│   ├── refresh/
│   └── me/
├── farmer/
│   └── profile/
├── crops/
│   └── lots/
├── markets/
│   ├── list/
│   ├── prices/
│   ├── compare/
│   └── history/
├── forecast/
│   └── {commodity}/
├── decisions/
│   └── analyze/{crop_lot_id}/
└── admin/
```

### 4.3 Authentication

- JWT (djangorestframework-simplejwt)
- Access token: 60 min
- Refresh token: 7 days
- Rotate refresh tokens + blacklist after rotation
- Role-based: `farmer` | `admin` | `buyer`
- Object-level ownership: farmers can only access their own crop lots and recommendations

---

## 5. Database Architecture (PostgreSQL + PostGIS)

### 5.1 Core Models

```
User (AbstractUser extension)
  └── FarmerProfile (OneToOne)
        └── CropLot (ForeignKey)
              └── Recommendation (ForeignKey)

Market
  └── MarketPrice (ForeignKey)
  └── Forecast (ForeignKey)
```

### 5.2 Model Specifications

**User**
```
id, username, email, phone, role (farmer|admin|buyer),
password_hash, is_active, created_at, updated_at
```

**FarmerProfile**
```
id, user (OneToOne), district, taluka, village,
latitude (decimal), longitude (decimal),
pincode, created_at, updated_at
```

**CropLot**
```
id, farmer (FK→FarmerProfile), commodity (cotton|groundnut),
variety (nullable), quantity (decimal), unit (quintal|kg|tonne),
moisture_percent (decimal, nullable), quality_grade (A|B|C, nullable),
harvest_date (date), storage_status (farm|warehouse|cold_storage),
storage_start_date (date, nullable), notes (text),
is_active (bool), created_at, updated_at
```

**Market**
```
id, name, district, taluka, latitude, longitude,
market_type (APMC|private), state (GJ default),
is_active (bool), created_at
```

**MarketPrice**
```
id, market (FK), commodity, variety (nullable),
min_price, max_price, modal_price (decimal, Rs/quintal),
arrival_quantity (decimal, nullable), price_date (date),
source (agmarknet|manual|mock), source_timestamp,
is_verified (bool), created_at
```

**Forecast**
```
id, commodity, market (FK, nullable — statewide forecasts allowed),
forecast_date (date), predicted_price (decimal),
lower_bound (decimal), upper_bound (decimal),
confidence_score (0–1), model_name, model_version,
horizon_days (int), generated_at, is_mock (bool)
```

**Recommendation**
```
id, crop_lot (FK), best_market (FK→Market, nullable),
recommendation (SELL_NOW|HOLD|PARTIAL_SELL),
current_net_value (decimal), expected_future_net_value (decimal),
sell_quantity_suggestion (decimal, nullable),
confidence (0–1), reasoning_factors (JSONField),
rule_version, generated_at, granite_explanation (text)
```

### 5.3 PostGIS Usage

- `FarmerProfile.location` → `PointField` (latitude/longitude)
- `Market.location` → `PointField`
- Used for `find_nearest_markets()` spatial queries
- Required when comparing transport distances

---

## 6. Tool Layer (Deterministic Python Functions)

All tools live in `backend/tools/`. They are the single source of truth for calculations. Agents may only call tools from the allow-list; they may not generate raw Python or SQL.

### 6.1 Market Tools (`market_tools.py`)

| Tool | Inputs | Output |
|------|--------|--------|
| `get_latest_market_price(commodity, market_id)` | commodity, market_id | `{min, max, modal, date, source}` |
| `get_market_price_history(commodity, market_id, days)` | commodity, market_id, days | list of price records |
| `get_nearby_markets(lat, lon, radius_km, commodity)` | lat, lon, radius_km, commodity | list of markets with distance |
| `compare_market_prices(commodity, market_ids)` | commodity, list of market_ids | ranked comparison with transport stub |
| `calculate_price_change(commodity, market_id, days)` | commodity, market_id, days | `{change_pct, trend}` |
| `detect_price_anomaly(commodity, market_id)` | commodity, market_id | `{is_anomaly, reason}` |

### 6.2 Financial Tools (`financial_tools.py`)

| Tool | Inputs | Output |
|------|--------|--------|
| `calculate_transport_cost(origin_lat, origin_lon, market_id, quantity_quintal)` | coordinates, market_id, qty | `{distance_km, cost_rs, cost_per_quintal}` |
| `calculate_market_revenue(modal_price, quantity)` | modal_price, qty | `{gross_revenue}` |
| `calculate_net_value(gross, transport_cost)` | gross, transport | `{net_value, net_per_quintal}` |
| `calculate_storage_cost(storage_type, days, quantity)` | type, days, qty | `{total_cost, cost_per_quintal_per_day}` |
| `calculate_expected_future_value(forecast_price, quantity, transport, storage_days)` | all inputs | `{expected_net_value, breakdown}` |
| `calculate_roi(current_net, expected_future_net, holding_days)` | values | `{roi_pct, annualized_roi}` |
| `recommend_sell_or_hold(current_net_value, expected_future_net_value, risk_factor)` | values | `{recommendation, margin, reasoning}` |
| `calculate_partial_sell_strategy(quantity, current_net, expected_future_net)` | values | `{sell_qty, hold_qty, rationale}` |

### 6.3 Forecast Tools (`forecast_tools.py`)

| Tool | Inputs | Output |
|------|--------|--------|
| `generate_price_forecast(commodity, market_id, horizon_days)` | commodity, market_id, horizon | `{predictions, confidence_band, model}` |
| `calculate_price_trend(commodity, market_id, days)` | commodity, market_id, days | `{trend_direction, slope, r2}` |
| `get_forecast_confidence(commodity, market_id)` | commodity, market_id | `{confidence_score, data_points}` |

### 6.4 Farmer Tools (`farmer_tools.py`)

| Tool | Inputs | Output |
|------|--------|--------|
| `get_farmer_profile(user_id)` | user_id | FarmerProfile dict |
| `get_crop_lot(crop_lot_id)` | crop_lot_id | CropLot dict |
| `create_crop_lot(farmer_id, data)` | farmer_id, validated data | created CropLot |
| `get_farmer_inventory(farmer_id)` | farmer_id | list of active CropLots |

---

## 7. ML / Forecasting Architecture

### 7.1 Models

**Baseline — Linear Regression / Moving Average**
- Simple, fast, explainable
- Used as fallback when insufficient data

**Primary — Prophet (by Meta) or ARIMAX / SARIMA**
- Handles seasonality in agricultural prices
- Statsmodels SARIMAX as first candidate (no extra dependencies)
- Can upgrade to Prophet or LightGBM later

**Feature inputs for ML models:**
- Historical modal prices (primary)
- Arrival quantities (where available)
- Seasonal dummy variables
- Day-of-week / month features
- (Post-MVP) Weather data, MSP notifications

### 7.2 Training / Inference Pipeline

```
MarketPrice (PostgreSQL)
    → Pandas DataFrame
    → Feature engineering
    → SARIMAX / LinearRegression fit
    → Predictions + confidence intervals
    → Forecast table (PostgreSQL)
```

- Forecasts run as Celery background tasks
- Cached in DB; fresh forecast generated if > 24 hours stale
- Model version tracked in Forecast table

---

## 8. Agent / Orchestration Architecture (MVP)

```
User Request (via API)
    ↓
Orchestrator (Python service, NOT LLM)
    ↓
Tool calls (deterministic):
    ├── Market Intelligence Service
    │     get_latest_market_price()
    │     get_nearby_markets()
    │     compare_market_prices()
    │     get_market_price_history()
    │
    ├── Forecast Service
    │     generate_price_forecast()
    │     calculate_price_trend()
    │
    └── Financial Decision Service
          calculate_transport_cost()
          calculate_net_value()
          calculate_storage_cost()
          calculate_expected_future_value()
          recommend_sell_or_hold()
    ↓
Structured JSON result bundle
    ↓
IBM Granite Advisory Agent
    (receives JSON context — no raw DB access)
    (explains recommendation in plain language)
    ↓
Recommendation stored + returned to frontend
```

**The Orchestrator is deterministic Python, not LLM-driven, for the MVP.** IBM Granite is only invoked once at the end to generate a natural-language explanation from a structured JSON context bundle.

---

## 9. IBM Granite Integration

### 9.1 Role

- Natural-language explanation of SELL/HOLD/PARTIAL SELL recommendation
- Translates numbers into farmer-friendly narrative
- Supports Gujarati/Hindi/English responses
- Does NOT have direct database access
- Does NOT generate Python or SQL
- Does NOT calculate financial values

### 9.2 Input to Granite (structured context bundle)

```json
{
  "farmer": { "village": "Gondal", "district": "Rajkot" },
  "crop_lot": { "commodity": "groundnut", "quantity": 40, "unit": "quintal" },
  "market_comparison": [
    { "market": "Gondal APMC", "modal_price": 5800, "net_value": 228400, "distance_km": 12 },
    { "market": "Rajkot APMC", "modal_price": 5950, "net_value": 231100, "distance_km": 30 }
  ],
  "forecast": {
    "horizon_days": 14, "predicted_price": 6100,
    "confidence": 0.72, "trend": "upward"
  },
  "recommendation": {
    "action": "HOLD", "current_net_value": 231100,
    "expected_future_net_value": 240500, "margin": 9400
  },
  "language": "gujarati"
}
```

### 9.3 Granite Model

- IBM Granite 13B Instruct (or IBM Granite 3.x when available on IBM Cloud)
- IBM watsonx.ai API endpoint
- API key stored in environment variable
- Graceful fallback: return a template-based explanation if Granite is unavailable

---

## 10. Frontend Architecture (React + Vite)

### 10.1 Page Structure

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Auth/Login | JWT login — Phase 1 ✅ |
| `/register` | Auth/Register | Farmer registration — Phase 1 ✅ |
| `/dashboard` | Dashboard | Farmer overview, quick actions — Phase 1 ✅ |
| `/farmer/profile` | FarmerProfile | Location profile GET/PATCH — Phase 1 ✅ |
| `/crop-lots/new` | CropLot/Create | Create new crop lot — Phase 2 |
| `/crop-lots` | CropLot/List | Lot listing — Phase 2 |
| `/analysis/:cropLotId` | Analysis/Main | Full decision analysis — Phase 8 |
| `/markets` | Market/List | Market price browser — Phase 3 |

### 10.2 Key Components

- `PriceChart` — Recharts line chart for historical + forecast prices
- `MarketComparisonTable` — table with net-value-ranked markets
- `RecommendationCard` — SELL/HOLD/PARTIAL SELL with evidence
- `AIExplanationCard` — Granite-generated narrative
- `CropLotCard` — summary card for a crop lot
- `TransportCostBreakdown` — financial breakdown component

### 10.3 Auth Architecture

```
AuthContext (context/AuthContext.jsx)
  ├── login(email, password) → stores tokens in localStorage
  ├── register(payload)      → registers + auto-logs in
  ├── logout()               → clears tokens + user state
  └── rehydrate on mount     → fetchMe() if access_token exists

ProtectedRoute → redirects to /login if not authenticated
PublicRoute    → redirects to /dashboard if already authenticated
```

### 10.4 Data Fetching

- React Query for server state (cache, background refetch, loading/error states)
- Axios instance with JWT header injection + auto-refresh on 401
- Optimistic UI for crop lot creation

---

## 11. Background Jobs (Celery + Redis)

| Task | Trigger | Schedule |
|------|---------|----------|
| `fetch_market_prices` | Scheduled | Every 6 hours (or when data source allows) |
| `generate_forecasts` | After price update | After each market price fetch |
| `expire_stale_recommendations` | Scheduled | Daily |

Redis is used as both Celery broker and result backend.

---

## 12. Data Flow — Full Analysis Request

```
1. Farmer logs in → JWT token
2. Farmer creates CropLot → stored in PostgreSQL
3. Farmer triggers "Analyze" on a crop lot
4. API receives request → validates farmer ownership
5. Orchestrator:
   a. get_farmer_profile() — lat/lon from farmer profile
   b. get_nearby_markets() — PostGIS query, top 5 markets
   c. get_latest_market_price() — for each nearby market
   d. compare_market_prices() — rank by net value
   e. calculate_transport_cost() — for each market
   f. calculate_net_value() — current best net value
   g. get_market_price_history() — last 90 days
   h. generate_price_forecast() — 14-day forecast
   i. calculate_price_trend()
   j. calculate_storage_cost()
   k. calculate_expected_future_value()
   l. recommend_sell_or_hold()
6. Structured JSON bundle assembled
7. IBM Granite called → natural language explanation
8. Recommendation stored in DB
9. Full result returned to frontend
10. React renders dashboard, charts, cards
```

---

## 13. Security Architecture

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT (simplejwt) — access 60min, refresh 7 days |
| Authorization | DRF permissions + object-level ownership |
| Password storage | Django PBKDF2 (default) |
| Input validation | DRF serializer validators + model constraints |
| SQL injection | Django ORM (parameterized) |
| Secrets | Environment variables (.env) / IBM Cloud Secrets Manager |
| Rate limiting | django-ratelimit on auth endpoints |
| Granite safety | Tool allow-list; Granite receives no DB access |
| Prompt injection | Structured JSON context (not raw user text) passed to Granite |
| Audit logging | Sensitive operations logged with user/timestamp |
| Token blacklist | simplejwt token_blacklist — invalidates rotated refresh tokens |

---

## 14. External Data Sources

| Source | Data | Status |
|--------|------|--------|
| Agmarknet API / data.gov.in | APMC market prices | Phase 0: Mock data → Phase 3: Real integration |
| OpenRouteService / OSRM | Distance / route calculation | Phase 4: Transport tool |
| OpenWeatherMap / IMD | Weather risk | Phase 2 (Post-MVP) |

**All mock/demo data must be clearly flagged with `is_mock: true` and `source: "mock"` in the database and API responses.**

---

## 15. Deployment Architecture (Target)

```
IBM Cloud
├── IBM Kubernetes Service (IKS) or Code Engine
│   ├── backend containers (Django + Gunicorn)
│   ├── frontend container (Nginx + React build)
│   ├── Celery worker containers
│   └── Redis (IBM Databases for Redis or self-managed)
├── IBM Databases for PostgreSQL (with PostGIS extension)
├── IBM watsonx.ai (IBM Granite model endpoint)
└── IBM Cloud Object Storage (static assets, ML model artifacts)
```

**Development:** Docker Compose locally with all services.

---

## 16. MVP Component Map

| # | Component | App | Priority | Status |
|---|-----------|-----|----------|--------|
| 1 | Project scaffold | — | P0 | ✅ Done |
| 2 | Django settings, Docker, env | — | P0 | ✅ Done |
| 3 | User model + JWT auth | accounts | P0 | ✅ Done |
| 4 | FarmerProfile CRUD | accounts | P0 | ✅ Done |
| 5 | Login + Register UI | frontend | P0 | ✅ Done |
| 6 | Dashboard UI | frontend | P0 | ✅ Done |
| 7 | FarmerProfile UI | frontend | P0 | ✅ Done |
| 8 | CropLot CRUD | crops | P0 | ⚙️ Scaffolded |
| 9 | Market + MarketPrice models | markets | P0 | ⚙️ Scaffolded |
| 10 | Mock market data seeder | markets | P0 | ❌ Pending |
| 11 | Market price APIs | markets | P0 | ⚙️ Scaffolded |
| 12 | Nearby market discovery | markets | P0 | ⚙️ Scaffolded |
| 13 | Transport cost tool | tools | P0 | ✅ Done |
| 14 | Net value calculation | tools | P0 | ✅ Done |
| 15 | Historical price analytics | markets | P0 | ❌ Pending |
| 16 | Price forecasting (SARIMAX) | forecasting | P0 | ⚙️ Scaffolded |
| 17 | SELL/HOLD/PARTIAL SELL engine | decisions | P0 | ⚙️ Scaffolded |
| 18 | IBM Granite advisory | agents | P0 | ⚙️ Stub |
| 19 | Orchestrator service | agents | P0 | ❌ Pending |
| 20 | CropLot UI | frontend | P0 | ❌ Pending |
| 21 | Analysis/Dashboard UI | frontend | P0 | ❌ Pending |
| 22 | Price charts (Recharts) | frontend | P0 | ❌ Pending |
| 23 | End-to-end integration test | tests | P0 | ❌ Pending |

---

## 17. Phased Implementation Plan

### PHASE 0 — Project Setup ✅ Complete
- Git structure, monorepo layout
- Django project + app scaffolding
- PostgreSQL + PostGIS Docker
- Redis Docker
- Environment variables (.env)
- Base settings (dev/prod split)
- `requirements.txt`
- React + Vite scaffold

### PHASE 1 — Authentication ✅ Complete
- Custom User model with role
- JWT auth endpoints (register, login, refresh, me)
- FarmerProfile model + serializer + API
- 29 auth integration tests passing
- Login UI (functional form)
- Register UI (functional form + password strength)
- Dashboard UI (welcome, quick actions)
- FarmerProfile UI (GET/PATCH form)
- AuthContext + route guards

### PHASE 2 — Farmer + Crop Lots (Next)
- CropLot API integration tests
- Ownership enforcement tests
- CropLot create/list UI

### PHASE 3 — Market Intelligence
- Market model + seeder (Gujarat APMCs)
- MarketPrice model + seeder (mock historical data)
- Price list, history, nearby APIs
- Market comparison tool

### PHASE 4 — Financial Engine
- `financial_tools.py` connected to decision views
- Market comparison API with net value

### PHASE 5 — Forecasting
- `forecast_tools.py`: SARIMAX or linear trend
- Forecast model + storage + API
- Celery task for background re-forecasting

### PHASE 6 — SELL/HOLD Decision
- `recommend_sell_or_hold()` engine wired to API
- `calculate_partial_sell_strategy()`
- Recommendation model + API

### PHASE 7 — IBM Granite
- IBM watsonx.ai client wrapper
- Prompt template + structured context assembly
- Fallback template explanation
- Gujarati/Hindi/English support

### PHASE 8 — Orchestrator
- `AnalysisOrchestrator` service class
- Full pipeline: market → forecast → financial → decision → Granite
- Full analysis endpoint (`/api/v1/decisions/analyze/{crop_lot_id}/`)
- Integration tests

### PHASE 9 — React Dashboard
- Auth pages (Login, Register) ✅ Done
- Farmer Dashboard ✅ Done
- FarmerProfile ✅ Done
- CropLot create/list
- Analysis page (charts, comparison, recommendation, AI explanation)
- Price charts (Recharts)
- Leaflet map for market comparison

### PHASE 10 — Integration + Testing + Demo Hardening
- End-to-end flow test
- Error state handling
- Loading states
- Demo seed data (Gondal farmer, groundnut, 40 quintals)
- API documentation
- project_status.md final update

---

*Architecture authored by: IBM Bob / KrishiLink AI Lead Architect*
*Last updated: 2025-07-14*
