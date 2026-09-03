# KrishiLink AI — AI Agent Project Instructions

## 1. Project Identity

**Project:** KrishiLink AI  
**Purpose:** AI-Powered Cotton & Groundnut Market Linkage and Decision-Intelligence Platform  
**Target:** Gujarat Hackathon 2026  
**Primary region:** Gujarat, with initial focus on Saurashtra / North Gujarat  
**Primary users:** Farmers, Buyers, Admin/Regulator  
**AI platform requirement:** IBM Granite + IBM Bob / agentic workflow + IBM Cloud

## 2. Core Problem

Cotton and groundnut farmers often lack timely, trustworthy market intelligence and bargaining power. They may know the current price but still make poor selling decisions because they do not know:
- Which nearby market gives the best NET value after transport costs.
- Whether prices are likely to rise or fall in the short term.
- Whether storing the crop is financially worthwhile.
- How crop quality affects expected value.
- Which buyers are suitable for their crop lot.
- How weather/storage risk changes the decision.

**Core promise:** Do not merely show farmers prices. Determine the best economic action for their crop lot and clearly explain why.

## 3. Golden MVP User Journey

1. Farmer registers/logs in.
2. Farmer creates a crop lot.
3. Farmer selects Cotton or Groundnut.
4. Farmer enters quantity, location and available quality information.
5. System obtains current market data.
6. System compares relevant markets.
7. System calculates transportation and net selling value.
8. System analyzes historical price movement.
9. System generates a short-term price forecast.
10. System calculates whether selling now or holding is financially better.
11. System produces SELL / HOLD / PARTIAL SELL recommendation.
12. IBM Granite explains the recommendation in simple language.
13. Farmer sees the result on a polished dashboard.

**This end-to-end flow is the highest priority.**

## 4. 80/20 MVP Principle

Do NOT implement the entire commercial platform initially.

### MVP MUST HAVE

**Farmer**
- Registration/login
- Farmer profile
- Crop-lot creation/listing
- Cotton and Groundnut support

**Market Intelligence**
- Current mandi prices
- Min/Max/Modal price
- Arrival quantity where available
- Historical price data
- Nearby market discovery
- Market comparison

**Financial Intelligence**
- Transport-cost calculation
- Current gross revenue
- Net revenue
- Storage-cost calculation
- Expected future value
- Basic ROI/net-benefit calculation

**Forecasting**
- Price trend
- Short-term forecast
- Confidence/uncertainty indicator
- Baseline model plus one stronger statistical/ML model

**Decision**
- SELL NOW
- HOLD
- PARTIAL SELL
- Evidence-backed recommendation
- Explicit reason/factors

**IBM Granite**
- Natural-language intent understanding
- Tool selection where needed
- Final explanation
- Gujarati/Hindi/English-ready architecture
- Granite must not invent numerical market values

**UI**
- Farmer dashboard
- Crop analysis page
- Price charts
- Market comparison table
- Recommendation card
- AI explanation card

## 5. Post-MVP Roadmap

### Phase 2 — Advanced Intelligence
- Quality & Valuation Agent
- Detailed crop grading
- Weather & Risk Agent
- Spoilage/storage risk
- Better forecasting
- Price anomaly detection

### Phase 3 — Buyer Marketplace
- Buyer registration/profile
- Buyer requirements
- Verified buyers
- Buyer matching
- Offer submission
- Buyer ranking
- Deal-room foundation
- Digital deal slip

### Phase 4 — Trust, Logistics & Traceability
- Buyer trust score
- Fraud/anomaly detection
- Advanced transport optimization
- QR crop-lot traceability
- Farm-to-buyer history

### Phase 5 — Ecosystem
- Government scheme matching
- MSP/procurement-window intelligence
- Indicative inventory financing
- Buyer demand analytics
- Regulator dashboard

### Phase 6 — Scale & Accessibility
- Gujarati/Hindi voice interface
- WhatsApp integration
- SMS/IVR
- Offline-first support
- More crops
- More districts/APMCs
- Production-scale optimization

