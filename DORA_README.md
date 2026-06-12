# DORA Metrics Dashboard - Real-Time CI/CD Observability

A real-time implementation of the DevOps Research and Assessment (DORA) metrics using Flask, SQLAlchemy, and event-time processing.

## ✨ Features

✅ **4 DORA Metrics** - Deployment Frequency, Lead Time for Change, Change Failure Rate, Mean Time to Restore  
✅ **Event-Time Semantics** - Handles out-of-order events correctly using watermarks  
✅ **Real-Time Dashboard** - Beautiful, responsive UI with live metric cards  
✅ **REST API** - Ingest events via POST endpoints  
✅ **JSON API** - Query metrics programmatically  
✅ **Sample Data** - Pre-populated realistic CI/CD data  
✅ **Test Suite** - 9 comprehensive unit tests  

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd smart-incident-platform
pip install -r requirements.txt
```

### 2. Generate Sample Data
```bash
python sample_data.py
```

This creates 159 realistic pipeline events across 4 sample pipelines.

### 3. Start the App
```bash
python app.py
```

Visit http://localhost:5000/dora

### 4. Send Test Events
```bash
# Simulate a successful build & deploy
python test_client.py success my-pipeline run-001

# Simulate a failed build
python test_client.py failure my-pipeline run-002

# View current metrics
python test_client.py metrics
```

---

## 📊 DORA Metrics Explained

### 1. Deployment Frequency
**What it measures:** How often code reaches production  
**How it's calculated:** Count of `deploy_success` events / number of days  
**DORA Bands:**
- Elite: ≥ 1 per day
- High: ≥ 1 per week  
- Medium: ≥ 1 per month
- Low: < 1 per month

### 2. Lead Time for Change
**What it measures:** Time from code written to deployed in production  
**How it's calculated:** `deploy_success.event_time - build_start.event_time` (per run)  
**DORA Bands:**
- Elite: < 1 hour
- High: < 1 day
- Medium: < 1 week
- Low: ≥ 1 week

### 3. Change Failure Rate  
**What it measures:** % of deployments that caused failures or rollbacks  
**How it's calculated:** `(deploy_failure + rollback) / (deploy_success + deploy_failure + rollback) × 100`  
**DORA Bands:**
- Elite: ≤ 5%
- High: ≤ 10%
- Medium: ≤ 15%
- Low: > 15%

### 4. Mean Time to Restore
**What it measures:** Average time to fix a production incident  
**How it's calculated:** Average of `deploy_success.event_time - failure_event.event_time` (for each recovery)  
**DORA Bands:**
- Elite: < 1 hour
- High: < 1 day
- Medium: < 1 week
- Low: ≥ 1 week

---

## 🔌 API Usage

### Single Event Ingestion
```bash
curl -X POST http://localhost:5000/dora/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "my-service",
    "run_id": "run-123",
    "event_type": "deploy_success",
    "commit_hash": "abc123def456",
    "event_time": "2026-06-06T14:30:00"
  }'
```

### Bulk Event Ingestion
```bash
curl -X POST http://localhost:5000/dora/api/events/bulk \
  -H "Content-Type: application/json" \
  -d '[
    {"pipeline_id": "svc", "run_id": "run-1", "event_type": "build_start"},
    {"pipeline_id": "svc", "run_id": "run-1", "event_type": "build_success"},
    {"pipeline_id": "svc", "run_id": "run-1", "event_type": "deploy_success"}
  ]'
```

### Query Metrics
```bash
# Last 30 days (default)
curl http://localhost:5000/dora/api/metrics

