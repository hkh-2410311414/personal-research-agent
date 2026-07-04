"""
工具测试
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools import WebSearchTool, KnowledgeBaseTool, ResearchSummarizerTool
from model_client import ModelClient, ModelResponse, TokenUsage


class TestWebSearchTool:
    """网络搜索工具测试"""
    
    def test_search_valid_query(self):
        tool = WebSearchTool()
        result = tool.search("人工智能", top_k=3)
        assert result["status"] == "success"
        assert "items" in result
        assert len(result["items"]) <= 3
    
    def test_search_empty_query(self):
        tool = WebSearchTool()
        result = tool.search("")
        assert result["status"] == "validation_error"
    
    def test_search_invalid_top_k(self):
        tool = WebSearchTool()
        result = tool.search("test", top_k=0)
        assert result["status"] == "validation_error"
        
        result = tool.search("test", top_k=11)
        assert result["status"] == "validation_error"
    
    def test_search_sensitive_query(self):
        tool = WebSearchTool()
        result = tool.search("hate speech and violence")
        assert result["status"] == "security_blocked"
    
    def test_search_mock_data(self):
        tool = WebSearchTool()
        result = tool.search("机器学习", top_k=2)
        assert result["status"] == "success"
        assert len(result["items"]) > 0


class TestKnowledgeBaseTool:
    """知识库工具测试"""
    
    def test_search_valid_query(self):
        tool = KnowledgeBaseTool()
        result = tool.search("机器学习", top_k=2)
        if result["status"] == "success":
            assert "items" in result
            assert len(result["items"]) <= 2
    
    def test_search_empty_query(self):
        tool = KnowledgeBaseTool()
        result = tool.search("")
        assert result["status"] == "validation_error"
    
    def test_search_invalid_top_k(self):
        tool = KnowledgeBaseTool()
        result = tool.search("test", top_k=0)
        assert result["status"] == "validation_error"
        
        result = tool.search("test", top_k=6)
        assert result["status"] == "validation_error"
    
    def test_search_with_category(self):
        tool = KnowledgeBaseTool()
        result = tool.search("AI", category="research")
        assert result["status"] in ["success", "no_documents"]
    
    def test_documents_created(self):
        tool = KnowledgeBaseTool()
        assert tool.data_dir.exists()
        docs = list(tool.data_dir.glob("*.md"))
        assert len(docs) > 0


class TestResearchSummarizerTool:
    """摘要工具测试"""
    
    def test_summarize_valid_content(self):
        # 创建模拟客户端
        mock_client = Mock()
        mock_client.chat.return_value = ModelResponse(
            content="SUMMARY: 这是一个测试摘要\nKEY_POINTS:\n- 要点1\n- 要点2\n- 要点3",
            usage=TokenUsage(total_tokens=50),
            model="test",
            latency=0.1,
            finish_reason="stop"
        )
        
        tool = ResearchSummarizerTool(mock_client)
        result = tool.summarize("这是一个测试内容")
        assert result["status"] == "success"
        assert "summary" in result
        assert "key_points" in result
    
    def test_summarize_empty_content(self):
        mock_client = Mock()
        tool = ResearchSummarizerTool(mock_client)
        result = tool.summarize("")
        assert result["status"] == "validation_error"
    
    def test_summarize_too_long(self):
        mock_client = Mock()
        tool = ResearchSummarizerTool(mock_client)
        long_content = "a" * 10001
        result = tool.summarize(long_content)
        assert result["status"] == "length_exceeded"
    
    def test_summarize_sensitive_content(self):
        mock_client = Mock()
        tool = ResearchSummarizerTool(mock_client)
        result = tool.summarize("This contains violence and hate speech")
        assert result["status"] == "security_blocked"
    
    def test_summarize_bullets_format(self):
        mock_client = Mock()
        mock_client.chat.return_value = ModelResponse(
            content="SUMMARY: 测试摘要\nKEY_POINTS:\n- 要点1",
            usage=TokenUsage(total_tokens=30),
            model="test",
            latency=0.1,
            finish_reason="stop"
        )
        
        tool = ResearchSummarizerTool(mock_client)
        result = tool.summarize("测试内容", format="bullets")
        assert result["status"] == "success"