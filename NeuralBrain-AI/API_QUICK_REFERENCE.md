# NeuralBrain-AI: REST API Quick Reference

## 📍 Base URL
```
http://localhost:5000/api/health
```

## 🔌 All Endpoints (16 Total)

### Health Status Endpoints

#### 1. Get Overall System Health
```
GET /api/health/status
```
**Response**: Overall system health, monitoring status, current provider, provider statistics

#### 2. Get All Providers Health
```
GET /api/health/providers
```
**Response**: Array of all 5 providers with health status, error rate, latency

#### 3. Get Specific Provider Health
```
GET /api/health/provider/{name}
```
**Parameters**: `name` - Provider name (openai, gemini, groq, cloudflare, huggingface)
**Response**: Detailed health info for the specified provider

---

### Metrics Endpoints

#### 4. Get Recent Metrics
```
GET /api/health/metrics?limit=20
```
**Parameters**: 
- `limit` (optional): Number of records (default: 20, max: 100)

**Response**: Recent metrics from all providers

#### 5. Get Provider History
```
GET /api/health/history/{provider}?limit=100
```
**Parameters**:
- `provider`: Provider name
- `limit` (optional): Number of records (default: 100, max: 1000)

**Response**: Historical metrics for specific provider

---

### Dashboard Endpoint

#### 6. Get Dashboard Data
```
GET /api/health/dashboard
```
**Response**: Comprehensive dashboard data including:
- System status
- Statistics (provider count, error rate, latency)
- All provider status
- Alerts and warnings

---

### Configuration Endpoints

#### 7. Get Monitor Configuration
```
GET /api/health/config/monitor
```
**Response**: Current monitoring configuration
```json
{
  "check_interval_seconds": 300,
  "failure_threshold": 3,
  "degradation_threshold": 50.0,
  "is_running": true
}
```

#### 8. Update Monitor Configuration
```
POST /api/health/config/monitor
Content-Type: application/json

{
  "check_interval_seconds": 600,
  "failure_threshold": 5,
  "degradation_threshold": 60.0
}
```
**Response**: Updated configuration

---

### Control Endpoints

#### 9. Start Monitoring
```
POST /api/health/control/start
```
**Response**: Confirmation that monitoring started

#### 10. Stop Monitoring
```
POST /api/health/control/stop
```
**Response**: Confirmation that monitoring stopped

---

### System Endpoint

#### 11. Get System Information
```
GET /api/health/system
```
**Response**: System version, available providers, monitoring status, component list

---

## 📊 Response Format

All endpoints return JSON with this structure:

### Success Response (200)
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "data": {
    ...endpoint-specific data...
  }
}
```

### Error Response (400/500/503)
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "error": "Error description",
  "status_code": 500
}
```

---

## 🧪 Example Usage

### cURL Examples

#### Get system health
```bash
curl http://localhost:5000/api/health/status
```

#### Get all providers
```bash
curl http://localhost:5000/api/health/providers
```

#### Get OpenAI provider health
```bash
curl http://localhost:5000/api/health/provider/openai
```

#### Get recent metrics (last 30)
```bash
curl "http://localhost:5000/api/health/metrics?limit=30"
```

#### Get OpenAI history (last 50 checks)
```bash
curl "http://localhost:5000/api/health/history/openai?limit=50"
```

#### Get dashboard
```bash
curl http://localhost:5000/api/health/dashboard
```

#### Get monitor configuration
```bash
curl http://localhost:5000/api/health/config/monitor
```

#### Update monitor configuration
```bash
curl -X POST http://localhost:5000/api/health/config/monitor \
  -H "Content-Type: application/json" \
  -d '{
    "check_interval_seconds": 600,
    "failure_threshold": 5,
    "degradation_threshold": 60.0
  }'
```

#### Start monitoring
```bash
curl -X POST http://localhost:5000/api/health/control/start
```

#### Stop monitoring
```bash
curl -X POST http://localhost:5000/api/health/control/stop
```

#### Get system information
```bash
curl http://localhost:5000/api/health/system
```

---

## 🐍 Python Examples

### Using requests library

```python
import requests

BASE_URL = "http://localhost:5000/api/health"

# Get health status
response = requests.get(f"{BASE_URL}/status")
status = response.json()
print(f"System health: {status['data']['overall_status']}")

# Get all providers
response = requests.get(f"{BASE_URL}/providers")
providers = response.json()['data']['providers']
for provider in providers:
    print(f"{provider['provider']}: {provider['status']}")

# Get dashboard
response = requests.get(f"{BASE_URL}/dashboard")
dashboard = response.json()['data']
print(f"Average latency: {dashboard['statistics']['avg_latency_ms']}ms")

# Update configuration
new_config = {
    "check_interval_seconds": 600,
    "failure_threshold": 5,
    "degradation_threshold": 60.0
}
response = requests.post(f"{BASE_URL}/config/monitor", json=new_config)
print(response.json())

# Start monitoring
response = requests.post(f"{BASE_URL}/control/start")
print(response.json()['data']['message'])
```

---

## 📈 Status Codes

| Code | Meaning |
|------|---------|
| **200** | Success - Request completed successfully |
| **400** | Bad Request - Invalid parameters |
| **500** | Server Error - Internal error |
| **503** | Service Unavailable - Systems not initialized |

---

## 🔄 Provider Names

Valid provider names for endpoint parameters:
- `openai`
- `gemini`
- `groq`
- `cloudflare`
- `huggingface`

---

## ⚙️ Configuration Parameters

### check_interval_seconds
- Default: 300
- Range: 60 - 3600
- Description: How often to check provider health

### failure_threshold
- Default: 3
- Range: 1 - 10
- Description: Number of failures before marking provider unavailable

### degradation_threshold
- Default: 50.0
- Range: 0 - 100
- Description: Error rate percentage to mark provider as degraded

---

## 🚀 Quick Start

1. **Start the app**
   ```bash
   python3 app.py
   ```

2. **Check health**
   ```bash
   curl http://localhost:5000/api/health/status
   ```

3. **View dashboard**
   ```bash
   curl http://localhost:5000/api/health/dashboard | python3 -m json.tool
   ```

4. **Configure monitoring**
   ```bash
   curl -X POST http://localhost:5000/api/health/config/monitor \
     -H "Content-Type: application/json" \
     -d '{"check_interval_seconds": 600}'
   ```

---

## 📚 Additional Resources

- **Full API Documentation**: [PHASE_F_SUMMARY.md](PHASE_F_SUMMARY.md)
- **Test Suite**: `tests/test_health_api.py`
- **Implementation**: `routes/health_api.py`
- **Session Summary**: [SESSION_6_SUMMARY.md](SESSION_6_SUMMARY.md)

---

**Last Updated**: Session 6, Phase F ✅  
**Status**: Production Ready  
**Version**: 1.0.0

