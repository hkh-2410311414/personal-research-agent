#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
个人研究员智能体 - 主入口
"""

import os
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from model_client import ModelClient
from agent import ResearchAgent
from guardrails import SecurityGuardrail

# 配置日志
os.makedirs("logs", exist_ok=True)
log_filename = f"logs/agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_filename)
    ]
)
logger = logging.getLogger(__name__)


def check_model():
    """检查模型连通性（输出已脱敏）"""
    print("=" * 60)
    print("🔍 真实模型连通性测试")
    print("=" * 60)
    
    try:
        load_dotenv()
        client = ModelClient()
        result = client.check_connectivity()
        
        # 安全显示API端点
        api_url = client.base_url
        if client.api_key:
            # 隐藏API密钥
            api_url = api_url.replace(client.api_key, "[REDACTED]")
        
        print(f"\n📡 API端点: {api_url}")
        print(f"🤖 模型: {result['model']}")
        print(f"📊 状态: {'✅ 连接成功' if result['success'] else '❌ 连接失败'}")
        
        if result['success']:
            print(f"⏱️  延迟: {result['latency']:.2f}s")
            print(f"📝 词元消耗: {result['tokens']}")
            print(f"💬 响应: {result['response'][:50]}..." if len(result.get('response', '')) > 50 else f"💬 响应: {result.get('response', '')}")
        else:
            print(f"❌ 错误: {result.get('error', '未知错误')}")
        
        print("\n" + "=" * 60)
        
        if result['success']:
            print("✅ 模型连通性测试通过")
        else:
            print("❌ 模型连通性测试失败，请检查配置")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"模型检查失败: {e}")
        print(f"\n❌ 模型连接失败: {e}")
        print("\n请检查:")
        print("  1. .env 文件是否存在")
        print("  2. API密钥是否正确")
        print("  3. 网络连接是否正常")
        return False


def run_agent(goal: str, budget_limit: int = 5000):
    """运行智能体"""
    print("=" * 60)
    print("🤖 个人研究员智能体")
    print("=" * 60)
    print(f"\n📋 研究目标: {goal}")
    print(f"💰 预算限制: {budget_limit} 词元")
    print("\n" + "=" * 60)
    print("⏳ 智能体正在处理...\n")
    
    try:
        # 加载环境变量
        load_dotenv()
        
        # 初始化
        model_client = ModelClient()
        
        # 安全检查
        guardrail = SecurityGuardrail()
        input_check = guardrail.validate_input(goal)
        if not input_check["valid"]:
            print(f"❌ 输入验证失败: {input_check['reason']}")
            return {"status": "failed", "failure_reason": input_check['reason']}
        
        # 创建并运行智能体
        agent = ResearchAgent(model_client)
        agent.budget_limit = budget_limit
        
        result = agent.run(goal)
        
        print("\n" + "=" * 60)
        print("📊 执行结果")
        print("=" * 60)
        
        if result["status"] == "success":
            # 显示报告
            print("\n📋 研究报告:")
            print("-" * 40)
            print(result.get("report", "无报告内容"))
            print("-" * 40)
            
            # 显示关键要点
            print("\n💡 关键要点:")
            key_points = result.get("key_points", [])
            if key_points:
                for i, point in enumerate(key_points, 1):
                    print(f"  {i}. {point}")
            else:
                print("  （无关键要点）")
            
            # 显示资料来源
            print("\n📚 资料来源:")
            sources = result.get("sources", [])
            if sources:
                for source in sources:
                    print(f"  - {source}")
            else:
                print("  （无资料来源）")
            
            # 显示统计信息
            if result.get("state"):
                state = result["state"]
                print("\n📊 执行统计:")
                print(f"  📝 计划步骤: {len(state.get('plan', []))}")
                print(f"  ✅ 执行步骤: {len(state.get('step_results', []))}")
                print(f"  🔢 词元消耗: {state.get('token_usage', {}).get('total', 0)}")
                print(f"  💰 估算成本: ${state.get('token_usage', {}).get('cost', 0):.6f}")
        else:
            print(f"\n❌ 任务失败: {result.get('failure_reason', '未知原因')}")
        
        print("\n" + "=" * 60)
        
        # 保存结果
        output_file = f"logs/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # 移除敏感信息后再保存
            safe_result = {
                "status": result["status"],
                "report": result.get("report", ""),
                "key_points": result.get("key_points", []),
                "sources": result.get("sources", []),
                "failure_reason": result.get("failure_reason", ""),
                "timestamp": datetime.now().isoformat()
            }
            json.dump(safe_result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存: {output_file}")
        
        return result
        
    except Exception as e:
        logger.error(f"执行错误: {e}")
        print(f"\n❌ 执行错误: {e}")
        return {"status": "failed", "failure_reason": str(e)}


def interactive_mode(budget_limit: int = 5000):
    """交互模式"""
    print("=" * 60)
    print("🤖 个人研究员智能体 - 交互模式")
    print("=" * 60)
    print("\n💡 输入研究目标，智能体将自动完成研究")
    print("💡 输入 'quit' 或 'exit' 退出")
    print("💡 输入 'help' 查看帮助")
    print("-" * 60)
    
    while True:
        try:
            goal = input("\n📝 请输入研究目标: ").strip()
            
            if goal.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！")
                break
            
            if goal.lower() == 'help':
                print("\n📖 帮助:")
                print("  - 输入任意研究目标，如: '研究人工智能在医疗领域的应用'")
                print("  - 目标应清晰明确，包含主题和方向")
                print("  - 智能体会自动搜索、检索和生成报告")
                continue
            
            if not goal:
                print("⚠️  请输入有效的研究目标")
                continue
            
            run_agent(goal, budget_limit)
            
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="个人研究员智能体 - 基于AI的自动化研究工具"
    )
    parser.add_argument(
        "--check-model", 
        action="store_true", 
        help="检查模型连通性"
    )
    parser.add_argument(
        "--goal", 
        type=str, 
        help="研究目标"
    )
    parser.add_argument(
        "--budget", 
        type=int, 
        default=5000, 
        help="词元预算限制（默认5000）"
    )
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true", 
        help="交互模式"
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="检查环境配置"
    )
    
    args = parser.parse_args()
    
    # 加载环境变量
    load_dotenv()
    
    # 确保必要目录存在
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data/knowledge_base", exist_ok=True)
    
    if args.check_env:
        from scripts.check_env import check_env
        sys.exit(0 if check_env() else 1)
    
    if args.check_model:
        success = check_model()
        sys.exit(0 if success else 1)
    
    if args.interactive:
        interactive_mode(args.budget)
        return
    
    if args.goal:
        result = run_agent(args.goal, args.budget)
        sys.exit(0 if result["status"] == "success" else 1)
    
    # 默认显示帮助
    parser.print_help()
    print("\n示例:")
    print("  python main.py --check-model")
    print("  python main.py --goal '研究人工智能在医疗领域的应用'")
    print("  python main.py --interactive")


if __name__ == "__main__":
    main()