# Custom time window
curl "http://localhost:5000/dora/api/metrics?start=2026-05-01T00:00:00&end=2026-06-06T23:59:59"
```

See [API_DOCS.md](API_DOCS.md) for complete integration examples.

---

## 📁 Project Structure

```
smart-incident-platform/
├── app.py                    # Flask app entry point
├── config.py                 # Configuration
├── extensions.py             # Shared db & login_manager (no circular imports)
│
├── models/
│   ├── user.py              # User model
│   ├── incident.py          # Incident model
│   └── pipeline_event.py    # PipelineEvent model (CI/CD events)
│
├── routes/
│   ├── auth.py              # Login/register routes
│   ├── incidents.py         # Incident management routes
│   └── dora.py              # DORA metrics routes & API
│
├── services/
│   └── dora_metrics.py      # DORA metric calculations
│
├── templates/
│   ├── base.html            # Base layout with modern CSS
│   ├── dashboard.html       # Main dashboard
│   ├── dora_dashboard.html  # DORA metrics dashboard
│   ├── incidents.html       # Incidents list
│   ├── create_incident.html # Create incident form
│   ├── login.html           # Login page
│   └── register.html        # Registration page
│
├── tests/
│   ├── test_incidents.py    # Incident tests
│   └── test_dora_metrics.py # DORA metric tests (9 tests)
│
├── sample_data.py           # Generate realistic CI/CD events
├── test_client.py           # CLI tool to test API
├── API_DOCS.md              # Detailed API documentation
└── requirements.txt         # Python dependencies
```

---

## 🧪 Testing

Run all DORA metric tests:
```bash
python -m pytest tests/test_dora_metrics.py -v
```

Run a specific test:
```bash
python -m pytest tests/test_dora_metrics.py::test_lead_time_out_of_order_event -v
```

**Note:** Tests include an important **out-of-order event test** that validates event-time semantics.

---

## 🎯 Key Design Decisions

### Event-Time Semantics
Instead of using ingestion time, the system uses `event_time` to calculate metrics. This handles distributed CI/CD pipelines where events may arrive out-of-order.

**Example:**
```
Events received in order:  deploy_success → build_success → build_start
Real event time order:     build_start → build_success → deploy_success

Lead time calculation uses real event times, not receipt order:
lead_time = deploy_success.event_time - build_start.event_time
```

### Circular Import Fix
The original code had `models/ → app → models` circular import. This was fixed by:
- Creating `extensions.py` to hold `db` and `login_manager`
- All models import from `extensions` instead of `app`
- `app.py` imports from `extensions` instead of creating these objects

### DORA Band Thresholds
Thresholds follow [DORA research](https://dora.dev) to classify teams into Elite/High/Medium/Low performers.

---

## 📈 Next Steps (Roadmap)

- [ ] Apache Kafka producer for Jenkins/GitHub Actions events
- [ ] Apache Flink stream processor for real-time metric updates
- [ ] Predictive anomaly detection with rule engine
- [ ] Historical trend charts and forecasting
- [ ] Slack/email alerting when metrics drop below thresholds
- [ ] Database migrations with Alembic
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests

---

## 🛠️ Valid Event Types

```
build_start       - Build started
build_success     - Build succeeded
build_failure     - Build failed

test_start        - Test suite started
test_pass         - All tests passed
test_fail         - Tests failed

deploy_start      - Deployment started
deploy_success    - Deployment succeeded
deploy_failure    - Deployment failed

rollback          - Rollback executed
```

---

## 📝 License

This implementation is part of the Smart Incident Management Platform research project.

---

## 🤝 Integration Examples

### Jenkins
See `API_DOCS.md` → Section 5.A for Jenkins pipeline integration.

### GitHub Actions
See `API_DOCS.md` → Section 5.B for GitHub Actions workflow integration.

### GitLab CI
See `API_DOCS.md` → Section 5.C for GitLab CI integration.

---

## 💡 Tips

1. **View Sample Data:** Run `sample_data.py` to auto-generate 159 realistic events
2. **Test API:** Use `test_client.py` to send events and see metrics update
3. **Custom Time Window:** Add `?start=...&end=...` to `/dora/api/metrics` endpoint
4. **Monitor Performance:** DORA metrics update in real-time as events are ingested
5. **Check Database:** Events are stored in SQLite (`incident.db`) — inspect with DB browser

---

**Questions?** Check `API_DOCS.md` for detailed endpoint documentation and integration patterns.
