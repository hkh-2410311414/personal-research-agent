"""
模型客户端 - 统一的大模型API调用封装
"""

import os
import time
import json
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """词元使用统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0


@dataclass
class ModelResponse:
    """模型响应"""
    content: str
    usage: TokenUsage
    model: str
    latency: float
    finish_reason: str


class ModelClient:
    """大模型客户端封装"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        # 从环境变量读取配置
        self.api_key = api_key or os.getenv("MODEL_API_KEY")
        self.base_url = base_url or os.getenv("MODEL_BASE_URL")
        self.model = model or os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.max_tokens = max_tokens or int(os.getenv("MAX_TOKENS", 4096))
        self.temperature = temperature or float(os.getenv("TEMPERATURE", 0.7))
        
        if not self.api_key:
            logger.warning("MODEL_API_KEY未设置，请配置.env文件")
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key or "dummy",
            base_url=self.base_url
        )
        
        # 初始化token计数器
        try:
            self.encoder = tiktoken.encoding_for_model(self.model)
        except:
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """计算文本的词元数"""
        try:
            return len(self.encoder.encode(text))
        except:
            return len(text) // 4  # 粗略估计
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> ModelResponse:
        """发送聊天请求"""
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                **{k: v for k, v in kwargs.items() if k not in ["max_tokens", "temperature"]}
            )
            
            latency = time.time() - start_time
            
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cost=self._estimate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                )
            )
            
            return ModelResponse(
                content=response.choices[0].message.content,
                usage=usage,
                model=response.model,
                latency=latency,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"Model request failed: {e}")
            raise
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """估算成本（仅供参考）"""
        # GPT-3.5-turbo 价格参考
        prompt_cost = prompt_tokens * 0.0000015
        completion_cost = completion_tokens * 0.000002
        return prompt_cost + completion_cost
    
    def check_connectivity(self) -> Dict[str, Any]:
        """检查模型连通性"""
        start_time = time.time()
        
        try:
            response = self.chat([
                {"role": "user", "content": "Hello, please respond with 'OK' to confirm connectivity."}
            ], max_tokens=10)
            
            return {
                "success": True,
                "model": self.model,
                "latency": time.time() - start_time,
                "tokens": response.usage.total_tokens,
                "response": response.content[:50] if response.content else ""
            }
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return {
                "success": False,
                "model": self.model,
                "error": str(e),
                "latency": time.time() - start_time,
                "tokens": 0,
                "response": ""
            }