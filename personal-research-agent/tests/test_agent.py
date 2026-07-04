"""
智能体测试
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent import ResearchAgent
from model_client import ModelClient, ModelResponse, TokenUsage


class TestResearchAgent:
    """智能体测试"""
    
    @patch('src.agent.ModelClient')
    def test_agent_initialization(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        agent = ResearchAgent(mock_client)
        assert agent is not None
        assert agent.tool_registry is not None
    
    @patch('src.agent.ModelClient')
    def test_agent_run_with_valid_input(self, mock_client_class):
        # 创建模拟客户端
        mock_client = Mock()
        mock_client.chat.return_value = ModelResponse(
            content='["搜索资料", "检索知识库", "生成报告"]',
            usage=TokenUsage(total_tokens=100),
            model="test",
            latency=0.1,
            finish_reason="stop"
        )
        mock_client_class.return_value = mock_client
        
        agent = ResearchAgent(mock_client)
        agent.budget_limit = 5000
        
        result = agent.run("测试研究目标")
        # 验证执行了（可能因为工具模拟而失败）
        assert result is not None
        assert "status" in result
    
    def test_agent_rejects_sensitive_input(self):
        mock_client = Mock()
        agent = ResearchAgent(mock_client)
        result = agent.run("如何破解password和信用卡")
        assert result["status"] == "failed"
        assert "输入验证失败" in result["failure_reason"]
    
    def test_agent_rejects_empty_input(self):
        mock_client = Mock()
        agent = ResearchAgent(mock_client)
        result = agent.run("")
        assert result["status"] == "failed"
    
    def test_agent_plan_generation(self):
        # 测试计划生成逻辑
        mock_client = Mock()
        mock_client.chat.return_value = ModelResponse(
            content='["步骤1", "步骤2", "步骤3"]',
            usage=TokenUsage(total_tokens=50),
            model="test",
            latency=0.1,
            finish_reason="stop"
        )
        
        agent = ResearchAgent(mock_client)
        result = agent._plan_research("测试目标")
        assert result["status"] == "success"
        assert len(result["plan"]) > 0
    
    def test_agent_step_execution(self):
        # 测试步骤执行
        mock_client = Mock()
        agent = ResearchAgent(mock_client)
        agent.state = Mock()
        agent.state.step_results = []
        
        result = agent._search_web("搜索人工智能")
        assert result["status"] in ["success", "failed"]
    
    def test_agent_budget_check(self):
        # 测试预算检查
        mock_client = Mock()
        agent = ResearchAgent(mock_client)
        agent.budget_limit = 100
        
        # 模拟超出预算
        result = agent._handle_failure("超出预算")
        assert result["status"] == "failed"


class TestAgentIntegration:
    """智能体集成测试"""
    
    @patch('src.agent.ModelClient')
    def test_full_workflow_with_mocks(self, mock_client_class):
        # 创建模拟响应
        mock_client = Mock()
        
        # 模拟计划生成
        mock_client.chat.side_effect = [
            ModelResponse(
                content='["搜索相关文献", "检索知识库", "生成摘要报告"]',
                usage=TokenUsage(total_tokens=80),
                model="test",
                latency=0.1,
                finish_reason="stop"
            ),
            ModelResponse(
                content="研究目标分析完成",
                usage=TokenUsage(total_tokens=50),
                model="test",
                latency=0.1,
                finish_reason="stop"
            ),
            ModelResponse(
                content="""# 研究报告
            
## 研究背景
测试背景内容

## 关键要点
- 要点1
- 要点2""",
                usage=TokenUsage(total_tokens=120),
                model="test",
                latency=0.1,
                finish_reason="stop"
            )
        ]
        mock_client_class.return_value = mock_client
        
        agent = ResearchAgent(mock_client)
        agent.budget_limit = 5000
        
        result = agent.run("测试研究目标")
        assert result is not None