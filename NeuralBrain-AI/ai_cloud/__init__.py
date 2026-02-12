"""
AI Cloud Services Module
========================

Real-data integration layer for NeuralBrain AI

Services:
- Huawei Cloud ModelArts (primary AI)
- Free Public Health APIs (secondary data)
- OpenAI (fallback intelligence)
- Data transformation & orchestration

All data is validated, transformed, and made compatible with frontend expectations.
"""

from .huawei_service import get_huawei_service
from .external_api_service import get_external_api_service
from .openai_service import get_openai_service
from .data_transformer import get_data_transformer
from .prediction_orchestrator import get_prediction_orchestrator

__all__ = [
    'get_huawei_service',
    'get_external_api_service', 
    'get_openai_service',
    'get_data_transformer',
    'get_prediction_orchestrator',
    'orchestrator',
    'external_api_service',
    'openai_service',
]

# Initialize singleton instances
orchestrator = get_prediction_orchestrator()
external_api_service = get_external_api_service()
openai_service = get_openai_service()

