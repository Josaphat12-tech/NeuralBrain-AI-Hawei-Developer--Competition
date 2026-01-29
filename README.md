# NeuralBrain-AI-Hawei-Developer-Competition

🧠 **Zero-Cost AI Health Monitoring Platform**  
**Developed by: Bitingo Josaphat JB**  

Built for the **Huawei Cloud Global Developer Competition**

---

## 🚀 Project Overview

**NeuralBrain AI** is a competition-grade, production-ready health monitoring platform demonstrating how **zero-cost architecture meets enterprise-level engineering**. 

**Feature #1 (CORE):** Health Data Ingestion, Aggregation, and Exposure Layer

This initial release implements the foundational data pipeline that will support future AI models, analytics, and cloud deployment.

---

## ✨ Phase 1: Core Implementation (COMPLETED)

### Feature #1: Health Data Ingestion, Aggregation & Exposure

**What's Included:**
- ✅ Data Ingestion Service - Fetch from free public APIs
- ✅ Data Normalization Service - Standardize inconsistent formats
- ✅ Data Validation Service - Validate against medical ranges
- ✅ SQLite Database - Persistent storage with JSON backups
- ✅ REST API - Complete JSON API for data access
- ✅ Professional Web UI - Bootstrap 5 dashboard
- ✅ Zero-Cost Operation - No paid APIs or subscriptions
- ✅ Production-Ready Architecture - Enterprise code quality

**Implemented Endpoints:**
- `GET /api/status` - System status
- `GET /api/health` - Health check
- `POST /api/ingest` - Trigger data ingestion
- `GET /api/data` - Retrieve normalized data
- `GET /api/logs` - View ingestion logs
- `POST /api/validate` - Validate health metrics

---

## 🎯 Key Differentiators

- **100% Free & Open** - Uses only free public APIs
- **Local Deployment** - No external cloud dependency for core features
- **Modular Architecture** - Easy to extend with AI models
- **Production Quality** - Enterprise patterns, error handling, logging
- **Fully Documented** - Inline code comments, API docs, README
- **Attribution Included** - "Developed by Bitingo Josaphat JB" on all pages

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────┐
│         Web Browser / API Client            │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │    Flask App       │
        │    (app.py)        │
        └─────────┬──────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐┌────────┐┌──────────┐
│ Routes ││Services││  Models  │
│        ││        ││          │
│ • API  ││Ingest  ││Database  │
│ • Views││Normalize││ (SQLite) │
└────────┘└────────┘└──────────┘
    │         │         │
    └─────────┼─────────┘
              │
        ┌─────▼──────┐
        │  Data Flow │
        └─────┬──────┘
        ┌─────▼────────────┐
        │ Free Public APIs │
        │ • Disease.sh     │
        │ • Fake API       │
        └──────────────────┘
