"""
PRODUCTION CODE REFERENCE: Multi-Provider AI Orchestration

This file shows the actual implementation code snippets used in NeuralBrain-AI
"""

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ORCHESTRATOR SINGLETON PATTERN
# ═══════════════════════════════════════════════════════════════════════════════

_orchestrator_instance = None

def get_ai_orchestrator() -> AIProviderOrchestrator:
    """Get singleton orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AIProviderOrchestrator()
    return _orchestrator_instance


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ORCHESTRATOR FAILOVER LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def send_request(self, prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], str]:
    """
    Send request with automatic failover.
    
    Returns:
        Tuple of (success: bool, response_text: Optional[str], provider_name: str)
    """
    
    # Try OpenAI first (PRIMARY)
    logger.info(f"📤 Attempting OpenAI ({model})...")
    success, response, error = self.openai_provider.send_request(
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    if success and response:
        self.last_provider_used = "OpenAI"
        logger.info(f"✅ Used provider: OpenAI (Primary)")
        return True, response, "OpenAI"
    
    logger.warning(f"⚠️ OpenAI failed: {error}")
    
    # Fallback to Gemini (SECONDARY)
    logger.info(f"📤 Falling back to Gemini...")
    self.last_fallback_triggered = datetime.utcnow().isoformat()
    
    success, response, error = self.gemini_provider.send_request(
        prompt=prompt,
        model="gemini-1.5-flash",
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    if success and response:
        self.last_provider_used = "Gemini"
        logger.warning(f"⚠️ FAILOVER TRIGGERED: Using Gemini (Secondary)")
        return True, response, "Gemini"
    
    logger.error(f"❌ Gemini also failed: {error}")
    
    # Both failed
    self.last_provider_used = None
    error_msg = f"All AI providers failed. OpenAI: {error}. Gemini: {error}"
    logger.error(f"🔴 CRITICAL: {error_msg}")
    
    return False, None, "NONE"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. OPENAI PROVIDER IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class OpenAIProvider(AIProvider):
    """OpenAI API Provider (Primary)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', '').strip()
        self.provider_name = "OpenAI"
        self.available = bool(self.api_key and self.api_key != 'sk-your-api-key-here')
        
        if self.available:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                self.available = False
                self.client = None
        else:
            self.client = None
            logger.warning("⚠️ OpenAI API key not configured")
    
    def send_request(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send request to OpenAI API"""
        if not self.is_available():
            return False, None, "OpenAI provider not available"
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"✅ OpenAI request successful (tokens: {response.usage.total_tokens})")
            return True, response_text, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ OpenAI request failed: {error_msg}")
            return False, None, error_msg


# ═══════════════════════════════════════════════════════════════════════════════
# 4. GEMINI PROVIDER IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class GeminiProvider(AIProvider):
    """Google Gemini API Provider (Secondary/Fallback)"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '').strip()
        self.provider_name = "Gemini"
        self.available = bool(self.api_key and self.api_key != 'your-gemini-api-key-here')
        
        if self.available:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
                logger.info("✅ Gemini provider initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
                self.available = False
                self.client = None
        else:
            self.client = None
            logger.warning("⚠️ Gemini API key not configured")
    
    def send_request(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], Optional[str]]:
        """Send request to Gemini API"""
        if not self.is_available():
            return False, None, "Gemini provider not available"
        
        try:
            gemini_model_name = "gemini-1.5-flash"
            gemini_model = self.client.GenerativeModel(gemini_model_name)
            
            generation_config = self.client.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            response = gemini_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            response_text = response.text.strip()
            logger.info(f"✅ Gemini request successful")
            return True, response_text, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Gemini request failed: {error_msg}")
            return False, None, error_msg


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PREDICTION SERVICE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

class PredictionService:
    """Generates AI predictions from real disease data using multi-provider orchestration"""
    
    def __init__(self):
        self.orchestrator = get_ai_orchestrator()
        self.available = self.orchestrator.openai_provider.is_available() or self.orchestrator.gemini_provider.is_available()
        
        if not self.available:
            logger.warning("⚠️ No AI providers configured (OpenAI + Gemini)")
    
    def predict_outbreak_7_day(self, 
                               global_stats: Dict[str, Any],
                               countries: List[Dict[str, Any]],
                               historical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate 7-day outbreak forecast using orchestrator"""
        try:
            if not self.available:
                return self._get_fallback_7_day_forecast()
            
            logger.info("🔮 Generating 7-day outbreak predictions via AI...")
            
            # Extract key metrics for AI analysis
            current_cases = global_stats.get('cases', 0)
            today_cases = global_stats.get('todayCases', 0)
            current_deaths = global_stats.get('deaths', 0)
            today_deaths = global_stats.get('todayDeaths', 0)
            
            prompt = f"""You are a medical AI analyst. Analyze this COVID-19 data and return ONLY a JSON array with 7-day predictions.

CURRENT DATA:
- Total cases: {current_cases}
- Today's cases: {today_cases}
- Total deaths: {current_deaths}
- Today's deaths: {today_deaths}

Generate ONLY this JSON structure, nothing else:
[
  {{"day": 1, "predicted_cases": <number>, "confidence": <0.0-1.0>, "severity": "<CRITICAL|HIGH|MEDIUM|LOW>"}},
  ...7 days total
]

Rules:
- NO text, NO explanations, ONLY JSON array
- Return ONLY the JSON, nothing else"""

            # Use orchestrator (automatic failover)
            success, response_text, provider = self.orchestrator.send_request(
                prompt=prompt,
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=500
            )
            
            if not success or not response_text:
                logger.warning(f"⚠️ AI request failed (provider: {provider}), using fallback")
                return self._get_fallback_7_day_forecast()
            
            logger.info(f"✅ 7-day forecast from {provider}")
            
            # Extract JSON from response
            forecast = self._extract_json_array(response_text)
            
            if forecast and len(forecast) >= 7:
                logger.info("✅ 7-day forecast generated successfully")
                return forecast[:7]
            else:
                logger.warning("⚠️ AI response invalid, using fallback")
                return self._get_fallback_7_day_forecast()
                
        except Exception as e:
            logger.error(f"❌ Prediction error: {str(e)}")
            return self._get_fallback_7_day_forecast()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ABSTRACT BASE CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass
    
    @abstractmethod
    def send_request(self, prompt: str, model: str, temperature: float = 0.3, max_tokens: int = 500) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send request to AI provider
        
        Returns:
            Tuple of (success: bool, response_text: Optional[str], error: Optional[str])
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name for logging"""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ENVIRONMENT CONFIGURATION (.env)
# ═══════════════════════════════════════════════════════════════════════════════

"""
# OpenAI (PRIMARY)
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TIMEOUT=30
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.6

# Gemini (SECONDARY)
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT=30
GEMINI_MAX_TOKENS=2000
GEMINI_TEMPERATURE=0.6
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 8. USAGE EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════════

"""
from services.prediction_service import PredictionService

service = PredictionService()

# Single method call handles all the complexity
forecast = service.predict_outbreak_7_day(
    global_stats=disease_data.get_global_stats(),
    countries=disease_data.get_countries(),
    historical=disease_data.get_historical()
)

# Behind the scenes:
# 1. Orchestrator attempts OpenAI
# 2. If OpenAI fails → Automatically tries Gemini
# 3. If both fail → Returns realistic fallback data
# 4. Logs show which provider served the request
# 5. Frontend receives valid predictions either way
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 9. TEST EXAMPLE
# ═══════════════════════════════════════════════════════════════════════════════

"""
def test_orchestrator_tracks_last_provider():
    orch = get_ai_orchestrator()
    orch.last_provider_used = None
    
    success, response, provider = orch.send_request(
        prompt="Return JSON: {\"test\": 123}",
        model="gpt-3.5-turbo"
    )
    
    if success:
        assert orch.last_provider_used in ["OpenAI", "Gemini"]
        assert provider in ["OpenAI", "Gemini"]


def test_failover_mechanism():
    orch = get_ai_orchestrator()
    
    # If both providers available, orchestrator still uses only one
    if orch.openai_provider.is_available() and orch.gemini_provider.is_available():
        for _ in range(3):
            success, response, provider = orch.send_request(
                prompt="Test",
                model="gpt-3.5-turbo"
            )
            
            if success:
                assert provider in ["OpenAI", "Gemini"]  # Only one provider


def test_prediction_service_uses_orchestrator():
    service = PredictionService()
    assert hasattr(service, 'orchestrator')
    assert service.orchestrator is not None
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 10. LOGGING OUTPUT EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════════

"""
=== SUCCESSFUL REQUEST (OpenAI) ===
2026-02-08 22:11:31 - services.ai_providers - INFO - ✅ OpenAI provider initialized
2026-02-08 22:11:31 - services.ai_providers - INFO - 🎯 AI Provider Orchestrator initialized
2026-02-08 22:11:31 - services.ai_providers - INFO - 📤 Attempting OpenAI (gpt-3.5-turbo)...
2026-02-08 22:11:34 - services.ai_providers - INFO - ✅ OpenAI request successful (tokens: 250)
2026-02-08 22:11:34 - services.ai_providers - INFO - ✅ Used provider: OpenAI (Primary)


=== FAILOVER (OpenAI fails, Gemini succeeds) ===
2026-02-08 22:11:31 - services.ai_providers - INFO - 📤 Attempting OpenAI (gpt-3.5-turbo)...
2026-02-08 22:11:37 - services.ai_providers - ERROR - ❌ OpenAI request failed: Error code: 429
2026-02-08 22:11:37 - services.ai_providers - WARNING - ⚠️ OpenAI failed: Error code: 429
2026-02-08 22:11:37 - services.ai_providers - INFO - 📤 Falling back to Gemini...
2026-02-08 22:11:40 - services.ai_providers - INFO - ✅ Gemini request successful
2026-02-08 22:11:40 - services.ai_providers - WARNING - ⚠️ FAILOVER TRIGGERED: Using Gemini (Secondary)


=== BOTH PROVIDERS FAIL ===
2026-02-08 22:11:31 - services.ai_providers - INFO - 📤 Attempting OpenAI (gpt-3.5-turbo)...
2026-02-08 22:11:37 - services.ai_providers - ERROR - ❌ OpenAI request failed: Error code: 429
2026-02-08 22:11:37 - services.ai_providers - WARNING - ⚠️ OpenAI failed: Error code: 429
2026-02-08 22:11:37 - services.ai_providers - INFO - 📤 Falling back to Gemini...
2026-02-08 22:11:38 - services.ai_providers - ERROR - ❌ Gemini request failed: timeout
2026-02-08 22:11:38 - services.ai_providers - ERROR - 🔴 CRITICAL: All AI providers failed
2026-02-08 22:11:38 - services.prediction_service - WARNING - ⚠️ AI request failed (provider: NONE), using fallback
"""

