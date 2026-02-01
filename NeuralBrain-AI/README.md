# NeuralBrain-AI: Zero-Cost AI Health Monitoring Platform

---

## Overview

**NeuralBrain-AI** is a competition-grade health monitoring platform designed to demonstrate production-ready AI architecture with **zero operating costs**. The system ingests health data from free public APIs, processes it through intelligent services, and exposes it via a professional REST API and web dashboard.

### Key Features

✅ **Zero-Cost Operation** - Uses only free, public APIs with no paid subscriptions  
✅ **Production-Ready Architecture** - Enterprise-level code quality and design patterns  
✅ **Modular Services** - Decoupled components for easy extension  
✅ **REST API** - Complete API for programmatic access  
✅ **Professional UI** - Modern Bootstrap 5 dashboard  
✅ **Local Deployment** - Full control without external dependencies  
✅ **Extensible Design** - Ready for future AI models and features  

---

## Technology Stack

### Backend
- **Python 3.10+** - Core language
- **Flask 2.3+** - Lightweight web framework
- **SQLAlchemy** - ORM for database access
- **Requests** - HTTP client library

### Frontend
- **HTML5** - Semantic markup
- **Bootstrap 5** - Responsive CSS framework (CDN)
- **Jinja2** - Template engine
- **Font Awesome** - Icon library

### Database
- **SUPABASE** - Lightweight, serverless database
- **JSON** - Backup format for raw data

### APIs
- **Disease.sh** - COVID-19 epidemiological data
- **Fake API** - Health profile data for testing

---

## Project Structure

```
NeuralBrain-AI/
├── app.py                      # Flask application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
│
├── models/
│   ├── __init__.py
│   └── database.py             # SQLAlchemy models
│
├── services/
│   ├── __init__.py
│   ├── ingestion.py            # Data fetching service
│   ├── normalization.py        # Data standardization
│   └── validation.py           # Data validation
│
├── routes/
│   ├── __init__.py
│   ├── api.py                  # REST API endpoints
│   └── views.py                # Web UI views
│
├── templates/
│   ├── base.html               # Base template (navbar, footer)
│   ├── index.html              # Dashboard
│   ├── data.html               # Data explorer
│   ├── about.html              # About page
│   ├── api_docs.html           # API documentation
│   └── errors/
│       ├── 404.html
│       ├── 500.html
│       └── 403.html
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom styling
│   └── js/
│       └── main.js             # Client-side utilities
│
└── data/
    ├── raw_data.json           # Ingested raw data
    ├── processed_data.json     # Normalized data
    └── neuralbrain.db          # SQLite database
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip package manager
- Virtual environment (recommended)

### Step 1: Clone Repository

```bash
cd NeuralBrain-AI-Hawei-Developer--Competition/NeuralBrain-AI
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

The `.env` file is pre-configured for development. Modify if needed:

```bash
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000
```

### Step 5: Initialize Database

```bash
python3 -c "from app import create_app; app = create_app(); app.app_context().push()"
```

### Step 6: Run Application

```bash
python3 app.py
```

The application will start at `http://localhost:5000`

---

## Usage

### Web Dashboard

**Dashboard** (`/`)
- System statistics and overview
- Data source information
- Manual ingestion trigger

**Data Explorer** (`/data`)
- Browse all ingested records
- Filter by source and status
- View record details

**API Documentation** (`/api-docs`)
- Complete API reference
- Endpoint specifications
- Example requests and responses

**About** (`/about`)
- Project information
- Technology stack
- Planned features

---

## REST API Endpoints

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### System Health
```
GET /api/status       # System status and configuration
GET /api/health       # Health check
```

#### Data Ingestion
```
POST /api/ingest      # Trigger data ingestion
GET /api/logs         # Get ingestion logs
```

#### Data Access
```
GET /api/data                 # Get normalized data (paginated)
GET /api/data/<id>            # Get specific record
POST /api/validate            # Validate health data
```

### Example Requests

**Ingest Data**
```bash
curl -X POST http://localhost:5000/api/ingest
```

**Get Data**
```bash
curl http://localhost:5000/api/data?source=covid19&limit=50
```

**Validate Metric**
```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"heart_rate": 72, "temperature": 37.5},
    "type": "single"
  }'
```

---

## Core Services

### Data Ingestion Service (`services/ingestion.py`)

Fetches health data from configured APIs with:
- Automatic retry with exponential backoff
- Timeout handling
- Error recovery
- JSON persistence

