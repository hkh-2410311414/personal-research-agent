"""
安全护栏测试
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from guardrails import SecurityGuardrail


class TestSecurityGuardrail:
    """安全护栏测试"""
    
    def test_validate_input_valid(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_input("正常的研究问题")
        assert result["valid"] is True
    
    def test_validate_input_empty(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_input("")
        assert result["valid"] is False
        assert result["reason"] == "empty_input"
    
    def test_validate_input_whitespace(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_input("   ")
        assert result["valid"] is False
        assert result["reason"] == "empty_input"
    
    def test_validate_input_sensitive_password(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_input("如何破解password")
        assert result["valid"] is False
        assert result["reason"] == "sensitive_content"
    
    def test_validate_input_sensitive_credit(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_input("信用卡号码是多少")
        assert result["valid"] is False
        assert result["reason"] == "sensitive_content"
    
    def test_validate_input_too_long(self):
        guardrail = SecurityGuardrail()
        long_text = "a" * 10001
        result = guardrail.validate_input(long_text)
        assert result["valid"] is False
        assert result["reason"] == "input_too_long"
    
    def test_validate_file_path_safe(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_file_path("./data/test.md")
        assert result["valid"] is True
    
    def test_validate_file_path_unsafe(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_file_path("/etc/passwd")
        assert result["valid"] is False
        assert "path_outside" in result["reason"]
    
    def test_validate_file_path_wrong_extension(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_file_path("./data/test.exe")
        assert result["valid"] is False
        assert result["reason"] == "disallowed_file_extension"
    
    def test_validate_url_https(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_url("https://arxiv.org/paper")
        assert result["valid"] is True
    
    def test_validate_url_http(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_url("http://example.com")
        assert result["valid"] is True
    
    def test_validate_url_unsafe_protocol(self):
        guardrail = SecurityGuardrail()
        result = guardrail.validate_url("ftp://example.com")
        assert result["valid"] is False
    
    def test_sanitize_output_removes_keys(self):
        guardrail = SecurityGuardrail()
        text = "My API key is sk-abc12345678901234567890123456789012345678"
        result = guardrail.sanitize_output(text)
        assert "sk-" not in result
        assert "[REDACTED_API_KEY]" in result
    
    def test_sanitize_output_removes_email(self):
        guardrail = SecurityGuardrail()
        text = "Contact me at test@example.com"
        result = guardrail.sanitize_output(text)
        assert "test@example.com" not in result
        assert "[REDACTED_EMAIL]" in result
    
    def test_check_budget_within_limit(self):
        guardrail = SecurityGuardrail()
        result = guardrail.check_budget(100, 500)
        assert result["within_budget"] is True
    
    def test_check_budget_exceeded(self):
        guardrail = SecurityGuardrail()
        result = guardrail.check_budget(600, 500)
        assert result["within_budget"] is False