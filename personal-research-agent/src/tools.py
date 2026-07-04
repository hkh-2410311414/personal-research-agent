"""
工具包 - MCP风格工具契约
每个工具都包含完整的契约说明
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================
# 工具1: web_search - MCP风格契约
# ============================================================
"""
工具名称: web_search
用途: 根据查询关键词搜索网络资料，返回相关网页摘要

输入参数:
  - query: string (必需) - 搜索查询词
  - top_k: integer (可选, 默认5, 范围1-10) - 返回结果数量

输出结构:
  - status: string - "success" 或错误类型
  - items: array of objects (仅成功时返回)
    - title: string - 网页标题
    - snippet: string - 内容摘要
    - source: string - 来源URL
    - relevance_score: float - 相关性评分(0-1)
  - total_found: integer - 总结果数

失败语义:
  - validation_error: query为空或top_k超出范围
  - network_error: 网络请求失败
  - rate_limit_error: 超过API调用限额

安全边界:
  - 只使用HTTPS协议
  - 过滤敏感关键词
  - 不自动下载文件
"""


class WebSearchTool:
    """网络搜索工具"""
    
    # 模拟数据（实际项目可替换为真实搜索API）
    MOCK_RESULTS = {
        "人工智能": [
            {"title": "人工智能发展趋势2026", 
             "snippet": "2026年AI领域的主要趋势包括多模态模型、自主智能体、AI安全...", 
             "source": "https://ai-trends.com/2026", 
             "relevance_score": 0.95},
            {"title": "AI在科研中的应用", 
             "snippet": "人工智能正在改变科学研究的方式，从文献检索到实验设计...",
             "source": "https://research-ai.org/applications", 
             "relevance_score": 0.88},
            {"title": "大语言模型综述", 
             "snippet": "本文综述了大型语言模型的发展历程、技术架构和应用场景...",
             "source": "https://llm-survey.com", 
             "relevance_score": 0.82},
        ],
        "医疗": [
            {"title": "AI辅助医疗诊断", 
             "snippet": "深度学习模型在医学影像分析中达到专家级准确率...",
             "source": "https://medical-ai.org/diagnosis", 
             "relevance_score": 0.91},
        ],
        "机器学习": [
            {"title": "机器学习基础教程", 
             "snippet": "从零开始学习机器学习，涵盖监督学习、无监督学习和强化学习...",
             "source": "https://ml-basics.com", 
             "relevance_score": 0.89},
        ],
    }
    
    def __init__(self):
        self.base_url = os.getenv("SEARCH_API_URL", "")
        self.api_key = os.getenv("SEARCH_API_KEY", "")
        self.sensitive_keywords = ["porn", "adult", "hate", "violence", "illegal", "terrorism"]
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        执行搜索 - MCP风格工具实现
        
        Args:
            query: 搜索查询词（必需）
            top_k: 返回结果数量（1-10）
        
        Returns:
            包含状态和结果的字典
        """
        # 1. 输入验证
        if not query or not query.strip():
            return {
                "status": "validation_error",
                "message": "query不能为空"
            }
        
        if top_k < 1 or top_k > 10:
            return {
                "status": "validation_error", 
                "message": f"top_k必须在1-10之间，当前值: {top_k}"
            }
        
        try:
            # 2. 安全检查
            if self._has_sensitive_content(query):
                return {
                    "status": "security_blocked",
                    "message": "查询包含敏感词，已被阻止"
                }
            
            # 3. 执行搜索（实际项目替换为真实API调用）
            results = self._mock_search(query, top_k)
            
            # 4. 后处理
            results = self._filter_sensitive(results)
            
            return {
                "status": "success",
                "items": results[:top_k],
                "total_found": len(results)
            }
            
        except requests.RequestException as e:
            logger.error(f"Search network error: {e}")
            return {
                "status": "network_error",
                "message": f"搜索请求失败: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "status": "error",
                "message": f"搜索失败: {str(e)}"
            }
    
    def _mock_search(self, query: str, top_k: int) -> List[Dict]:
        """模拟搜索"""
        results = []
        query_lower = query.lower()
        
        # 关键词匹配
        for key, items in self.MOCK_RESULTS.items():
            if key in query_lower or any(kw in query_lower for kw in key.split()):
                results.extend(items)
        
        # 如果没找到，生成通用结果
        if not results:
            results = [
                {"title": f"关于 '{query}' 的搜索结果", 
                 "snippet": f"这是关于 {query} 的模拟搜索结果。实际项目中会调用真实搜索API获取数据。",
                 "source": f"https://example.com/search?q={query}",
                 "relevance_score": 0.5}
            ]
        
        return results
    
    def _has_sensitive_content(self, text: str) -> bool:
        """检查敏感内容"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.sensitive_keywords)
    
    def _filter_sensitive(self, results: List[Dict]) -> List[Dict]:
        """过滤敏感内容"""
        filtered = []
        for item in results:
            text = (item.get("title", "") + " " + item.get("snippet", "")).lower()
            if not any(kw in text for kw in self.sensitive_keywords):
                filtered.append(item)
        return filtered


# ============================================================
# 工具2: knowledge_base_search - MCP风格契约
# ============================================================
"""
工具名称: knowledge_base_search
用途: 在本地知识库中检索与查询相关的文档片段

