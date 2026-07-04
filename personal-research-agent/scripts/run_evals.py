#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
评估脚本 - 运行 cases.jsonl 中的测试用例
"""

import json
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from model_client import ModelClient
from agent import ResearchAgent
from guardrails import SecurityGuardrail


def load_cases():
    """加载评估用例"""
    cases_file = Path(__file__).parent.parent / "evals" / "cases.jsonl"
    
    if not cases_file.exists():
        print(f"❌ 文件不存在: {cases_file}")
        return []
    
    cases = []
    with open(cases_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))
    
    return cases


def run_evaluation():
    """运行评估"""
    print("=" * 60)
    print("📊 评估用例执行")
    print("=" * 60)
    
    cases = load_cases()
    
    if not cases:
        print("⚠️  没有找到评估用例")
        return
    
    print(f"\n📋 共加载 {len(cases)} 个评估用例\n")
    
    guardrail = SecurityGuardrail()
    
    results = {
        "total": len(cases),
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for case in cases:
        case_id = case.get("id", "unknown")
        category = case.get("category", "unknown")
        user_input = case.get("input", "")
        expected = case.get("expected", "success")
        
        print(f"🔍 执行用例 [{case_id}] ({category})")
        print(f"  输入: {user_input[:50]}..." if len(user_input) > 50 else f"  输入: {user_input}")
        print(f"  期望: {expected}")
        
        # 安全检查
        check_result = guardrail.validate_input(user_input)
        
        # 判断结果
        if check_result["valid"] and expected == "success":
            status = "✅ PASS"
            results["passed"] += 1
        elif not check_result["valid"] and expected == "reject":
            status = "✅ PASS"
            results["passed"] += 1
        else:
            status = "❌ FAIL"
            results["failed"] += 1
        
        print(f"  结果: {status}")
        if not check_result["valid"]:
            print(f"  原因: {check_result.get('reason', 'unknown')}")
        print()
        
        results["details"].append({
            "id": case_id,
            "category": category,
            "input": user_input[:100],
            "expected": expected,
            "actual": "reject" if not check_result["valid"] else "success",
            "status": status,
            "reason": check_result.get("reason", "")
        })
    
    # 输出总结
    print("=" * 60)
    print("📊 评估结果总结")
    print("=" * 60)
    print(f"  总用例数: {results['total']}")
    print(f"  ✅ 通过: {results['passed']}")
    print(f"  ❌ 失败: {results['failed']}")
    print(f"  通过率: {results['passed']/results['total']*100:.1f}%")
    print("=" * 60)
    
    # 保存结果
    output_file = Path(__file__).parent.parent / "logs" / "eval_results.json"
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {output_file}")


if __name__ == "__main__":
    run_evaluation()