**Usage:**
```python
from services.ingestion import DataIngestionService

service = DataIngestionService()
result = service.ingest_all_sources()
```

### Data Normalization Service (`services/normalization.py`)

Standardizes data from multiple sources:
- Field mapping
- Type standardization
- Null handling
- Batch processing

**Usage:**
```python
from services.normalization import DataNormalizer

normalizer = DataNormalizer()
normalized = normalizer.normalize_record(raw_data, source='covid19')
```

### Data Validation Service (`services/validation.py`)

Validates health metrics:
- Range checking
- Type validation
- Batch validation
- Error reporting

**Usage:**
```python
from services.validation import DataValidator

validator = DataValidator()
is_valid, errors = validator.validate_record({'heart_rate': 72})
```

---

## Database Models

### HealthDataRecord
Stores normalized health data with fields:
- `id`, `data_source`, `raw_data`, `processed_data`
- `metrics`, `timestamp`, `last_updated`, `status`
- `validation_notes`

### IngestionLog
Tracks ingestion operations:
- `id`, `api_source`, `status`, `records_fetched`
- `records_processed`, `error_message`, `execution_time`
- `timestamp`, `details`

---

## Configuration

### config.py
Central configuration file containing:
- Flask settings
- Database configuration
- API credentials and endpoints
- Validation rules
- Session configuration

### Environment Variables
Load from `.env` file:
```
FLASK_ENV, FLASK_DEBUG, DATABASE_URL, SECRET_KEY
```

---

## Attribution

**This application MUST display the following attribution on all pages:**

> "Developed by Bitingo Josaphat JB"

The attribution appears in:
- Footer on every page
- About page metadata
- API response headers
- Configuration

---

## Future Enhancements (Roadmap)

### Phase 2: AI Models
- Disease prediction models
- Risk scoring engine
- Pattern analysis

### Phase 3: Advanced Analytics
- Interactive visualizations
- Trend analysis
- Comparative metrics

### Phase 4: Deployment
- Huawei Cloud integration
- Kubernetes deployment
- Scalability optimization

### Phase 5: Mobile & Integration
- Mobile app support
- Wearable device integration
- Third-party API consumers

---

## Code Quality

- ✅ Modular architecture with separation of concerns
- ✅ Comprehensive docstrings for all major functions
- ✅ Error handling and logging throughout
- ✅ Type hints in critical sections
- ✅ Configuration management (no hardcoded values)
- ✅ Professional naming conventions

---

## Logging

Configure logging in `app.py`:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Logs are output to console by default.

---

## Testing the Application

### Test Ingestion
```bash
curl -X POST http://localhost:5000/api/ingest
```

### Test Data Retrieval
```bash
curl http://localhost:5000/api/data
```

### Test Validation
```bash
curl -X POST http://localhost:5000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"data": {"heart_rate": 200}, "type": "single"}'
```

---

## Troubleshooting

### Issue: Database file not created
**Solution:** Ensure `data/` directory exists and is writable
```bash
mkdir -p data
chmod 755 data
```

### Issue: API requests timeout
**Solution:** Increase timeout in `config.py`
```python
API_TIMEOUT = 30  # seconds
```

### Issue: Port 5000 already in use
**Solution:** Change port in `.env`
```
FLASK_PORT=5001
```

---

## Performance Considerations

- **Database Indexing:** Indexes on `timestamp` and `data_source` for fast queries
- **Pagination:** API returns 100 records by default to prevent memory issues
- **Retry Logic:** Exponential backoff prevents API rate limiting
- **JSON Caching:** Raw data persisted to avoid repeated API calls

---

## Security Notes

⚠️ **Development Only:** This configuration is for development. For production:
1. Change `SECRET_KEY` in `.env`
2. Set `FLASK_DEBUG = False`
3. Use HTTPS
4. Implement authentication
5. Add CORS headers if needed
6. Use environment-specific configs

---

## Support & Documentation

- **API Docs:** Available at `/api-docs` endpoint
- **Source Code:** Fully documented with inline comments
- **Error Handling:** All errors logged and reported clearly

---

## License

MIT License - Free for educational and commercial use

---

## Author

**Bitingo Josaphat JB**  
*NeuralBrain-AI Project Lead*  
*2026*

---

## Acknowledgments

- Disease.sh API for COVID-19 data
- Bootstrap framework for UI components
- Flask community for web framework
- Python community for amazing libraries

---

**Welcome to NeuralBrain-AI! 🚀**

*Built with care for the Huawei Developer Competition 2026*