输入参数:
  - query: string (必需) - 检索查询
  - top_k: integer (可选, 默认3, 范围1-5) - 返回片段数量
  - category: string (可选) - 限定检索类别

输出结构:
  - status: string - "success" 或错误类型
  - items: array of objects (仅成功时返回)
    - title: string - 文档标题
    - snippet: string - 匹配片段（长度≤500字符）
    - source: string - 文件路径
    - score: float - 相似度分数(0-1)
  - total_found: integer - 匹配文档数

失败语义:
  - validation_error: query为空或top_k超出范围  - knowledge_base_missing: 知识库目录不存在
  - no_documents: 无可检索文档

安全边界:
  - 只读取项目 data/knowledge_base 目录
  - 不访问其他本地路径
  - 返回内容限制在500字符以内
"""


class KnowledgeBaseTool:
    """本地知识库检索工具"""
    
    def __init__(self, data_dir: str = "./data/knowledge_base"):
        self.data_dir = Path(data_dir)
        self.max_snippet_length = 500
        
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._create_sample_documents()
    
    def search(self, query: str, top_k: int = 3, category: Optional[str] = None) -> Dict[str, Any]:
        """
        检索知识库 - MCP风格工具实现
        """
        # 1. 输入验证
        if not query or not query.strip():
            return {
                "status": "validation_error",
                "message": "query不能为空"
            }
        
        if top_k < 1 or top_k > 5:
            return {
                "status": "validation_error",
                "message": f"top_k必须在1-5之间，当前值: {top_k}"
            }
        
        # 2. 检查知识库
        if not self.data_dir.exists():
            return {
                "status": "knowledge_base_missing",
                "message": f"知识库目录不存在: {self.data_dir}"
            }
        
        # 3. 获取文档
        documents = list(self.data_dir.glob("*.md")) + list(self.data_dir.glob("*.txt"))
        if category:
            documents = [d for d in documents if category.lower() in d.stem.lower()]
        
        if not documents:
            return {
                "status": "no_documents",
                "message": "知识库中没有可检索的文档"
            }
        
        try:
            # 4. 执行检索
            results = []
            for doc_path in documents:
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                score = self._calculate_similarity(query, content)
                if score > 0.1:
                    snippet = self._extract_snippet(content, query, self.max_snippet_length)
                    results.append({
                        "title": doc_path.stem,
                        "snippet": snippet,
                        "source": str(doc_path),
                        "score": round(score, 3)
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "status": "success",
                "items": results[:top_k],
                "total_found": len(results)
            }
            
        except Exception as e:
            logger.error(f"Knowledge base search error: {e}")
            return {
                "status": "error",
                "message": f"检索失败: {str(e)}"
            }
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        """计算文本相似度"""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        if not query_words:
            return 0.0
        overlap = len(query_words & text_words)
        return overlap / len(query_words) * 0.8 + 0.2
    
    def _extract_snippet(self, text: str, query: str, max_length: int) -> str:
        """提取包含关键词的片段"""
        sentences = text.replace('\n', ' ').split('。')
        for sent in sentences:
            if query.lower() in sent.lower():
                result = sent.strip()
                return result[:max_length] + ("..." if len(result) > max_length else "")
        
        return text[:max_length] + ("..." if len(text) > max_length else "")
    
    def _create_sample_documents(self):
        """创建示例文档"""
        samples = {
            "AI_research.md": """# 人工智能研究综述

