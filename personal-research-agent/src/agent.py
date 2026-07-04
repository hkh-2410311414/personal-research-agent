"""
智能体核心 - 研究计划、执行、报告生成
"""

import os
import sys
import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from model_client import ModelClient, TokenUsage
from tools import WebSearchTool, KnowledgeBaseTool, ResearchSummarizerTool, ToolRegistry
from guardrails import SecurityGuardrail


logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """智能体状态"""
    goal: str
    plan: List[str] = field(default_factory=list)
    current_step: int = 0
    step_results: List[Dict] = field(default_factory=list)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    is_complete: bool = False
    is_failed: bool = False
    failure_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_log(self) -> Dict:
        return {
            "goal": self.goal[:200],  # 限制长度
            "plan": self.plan,
            "current_step": self.current_step,
            "step_results": [
                {
                    "status": r.get("status"),
                    "tool": r.get("tool", "unknown"),
                    "query": r.get("query", "")[:100],
                    "total": r.get("total", 0)
                }
                for r in self.step_results
            ],
            "token_usage": {
                "total": self.token_usage.total_tokens,
                "cost": round(self.token_usage.cost, 6)
            },
            "is_complete": self.is_complete,
            "is_failed": self.is_failed,
            "failure_reason": self.failure_reason
        }


class ResearchAgent:
    """个人研究员智能体"""
    
    def __init__(self, model_client: ModelClient):
        self.model_client = model_client
        self.guardrail = SecurityGuardrail()
        
        # 初始化工具
        self.web_search = WebSearchTool()
        self.kb_search = KnowledgeBaseTool()
        self.summarizer = ResearchSummarizerTool(model_client)
        
        # 注册工具
        self.tool_registry = ToolRegistry()
        self.tool_registry.register("web_search", self.web_search)
        self.tool_registry.register("knowledge_base_search", self.kb_search)
        self.tool_registry.register("research_summarizer", self.summarizer)
        
        self.state: Optional[AgentState] = None
        self.budget_limit = int(os.getenv("BUDGET_TOKENS", 5000))
    
    def run(self, goal: str) -> Dict[str, Any]:
        """
        执行研究任务
        """
        # 输入安全检查
        input_check = self.guardrail.validate_input(goal)
        if not input_check["valid"]:
            return {
                "status": "failed",
                "failure_reason": f"输入验证失败: {input_check['reason']}",
                "state": None
            }
        
        # 初始化状态
        self.state = AgentState(goal=goal)
        logger.info(f"开始研究任务: {goal[:100]}...")
        
        try:
            # Step 1: 制定研究计划
            plan_result = self._plan_research(goal)
            if plan_result["status"] == "failed":
                return self._handle_failure(plan_result["reason"])
            
            self.state.plan = plan_result["plan"]
            logger.info(f"研究计划: {self.state.plan}")
            
            # Step 2: 执行研究步骤
            for step_idx, step in enumerate(self.state.plan):
                self.state.current_step = step_idx
                logger.info(f"执行步骤 {step_idx+1}/{len(self.state.plan)}: {step}")
                
                result = self._execute_step(step)
                self.state.step_results.append(result)
                
                # 检查预算
                budget_check = self.guardrail.check_budget(
                    self.state.token_usage.total_tokens,
                    self.budget_limit
                )
                if not budget_check["within_budget"]:
                    return self._handle_failure(f"超出预算: {budget_check['message']}")
                
                if result.get("status") == "failed":
                    return self._handle_failure(f"步骤失败: {result.get('reason', '未知错误')}")
            
            # Step 3: 生成研究报告
            report_result = self._generate_report()
            if report_result["status"] == "failed":
                return self._handle_failure(f"报告生成失败: {report_result.get('reason', '未知错误')}")
            
            self.state.is_complete = True
            
            return {
                "status": "success",
                "report": report_result["report"],
                "state": self.state.to_log(),
                "key_points": report_result.get("key_points", []),
                "sources": report_result.get("sources", [])
            }
            
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return self._handle_failure(f"执行异常: {str(e)}")

    def _plan_research(self, goal: str) -> Dict:
        """制定研究计划"""
        try:
            prompt = f"""
            你是一个研究规划专家。请为以下研究目标制定一个详细的研究计划：
            
            研究目标：{goal}
            
            请将计划分解为3-5个具体的研究步骤，每个步骤应该是可执行的操作。
            步骤应该包括搜索、检索、分析、摘要等类型。
            
            请以JSON数组格式输出，例如：
            ["搜索相关文献", "检索知识库", "整理关键信息", "生成摘要报告"]
            
            只输出JSON数组，不要有其他内容。
            """
            
            response = self.model_client.chat([
                {"role": "system", "content": "你是一个研究规划专家，擅长制定清晰的研究计划。"},
                {"role": "user", "content": prompt}
            ])
            
            self.state.token_usage.total_tokens += response.usage.total_tokens
            
            try:
                plan = json.loads(response.content.strip())
                if not isinstance(plan, list):
                    plan = ["搜索相关资料", "检索知识库", "整理和分析", "生成研究报告"]
            except:
                plan = ["搜索相关资料", "检索知识库", "整理和分析", "生成研究报告"]
            
            return {
                "status": "success",
                "plan": plan[:5]
            }
            
        except Exception as e:
            logger.error(f"Plan generation error: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def _execute_step(self, step: str) -> Dict:
        """执行单个步骤"""
        if "搜索" in step or "查找" in step or "检索网络" in step:
            return self._search_web(step)
        elif "知识库" in step or "本地" in step or "笔记" in step:
            return self._search_knowledge_base(step)
        elif "摘要" in step or "总结" in step or "整理" in step:
            return self._summarize_step(step)
        else:
            return self._general_step(step)
    
    def _search_web(self, step: str) -> Dict:
        """执行网络搜索"""
        try:
            query = self._extract_query(step, self.state.goal)
            result = self.web_search.search(query, top_k=5)
            
            if result["status"] != "success":
                return {"status": "failed", "reason": result.get("message", "搜索失败")}
            
            return {
                "status": "success",
                "tool": "web_search",
                "query": query,
                "results": result.get("items", []),
                "total": result.get("total_found", 0)
            }
            
        except Exception as e:
            return {"status": "failed", "reason": str(e)}
    
    def _search_knowledge_base(self, step: str) -> Dict:
        """检索知识库"""
        try:
            query = self._extract_query(step, self.state.goal)
            result = self.kb_search.search(query, top_k=3)
            
            if result["status"] != "success":
                return {"status": "failed", "reason": result.get("message", "知识库检索失败")}
            
            return {
                "status": "success",
                "tool": "knowledge_base_search",
                "query": query,
                "results": result.get("items", []),
                "total": result.get("total_found", 0)
            }
            
        except Exception as e:
            return {"status": "failed", "reason": str(e)}
    
    def _summarize_step(self, step: str) -> Dict:
        """执行摘要步骤"""
        try:
            # 收集之前步骤的结果
            content = ""
            for result in self.state.step_results:
                if result.get("status") == "success":
                    if "results" in result:
                        for item in result["results"]:
                            content += item.get("snippet", "") + "\n"
            
            if not content:
                content = f"关于 {self.state.goal} 的研究资料"
            
            result = self.summarizer.summarize(content, max_length=300)
            
            if result["status"] != "success":
                return {"status": "failed", "reason": result.get("message", "摘要失败")}
            
            return {
                "status": "success",
                "tool": "research_summarizer",
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", [])
            }
            
        except Exception as e:
            return {"status": "failed", "reason": str(e)}
    
    def _general_step(self, step: str) -> Dict:
        """通用步骤执行"""
        try:
            context = f"研究目标: {self.state.goal}\n当前步骤: {step}\n"
            if self.state.step_results:
                context += f"已完成: {len(self.state.step_results)} 步\n"
            
            prompt = f"""
            请执行以下研究步骤：
            
            {context}
            
            请提供具体的执行结果或分析。
            """
            
            response = self.model_client.chat([
                {"role": "system", "content": "你是一个研究助理，帮助执行研究步骤。"},
                {"role": "user", "content": prompt}
            ])
            
            self.state.token_usage.total_tokens += response.usage.total_tokens
            
            return {
                "status": "success",
                "tool": "general",
                "result": response.content
            }
            
        except Exception as e:
            return {"status": "failed", "reason": str(e)}
    
    def _extract_query(self, step: str, goal: str) -> str:
        """提取查询关键词"""
        keywords = [goal]
        query = step.replace("搜索", "").replace("查找", "").replace("检索", "").strip()
        if query and query != step:
            keywords.append(query)
        return " ".join(keywords)
    
    def _generate_report(self) -> Dict:
        """生成研究报告"""
        try:
            all_results = []
            for result in self.state.step_results:
                if result.get("status") == "success":
                    all_results.append(result)
            
            context = f"""
            研究目标: {self.state.goal}
            
            研究过程:
            {json.dumps(all_results, ensure_ascii=False, indent=2)}
            """
            
            prompt = f"""
            请根据以下研究过程和发现，生成一份完整的研究报告：
            
            {context}
            
            报告应包含：
            1. 研究背景和目标
            2. 主要发现
            3. 关键要点
            4. 结论与建议
            5. 参考资料来源
            
            请用结构化的方式输出，包含标题和段落。
            """
            
            response = self.model_client.chat([
                {"role": "system", "content": "你是一个专业的研究报告撰写专家。"},
                {"role": "user", "content": prompt}
            ])
            
            self.state.token_usage.total_tokens += response.usage.total_tokens
            
            # 提取关键要点
            key_points = []
            if "关键要点" in response.content:
                lines = response.content.split('\n')
                for line in lines:
                    if line.strip().startswith(('•', '-', '*', '关键要点')):
                        key_points.append(line.strip())
            
            return {
                "status": "success",
                "report": self.guardrail.sanitize_output(response.content),
                "key_points": key_points[:5],
                "sources": ["网络搜索结果", "本地知识库"]
            }
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {"status": "failed", "reason": str(e)}
    
    def _handle_failure(self, reason: str) -> Dict:
        """处理失败状态"""
        self.state.is_failed = True
        self.state.failure_reason = reason
        logger.error(f"Agent failed: {reason}")
        
        return {
            "status": "failed",
            "failure_reason": reason,
            "state": self.state.to_log()
        }