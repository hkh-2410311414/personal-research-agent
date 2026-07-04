#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工作流编排模块 - 定义智能体的执行流程和状态管理

本模块负责:
1. 定义工作流步骤
2. 编排各步骤的执行顺序
3. 管理工作流状态
4. 处理步骤间的数据传递
5. 记录工作流执行日志
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    name: str                           # 步骤名称
    description: str                    # 步骤描述
    action: str                         # 执行动作 (plan/search/summarize/report)
    required: bool = True               # 是否必须执行
    retry_count: int = 0                # 重试次数
    max_retries: int = 3                # 最大重试次数
    status: str = "pending"             # pending/running/success/failed/skipped
    result: Any = None                  # 执行结果
    error: Optional[str] = None         # 错误信息
    started_at: Optional[str] = None    # 开始时间
    finished_at: Optional[str] = None   # 结束时间


@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_id: str                    # 工作流ID
    goal: str                           # 研究目标
    current_step: int = 0               # 当前步骤索引
    steps: List[WorkflowStep] = field(default_factory=list)
    total_tokens: int = 0               # 总词元消耗
    total_cost: float = 0.0             # 总成本
    status: str = "idle"                # idle/running/completed/failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "workflow_id": self.workflow_id,
            "goal": self.goal,
            "current_step": self.current_step,
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "action": s.action,
                    "status": s.status,
                    "result": s.result,
                    "error": s.error
                }
                for s in self.steps
            ],
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error
        }