人工智能（AI）是计算机科学的重要分支，致力于创建能够执行通常需要人类智能的任务的系统。

## 主要研究方向

1. **机器学习**：通过数据训练模型，让计算机从经验中学习
2. **深度学习**：使用多层神经网络进行特征提取和模式识别
3. **自然语言处理**：理解和生成人类语言
4. **计算机视觉**：识别和理解图像和视频内容

## 应用领域

- 医疗诊断：AI辅助医生进行疾病诊断
- 自动驾驶：感知环境并做出驾驶决策
- 智能助理：理解和执行用户指令
- 金融分析：预测市场趋势和风险
""",
            "machine_learning.md": """# 机器学习基础

机器学习是AI的核心领域，通过算法让计算机从数据中学习和改进。

## 监督学习

使用带标签的数据训练模型，用于分类和回归任务。
- 分类：预测离散类别
- 回归：预测连续值

## 无监督学习

使用未标注数据发现数据中的隐藏模式。
- 聚类：将相似数据分组
- 降维：减少数据维度

## 强化学习

通过奖励机制训练智能体在环境中做出决策。
- 智能体通过试错学习最优策略
""",
            "prompt_engineering.md": """# 提示工程指南

提示工程是设计和优化AI模型输入的技术，对于获得高质量输出至关重要。

## 基本原则

1. **清晰明确**：准确描述任务和目标
2. **提供上下文**：给出足够的背景信息
3. **指定格式**：明确输出格式要求
4. **使用分隔符**：区分不同部分的内容

## 进阶技巧

- 链式思维推理：引导模型逐步思考
- 少样本学习：提供示例
- 角色扮演：指定AI的角色
- 约束条件：限制输出范围
"""
        }
        
        for filename, content in samples.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)


# ============================================================
# 工具3: research_summarizer - MCP风格契约
# ============================================================
"""
工具名称: research_summarizer
用途: 对研究资料进行智能摘要和关键信息提取

输入参数:
  - content: string (必需) - 要摘要的文本内容
  - max_length: integer (可选, 默认200, 范围50-500) - 摘要最大长度
  - format: string (可选, 默认"paragraph") - 输出格式: "paragraph" 或 "bullets"

输出结构:
  - status: string - "success" 或错误类型
  - summary: string - 生成的摘要（长度≤1000字符）
  - key_points: array - 关键要点列表（3-5条）
  - word_count: integer - 原始文本字数

失败语义:
  - validation_error: content为空
  - length_exceeded: 内容过长（>10000字符）
  - security_blocked: 内容包含敏感词

安全边界:
  - 不处理包含敏感词的内容
  - 输出限制在1000字符以内
  - 使用模型API时限制上下文
