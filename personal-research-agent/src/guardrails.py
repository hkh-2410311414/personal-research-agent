"""
安全护栏 - 输入验证、敏感信息过滤、预算控制
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityGuardrail:
    """安全护栏"""
    
    # 敏感词模式
    SENSITIVE_PATTERNS = [
        r'(?i)password|passwd|pwd',
        r'(?i)credit card|信用卡|银行卡',
        r'(?i)ssn|social security|身份证',
        r'(?i)hack|exploit|攻击|入侵',
        r'(?i)\bkill\b|\bdeath\b|自杀|杀人',
        r'(?i)非法|违法|毒品|violence|暴力',
        r'(?i)terrorism|恐怖|极端',
    ]
    
    # 密钥模式（用于日志脱敏）
    SECRET_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{32,}', '[REDACTED_API_KEY]'),
        (r'[a-zA-Z0-9]{40,}', '[REDACTED_KEY]'),
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[REDACTED_EMAIL]'),
        (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[REDACTED_IP]'),
        (r'(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3})', '[REDACTED_INTERNAL]'),
    ]
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'.md', '.txt', '.json', '.csv', '.pdf', '.docx'}
    
    # 允许的域名
    ALLOWED_DOMAINS = {
        'arxiv.org', 'scholar.google.com', 'wikipedia.org',
        'github.com', 'example.com', 'openai.com', 'deepseek.com'
    }
    
    def __init__(self):
        self.compiled_patterns = [re.compile(p) for p in self.SENSITIVE_PATTERNS]
    
    def validate_input(self, text: str) -> Dict[str, Any]:
        """验证用户输入是否安全"""
        if not text or not text.strip():
            return {"valid": False, "reason": "empty_input"}
        
        if len(text) > 10000:
            return {"valid": False, "reason": "input_too_long", "max_length": 10000}
        
        # 检查敏感词
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                logger.warning(f"Input blocked: contains sensitive pattern")
                return {"valid": False, "reason": "sensitive_content", "pattern": pattern.pattern}
        
        return {"valid": True}
    
    def validate_file_path(self, path: str, base_dir: str = "./data") -> Dict[str, Any]:
        """验证文件路径是否安全"""
        try:
            resolved_path = Path(path).resolve()
            base_path = Path(base_dir).resolve()
            
            if not str(resolved_path).startswith(str(base_path)):
                return {"valid": False, "reason": "path_outside_allowed_directory"}
            
            if resolved_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                return {"valid": False, "reason": "disallowed_file_extension"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "reason": f"path_validation_error: {str(e)}"}
    
    def validate_url(self, url: str) -> Dict[str, Any]:
        """验证URL是否安全"""
        try:
            if not url.startswith(('http://', 'https://')):
                return {"valid": False, "reason": "unsupported_protocol"}
            
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            allowed = any(domain.endswith(d) for d in self.ALLOWED_DOMAINS)
            if not allowed:
                return {"valid": False, "reason": "domain_not_allowed", "domain": domain}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "reason": f"url_validation_error: {str(e)}"}
    
    def sanitize_output(self, text: str) -> str:
        """清理输出中的敏感信息"""
        result = text
        for pattern, replacement in self.SECRET_PATTERNS:
            result = re.sub(pattern, replacement, result)
        return result
    
    def sanitize_log(self, text: str) -> str:
        """清理日志中的敏感信息"""
        return self.sanitize_output(text)
    
    def check_budget(self, tokens_used: int, budget_limit: int = 5000) -> Dict[str, Any]:
        """检查是否超出预算"""
        if tokens_used > budget_limit:
            return {
                "within_budget": False,
                "tokens_used": tokens_used,
                "budget_limit": budget_limit,
                "message": f"超出词元预算: {tokens_used}/{budget_limit}"
            }
        return {
            "within_budget": True,
            "tokens_used": tokens_used,
            "budget_limit": budget_limit
        }