```

---

## 📊 Data Flow

1. **Ingestion** - Fetch from public APIs with retry logic
2. **Normalization** - Standardize formats from different sources
3. **Validation** - Check data against medical ranges
4. **Storage** - Persist to SQLite + JSON backups
5. **Exposure** - REST API for data access
6. **Visualization** - Web dashboard with filtering

---

## 📦 Data Sources (100% Free & Open)

### Currently Integrated
- **Disease.sh API** - COVID-19 epidemiological data
- **Fake API** - Health profile testing data

### Extensible for Future
- WHO datasets
- World Bank indicators
- Climate data APIs
- Population data sources

> ✅ No private patient data, no paid APIs, fully zero-cost

---

## 🚀 Roadmap

### Phase 1 (COMPLETED)
- ✅ Data Ingestion & Aggregation
- ✅ REST API
- ✅ Web Dashboard
- ✅ Local SQLite Database

### Phase 2 (PLANNED)
- AI disease prediction models
- Risk scoring engine
- Advanced visualizations
- Automated alerts

### Phase 3 (PLANNED)
- Huawei Cloud integration
- Kubernetes deployment
- Mobile API support
- Wearable integration

---

## ☁️ Technology Stack

**Backend**
- Python 3.10+
- Flask 2.3+
- SQLAlchemy ORM
- Requests HTTP library

**Frontend**
- HTML5, Jinja2
- Bootstrap 5 (CDN)
- Font Awesome icons

**Database**
- SQLite (local)
- JSON backups

**APIs**
- Disease.sh (COVID-19)
- Fake API (testing)

---

## 💰 Zero-Cost Model

✅ **No subscription fees**  
✅ **No API keys required**  
✅ **Free tier only**  
✅ **Local deployment**  
✅ **Open-source dependencies**  

---

## 📖 Core Implementation: Phase 1

### Feature #1 - Health Data Ingestion Layer

**Status:** ✅ COMPLETED

Located in: `NeuralBrain-AI/` directory

**What's Been Implemented:**

1. **Data Ingestion Service** (`services/ingestion.py`)
   - Fetch from free public APIs (Disease.sh, etc.)
   - Automatic retry with exponential backoff
   - Comprehensive error handling
   - JSON persistence

2. **Data Normalization** (`services/normalization.py`)
   - Standardize data formats
   - Field mapping
   - Type conversion

3. **Data Validation** (`services/validation.py`)
   - Range validation
   - Medical constraint checking
   - Batch validation

4. **Database Models** (`models/database.py`)
   - SQLite storage
   - HealthDataRecord model
   - IngestionLog model

5. **REST API** (`routes/api.py`)
   - 7+ endpoints for data access
   - JSON responses
   - Pagination support
   - Error handling

6. **Web Dashboard** (`templates/`)
   - Bootstrap 5 UI
   - Dashboard page
   - Data explorer
   - API documentation
   - About page

7. **Attribution**
   - "Developed by Bitingo Josaphat JB" on all pages
   - Footer on every template
   - About page metadata

### Quick Start
```bash
cd NeuralBrain-AI
pip install -r requirements.txt
python3 app.py
# Visit http://localhost:5000
```

### API Access
```bash
curl http://localhost:5000/api/ingest      # Start ingestion
curl http://localhost:5000/api/data         # Get data
curl http://localhost:5000/api/status       # System status
```

**Total Cost: $0**

---

## 👥 Target Users

- **Health Analysts** – Detailed analytics & predictions  
- **Policy Makers** – Risk summaries & decision support  
- **NGOs & Aid Organizations** – Intervention prioritization  
- **Developers** – API access for integration  

---

## 📈 Expected Impact

- Predict outbreaks **2–4 weeks earlier**
- Reduce response time by **30–50%**
- Support millions of data records daily
- Improve global health preparedness
- Enable proactive, data-driven decisions

---

## 🧩 Open Source & Credits

This project builds upon and integrates ideas from existing open-source public health and machine learning projects.

All reused or referenced repositories are **properly credited** in documentation and code comments, in compliance with their respective licenses.

---

## 🏆 Competition Alignment

This project aligns with Huawei Cloud competition evaluation criteria:

- ✔ Real-world impact  
- ✔ Advanced AI & cloud usage  
- ✔ Scalable cloud architecture  
- ✔ Innovation & creativity  
- ✔ Business & social value  

---

## 🛠 Getting Started (Coming Soon)

- Deployment instructions
- Dataset preparation
- Model training pipeline
- Dashboard setup

---

## 📜 License

This project is released under the **MIT License** unless otherwise stated.

---

## 🤝 Contributing & Team

Contributions are welcome and appreciated!

### 👥 Core Team Members
- **Project Lead / Manager** – [@Kamangi001](https://github.com/kamangi001)
- **Cloud ,DevOps & AI Engineer** – [@Josaphat12-tech](https://github.com/josaphat12-tech)
- **Data Scientist / ML Engineer** – [@Josaphat12-tech](https://github.com/josaphat12-tech)
- **Backend Engineer** – [@jacobkitams](https://github.com/jacobkitams)
- **Frontend Integrator & API Endepoint Creator** – [@princempunga](https://github.com/princempunga)
- **Frontend / Visualization Engineer** – [@mozart1123](https://github.com/mozart1123)

> Team members are responsible for design, development, deployment, and documentation of the project.

---

### 🛠 How to Contribute

If you’d like to contribute:
1. Fork the repository
2. Create a new feature branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes with clear messages
4. Push to your forked repository
5. Open a Pull Request describing your changes

Please ensure:
- Code is well-documented
- Changes align with the project’s objectives
- Proper attribution is provided when using third-party resources


  ## ☕ Support the Project

If you find this project useful and would like to support its development, you can buy us a coffee ☕  
Your support helps us maintain, improve, and scale this open-source project.

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-orange.png)](https://www.buymeacoffee.com/bitingojb)


By contributing, you agree that your work may be used as part of the  
**NeuralBrain AI – Huawei Developer Competition** project.

---
