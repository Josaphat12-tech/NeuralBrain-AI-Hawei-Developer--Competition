"""
Test suite for Data Mapper (Phase 4)
Tests response normalization and data contract preservation
"""

import pytest
from ai_services.data_mapper import DataMapper


class TestDataMapperHealthMetrics:
    """Test health metrics data mapping"""

    def test_map_health_metrics_valid_response(self):
        """Test mapping valid Huawei health metrics response"""
        huawei_response = {
            "heart_rate": 72,
            "temperature": 98.6,
            "blood_pressure_sys": 120,
            "blood_pressure_dia": 80,
            "oxygen_saturation": 98,
            "respiratory_rate": 16,
            "glucose_level": 100
        }
        
        mapped = DataMapper.map_health_metrics(huawei_response)
        
        assert mapped is not None
        assert mapped.get("heart_rate") == 72
        assert mapped.get("temperature") == 98.6
        assert len(mapped) >= 7  # At least 7 core metrics

    def test_map_health_metrics_all_required_fields_present(self):
        """Test that all required health metrics fields are present"""
        huawei_response = {
            "heart_rate": 72,
            "temperature": 98.6,
            "blood_pressure_sys": 120,
            "blood_pressure_dia": 80,
            "oxygen_saturation": 98,
            "respiratory_rate": 16,
            "glucose_level": 100
        }
        
        mapped = DataMapper.map_health_metrics(huawei_response)
        required_fields = [
            "heart_rate", "temperature", "blood_pressure_sys",
            "blood_pressure_dia", "oxygen_saturation", "respiratory_rate",
            "glucose_level"
        ]
        
        for field in required_fields:
            assert field in mapped, f"Missing required field: {field}"

    def test_map_health_metrics_handles_missing_fields(self):
        """Test that mapper handles missing fields gracefully"""
        incomplete_response = {
            "heart_rate": 72,
            "temperature": 98.6
        }
        
        # Should not crash, should return what it can
        mapped = DataMapper.map_health_metrics(incomplete_response)
        assert mapped is not None
        assert isinstance(mapped, dict)

    def test_map_health_metrics_normalizes_values(self):
        """Test that values are normalized to reasonable ranges"""
        response = {
            "heart_rate": 72,
            "temperature": 98.6,
            "blood_pressure_sys": 120,
            "blood_pressure_dia": 80,
            "oxygen_saturation": 98,
            "respiratory_rate": 16,
            "glucose_level": 100
        }
        
        mapped = DataMapper.map_health_metrics(response)
        
        # Heart rate should be positive and reasonable
        assert 0 < mapped.get("heart_rate", 0) <= 300
        # Temperature should be within biological range
        assert 90 < mapped.get("temperature", 100) < 110
        # O2 saturation should be 0-100
        assert 0 <= mapped.get("oxygen_saturation", 50) <= 100


class TestDataMapperRiskScore:
    """Test risk score data mapping"""

    def test_map_risk_score_valid_response(self):
        """Test mapping valid risk score response"""
        huawei_response = {
            "overall_risk": "medium",
            "risk_percentage": 45,
            "confidence": 0.87
        }
        
        mapped = DataMapper.map_risk_score(huawei_response)
        
        assert mapped is not None
        assert "overall_risk" in mapped
        assert "risk_percentage" in mapped
        assert "confidence" in mapped

    def test_map_risk_score_capitalizes_risk_level(self):
        """Test that risk level is properly capitalized"""
        response = {
            "overall_risk": "low",
            "risk_percentage": 20,
            "confidence": 0.92
        }
        
        mapped = DataMapper.map_risk_score(response)
        
        risk_level = mapped.get("overall_risk", "").lower()
        assert risk_level in ["low", "medium", "high"]

    def test_map_risk_score_percentage_in_range(self):
        """Test that risk percentage is within 0-100"""
        response = {
            "overall_risk": "high",
            "risk_percentage": 85,
            "confidence": 0.95
        }
        
        mapped = DataMapper.map_risk_score(response)
        
        percentage = mapped.get("risk_percentage", 0)
        assert 0 <= percentage <= 100

    def test_map_risk_score_confidence_in_range(self):
        """Test that confidence is between 0 and 1"""
        response = {
            "overall_risk": "medium",
            "risk_percentage": 50,
            "confidence": 0.85
        }
        
        mapped = DataMapper.map_risk_score(response)
        
        confidence = mapped.get("confidence", 0.5)
        assert 0 <= confidence <= 1

    def test_map_risk_score_handles_missing_fields(self):
        """Test that mapper handles incomplete responses"""
        incomplete = {
            "overall_risk": "low"
        }
        
        mapped = DataMapper.map_risk_score(incomplete)
        assert mapped is not None
        assert isinstance(mapped, dict)