"""


class ResearchSummarizerTool:
    """研究摘要生成工具"""
    
    def __init__(self, model_client):
        self.model_client = model_client
        self.max_content_length = 10000
        self.max_output_length = 1000
        self.sensitive_keywords = ["hate", "violence", "terrorism", "illegal"]
    
    def summarize(self, content: str, max_length: int = 200, format: str = "paragraph") -> Dict[str, Any]:
        """
        生成摘要 - MCP风格工具实现
        """
        # 1. 输入验证
        if not content or not content.strip():
            return {
                "status": "validation_error",
                "message": "content不能为空"
            }
        
        if max_length < 50 or max_length > 500:
            return {
                "status": "validation_error",
                "message": f"max_length必须在50-500之间，当前值: {max_length}"
            }
        
        if len(content) > self.max_content_length:
            return {
                "status": "length_exceeded",
                "message": f"内容过长: {len(content)}字符，最大允许{self.max_content_length}字符"
            }
        
        # 2. 安全检查
        if self._has_sensitive_content(content):
            return {
                "status": "security_blocked",
                "message": "内容包含敏感词，已阻止处理"
            }
        
        try:
            # 3. 构建提示词
            format_instruction = {
                "paragraph": "请用一段连贯的文字总结",
                "bullets": "请用要点列表的形式总结"
            }.get(format, "请总结")
            
            prompt = f"""
            请对以下研究资料进行摘要：
            
            原始内容：
            {content[:3000]}
            
            {format_instruction}。
            摘要长度控制在{max_length}字以内。
            同时提取3-5个关键要点。
            
            请按以下格式输出：
            SUMMARY: [摘要内容]
            KEY_POINTS:
            - [要点1]
            - [要点2]
            - [要点3]
            """
            
            response = self.model_client.chat([
                {"role": "system", "content": "你是一个专业的研究助理，擅长提取关键信息并生成简洁准确的摘要。"},
                {"role": "user", "content": prompt}
            ], max_tokens=500)
            
            # 4. 解析响应
            summary_text = response.content
            key_points = self._extract_key_points(summary_text)
            summary = self._extract_summary(summary_text)
            
            return {
                "status": "success",
                "summary": summary[:self.max_output_length],
                "key_points": key_points[:5],
                "word_count": len(content.split()),
                "token_usage": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return {
                "status": "error",
                "message": f"摘要生成失败: {str(e)}"
            }
    
    def _has_sensitive_content(self, text: str) -> bool:
        """检查敏感内容"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.sensitive_keywords)
    
    def _extract_summary(self, text: str) -> str:
        """提取摘要"""
        if "SUMMARY:" in text:
            parts = text.split("SUMMARY:")
            if len(parts) > 1:
                summary_part = parts[1]
                if "KEY_POINTS:" in summary_part:
                    return summary_part.split("KEY_POINTS:")[0].strip()
                return summary_part.strip()
        return text[:300]
    
    def _extract_key_points(self, text: str) -> List[str]:
        """提取关键要点"""
        points = []
        if "KEY_POINTS:" in text:
            parts = text.split("KEY_POINTS:")
            if len(parts) > 1:
                bullet_section = parts[1]
                for line in bullet_section.strip().split('\n'):
                    line = line.strip()
                    if line.startswith('- ') or line.startswith('* '):
                        points.append(line[2:].strip())
                    elif line and not line.startswith('SUMMARY'):
                        points.append(line.strip())
        return points if points else ["无法提取关键要点"]


# ============================================================
# 工具注册表
# ============================================================

class ToolRegistry:
    """工具注册和管理"""
    
    def __init__(self):
        self.tools = {}
    
    def register(self, name: str, tool_instance):
        self.tools[name] = tool_instance
    
    def get(self, name: str):
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        return list(self.tools.keys())
    
    def get_tool_contract(self, name: str) -> Dict[str, Any]:
        """获取工具的MCP风格契约"""
        contracts = {
            "web_search": {
                "name": "web_search",
                "description": "搜索网络资料",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "搜索查询词"},
                    "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10}
                },
                "returns": {"items": "array", "total_found": "integer"},
                "failures": ["validation_error", "network_error", "rate_limit_error", "security_blocked"]
            },
            "knowledge_base_search": {
                "name": "knowledge_base_search",
                "description": "检索本地知识库",
                "parameters": {
                    "query": {"type": "string", "required": True, "description": "检索查询"},
                    "top_k": {"type": "integer", "default": 3, "minimum": 1, "maximum": 5},
                    "category": {"type": "string", "required": False, "description": "限定类别"}
                },
                "returns": {"items": "array", "total_found": "integer"},
                "failures": ["validation_error", "knowledge_base_missing", "no_documents"]
            },
            "research_summarizer": {
                "name": "research_summarizer",
                "description": "生成研究摘要",
                "parameters": {
                    "content": {"type": "string", "required": True, "description": "要摘要的内容"},
                    "max_length": {"type": "integer", "default": 200, "minimum": 50, "maximum": 500},
                    "format": {"type": "string", "default": "paragraph", "enum": ["paragraph", "bullets"]}
                },
                "returns": {"summary": "string", "key_points": "array", "word_count": "integer"},
                "failures": ["validation_error", "length_exceeded", "security_blocked"]
            }
        }
        return contracts.get(name, {})