## 6. Final Technology Stack

### Frontend
- React
- Vite
- JavaScript
- React Query
- Axios
- CSS Modules
- Recharts
- Leaflet

Do NOT use Tailwind unless explicitly requested.

### Backend
- Django
- Django REST Framework
- Django ORM
- JWT authentication
- DRF serializers/viewsets/routers
- Django Admin

### Database
- PostgreSQL
- PostGIS

### Background processing
- Celery
- Redis

Use Celery for long-running ML/agent jobs. Do not unnecessarily introduce asynchronous infrastructure for simple CRUD operations.

### Data / ML
- Python
- Pandas
- NumPy
- Scikit-learn
- Statsmodels
- XGBoost or LightGBM where useful

### AI
- IBM Granite
- IBM Bob / permitted IBM agentic orchestration
- IBM Cloud

### External data
- Agmarknet / appropriate government market-data source
- Weather API when Weather/Risk phase is implemented

### DevOps
- Git
- GitHub
- Docker
- IBM Cloud

## 7. Critical AI Architecture Principle

**LLM for reasoning and language. Python for computation. PostgreSQL for data. Agents for orchestration.**

NEVER make Granite perform deterministic calculations that the backend can perform.

Preferred flow:

`User -> Agent/Orchestrator -> deterministic tools -> structured JSON -> Granite explanation`

## 8. Token-Efficient Tool Architecture

Create deterministic Python tools.

### Market
- get_latest_market_price()
- get_market_price_history()
- get_market_arrivals()
- get_nearby_markets()
- compare_market_prices()
- calculate_price_change()
- detect_price_anomaly()

### Forecast
- generate_price_forecast()
- get_forecast_confidence()
- calculate_price_trend()

### Financial
- calculate_transport_cost()
- calculate_market_revenue()
- calculate_storage_cost()
- calculate_capital_cost()
- calculate_expected_future_value()
- calculate_net_profit()
- calculate_roi()
- recommend_sell_or_hold()
- calculate_partial_sell_strategy()

### Farmer
- get_farmer_profile()
- get_farmer_inventory()
- get_crop_lot()
- create_crop_lot()
- update_crop_lot()

### Quality
- calculate_quality_score()
- calculate_quality_grade()
- estimate_quality_price_adjustment()

### Buyer
- search_buyers()
- filter_buyers()
- rank_buyers()
- calculate_buyer_trust_score()

### Risk
- get_weather()
- calculate_weather_risk()
- calculate_spoilage_risk()

### Logistics
- calculate_distance()
- estimate_transport_cost()
- find_nearest_market()
- optimize_delivery_route()

## 9. Tool Design Rules

Every tool must:
1. Have one clear responsibility.
2. Accept structured input.
3. Return structured JSON/dictionary output.
4. Validate inputs.
5. Never depend on free-form LLM-generated code.
6. Never expose secrets.
7. Be independently unit-testable.
8. Return evidence/source timestamps where relevant.
9. Fail safely.
10. Have a clear description.

Do NOT expose all tools to every agent. Use agent-specific toolsets.

## 10. Agent Architecture

### MVP
Keep the architecture lean.

1. **Orchestrator / Decision Coordinator** — determines required tools/workflow.
2. **Market Intelligence Agent/Service** — current prices, history, comparison.
3. **Forecast Agent/Service** — trends and forecasts.
4. **Financial Decision Agent/Service** — transport, storage, net value, SELL/HOLD/PARTIAL SELL.
5. **Granite Advisory Agent** — farmer-friendly explanation.

The system may internally use Python services/tools instead of making every component an LLM-powered autonomous agent.

### Post-MVP agents
- Quality & Valuation Agent
- Weather & Risk Agent
- Buyer Matching Agent
- Logistics Agent
- Fraud & Trust Agent
- Government Scheme Agent

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