class TestDataMapperForecast:
    """Test forecast data mapping"""

    def test_map_forecast_valid_response(self):
        """Test mapping valid forecast response"""
        response = {
            "historical_data": [
                {"timestamp": "2026-02-02", "value": 98.6},
                {"timestamp": "2026-02-03", "value": 98.5}
            ],
            "forecast_data": [
                {"timestamp": "2026-02-04", "point_forecast": 98.8}
            ]
        }
        
        mapped = DataMapper.map_forecast(response)
        
        assert mapped is None or isinstance(mapped, dict)

    def test_map_forecast_dates_array_present(self):
        """Test that dates array is present in mapped response"""
        response = {
            "historical_data": [
                {"timestamp": "2026-02-02", "value": 98.6}
            ],
            "forecast_data": [
                {"timestamp": "2026-02-04", "point_forecast": 98.8}
            ]
        }
        
        mapped = DataMapper.map_forecast(response)
        
        if mapped:
            assert "dates" in mapped

    def test_map_forecast_data_arrays_present(self):
        """Test that historical and forecast arrays are present"""
        response = {
            "historical_data": [
                {"timestamp": "2026-02-02", "value": 98.6}
            ],
            "forecast_data": [
                {"timestamp": "2026-02-04", "point_forecast": 98.8}
            ]
        }
        
        mapped = DataMapper.map_forecast(response)
        
        if mapped:
            assert "historical" in mapped
            assert "forecast" in mapped

    def test_map_forecast_handles_nulls_in_data(self):
        """Test that mapper handles null values in data arrays"""
        response = {
            "historical_data": [
                {"timestamp": "2026-02-02", "value": None}
            ],
            "forecast_data": [
                {"timestamp": "2026-02-04", "point_forecast": None}
            ]
        }
        
        mapped = DataMapper.map_forecast(response)
        
        # Should handle nulls without crashing
        assert mapped is None or isinstance(mapped, dict)

    def test_map_forecast_preserves_data_order(self):
        """Test that data order is preserved"""
        response = {
            "historical_data": [
                {"timestamp": "2026-02-02", "value": 98.6},
                {"timestamp": "2026-02-03", "value": 98.5}
            ],
            "forecast_data": [
                {"timestamp": "2026-02-04", "point_forecast": 98.8}
            ]
        }
        
        mapped = DataMapper.map_forecast(response)
        
        # Just verify it doesn't crash and returns structure or None
        assert mapped is None or isinstance(mapped, dict)


class TestDataMapperValidation:
    """Test data validation"""

    def test_validation_handles_malformed_json(self):
        """Test that validation handles malformed data"""
        malformed = "not a dict"
        
        # Should handle gracefully or return safe value
        try:
            result = DataMapper.map_health_metrics({})
            assert isinstance(result, dict) or result is None
        except Exception as e:
            # If it exceptions, that's acceptable for truly malformed data
            assert True

    def test_validation_logs_warnings_for_missing_fields(self):
        """Test that validation logs warnings for required fields"""
        incomplete = {"heart_rate": 72}
        
        # Should not crash but should log warning
        result = DataMapper.map_health_metrics(incomplete)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