class WorkflowEngine:
    """
    工作流引擎 - 编排和执行工作流
    
    使用示例:
        engine = WorkflowEngine()
        engine.set_goal("研究人工智能在医疗领域的应用")
        engine.add_step("plan", "制定研究计划", "plan")
        engine.add_step("search", "搜索相关资料", "search")
        engine.add_step("summarize", "生成摘要", "summarize")
        engine.add_step("report", "生成研究报告", "report")
        engine.run()
    """
    
    def __init__(self):
        self.state: Optional[WorkflowState] = None
        self.step_handlers = {
            "plan": self._handle_plan,
            "search": self._handle_search,
            "knowledge": self._handle_knowledge,
            "summarize": self._handle_summarize,
            "report": self._handle_report,
            "general": self._handle_general
        }
    
    def set_goal(self, goal: str) -> "WorkflowEngine":
        """设置研究目标"""
        from datetime import datetime
        import uuid
        
        self.state = WorkflowState(
            workflow_id=str(uuid.uuid4())[:8],
            goal=goal,
            started_at=datetime.now().isoformat()
        )
        logger.info(f"创建工作流: {self.state.workflow_id}")
        logger.info(f"研究目标: {goal}")
        return self
    
    def add_step(self, name: str, description: str, action: str, required: bool = True) -> "WorkflowEngine":
        """添加工作流步骤"""
        if self.state is None:
            raise ValueError("请先调用 set_goal() 设置目标")
        
        step = WorkflowStep(
            name=name,
            description=description,
            action=action,
            required=required
        )
        self.state.steps.append(step)
        logger.info(f"添加步骤: {name} ({action})")
        return self
    
    def add_plan_steps(self) -> "WorkflowEngine":
        """添加标准研究计划步骤"""
        steps = [
            ("plan", "制定研究计划", "plan"),
            ("search", "搜索相关文献", "search"),
            ("knowledge", "检索本地知识库", "knowledge"),
            ("summarize", "整理和摘要信息", "summarize"),
            ("report", "生成研究报告", "report")
        ]
        for name, desc, action in steps:
            self.add_step(name, desc, action)
        return self
    
    def run(self, agent) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            agent: ResearchAgent 实例
        """
        if self.state is None:
            return {"status": "failed", "error": "未设置研究目标"}
        
        self.state.status = "running"
        logger.info(f"开始执行工作流: {self.state.workflow_id}")
        
        results = []
        
        for idx, step in enumerate(self.state.steps):
            self.state.current_step = idx
            step.status = "running"
            step.started_at = datetime.now().isoformat()
            
            logger.info(f"执行步骤 {idx+1}/{len(self.state.steps)}: {step.name}")
            
            try:
                # 调用对应的处理器
                handler = self.step_handlers.get(step.action, self._handle_general)
                result = handler(step, agent)
                
                if result.get("status") == "failed":
                    step.status = "failed"
                    step.error = result.get("error", "未知错误")
                    logger.error(f"步骤 {step.name} 失败: {step.error}")
                    
                    if step.required:
                        self.state.status = "failed"
                        self.state.error = step.error
                        return {
                            "status": "failed",
                            "error": step.error,
                            "step": step.name,
                            "results": results
                        }
                else:
                    step.status = "success"
                    step.result = result
                    results.append(result)
                    logger.info(f"步骤 {step.name} 完成")
                
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                logger.error(f"步骤 {step.name} 异常: {e}")
                
                if step.required:
                    self.state.status = "failed"
                    self.state.error = str(e)
                    return {
                        "status": "failed",
                        "error": str(e),
                        "step": step.name,
                        "results": results
                    }
            
            finally:
                step.finished_at = datetime.now().isoformat()
        
        self.state.status = "completed"
        self.state.completed_at = datetime.now().isoformat()
        logger.info(f"工作流完成: {self.state.workflow_id}")
        
        return {
            "status": "success",
            "workflow_id": self.state.workflow_id,
            "results": results,
            "state": self.state.to_dict()
        }
    
    def _handle_plan(self, step: WorkflowStep, agent) -> Dict:
        """处理计划生成步骤"""
        result = agent._plan_research(agent.state.goal)
        return result
    
    def _handle_search(self, step: WorkflowStep, agent) -> Dict:
        """处理搜索步骤"""
        query = agent._extract_query(step.description, agent.state.goal)
        result = agent.web_search.search(query, top_k=5)
        return result
    
    def _handle_knowledge(self, step: WorkflowStep, agent) -> Dict:
        """处理知识库检索步骤"""
        query = agent._extract_query(step.description, agent.state.goal)
        result = agent.kb_search.search(query, top_k=3)
        return result
    
    def _handle_summarize(self, step: WorkflowStep, agent) -> Dict:
        """处理摘要生成步骤"""
        # 收集之前步骤的结果作为内容
        content = ""
        for result in agent.state.step_results:
            if result.get("status") == "success":
                if "results" in result:
                    for item in result["results"]:
                        content += item.get("snippet", "") + "\n"
        
        if not content:
            content = f"关于 {agent.state.goal} 的研究资料"
        
        result = agent.summarizer.summarize(content, max_length=300)
        return result
    
    def _handle_report(self, step: WorkflowStep, agent) -> Dict:
        """处理报告生成步骤"""
        result = agent._generate_report()
        return result
    
    def _handle_general(self, step: WorkflowStep, agent) -> Dict:
        """处理通用步骤"""
        context = f"研究目标: {agent.state.goal}\n当前步骤: {step.description}"
        
        response = agent.model_client.chat([
            {"role": "system", "content": "你是一个研究助理，帮助执行研究步骤。"},
            {"role": "user", "content": context}
        ])
        
        agent.state.token_usage.total_tokens += response.usage.total_tokens
        
        return {
            "status": "success",
            "tool": "general",
            "result": response.content,
            "tokens": response.usage.total_tokens
        }
    
    def get_state(self) -> Optional[Dict]:
        """获取当前工作流状态"""
        if self.state is None:
            return None
        return self.state.to_dict()
    
    def get_progress(self) -> Dict:
        """获取工作流进度"""
        if self.state is None:
            return {"progress": 0, "status": "idle"}
        
        total = len(self.state.steps)
        completed = sum(1 for s in self.state.steps if s.status == "success")
        
        return {
            "progress": round(completed / total * 100, 1) if total > 0 else 0,
            "completed": completed,
            "total": total,
            "status": self.state.status,
            "current_step": self.state.current_step
        }


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    """
    工作流使用示例
    
    运行方式:
        python src/workflow.py
    """
    
    print("=" * 60)
    print("工作流引擎示例")
    print("=" * 60)
    
    # 创建引擎
    engine = WorkflowEngine()
    
    # 设置目标并添加步骤
    engine.set_goal("研究人工智能在医疗领域的应用")
    engine.add_plan_steps()
    
    # 显示工作流信息
    print(f"\n工作流ID: {engine.state.workflow_id}")
    print(f"步骤数: {len(engine.state.steps)}")
    print("\n步骤列表:")
    for idx, step in enumerate(engine.state.steps, 1):
        print(f"  {idx}. {step.name}: {step.description} ({step.action})")
    
    print("\n" + "=" * 60)
    print("提示: 在 agent.py 中集成 WorkflowEngine 使用")
    print("=" * 60)