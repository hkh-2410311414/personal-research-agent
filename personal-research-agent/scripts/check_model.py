#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型连通性检查脚本
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from model_client import ModelClient
from dotenv import load_dotenv


def main():
    """检查模型连通性"""
    load_dotenv()
    
    print("=" * 60)
    print("🔍 真实模型连通性测试")
    print("=" * 60)
    
    try:
        client = ModelClient()
        
        print(f"\n📡 配置信息:")
        print(f"  API端点: {client.base_url}")
        # 不显示API密钥
        print(f"  模型: {client.model}")
        print(f"  最大词元: {client.max_tokens}")
        
        print("\n⏳ 正在连接...")
        result = client.check_connectivity()
        
        print("\n📊 测试结果:")
        print(f"  状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
        print(f"  模型: {result['model']}")
        print(f"  延迟: {result['latency']:.2f}s")
        
        if result['success']:
            print(f"  词元消耗: {result['tokens']}")
            print(f"  响应: {result['response'][:50]}..." if len(result.get('response', '')) > 50 else f"  响应: {result.get('response', '')}")
        else:
            print(f"  错误: {result.get('error', '未知错误')[:100]}")
        
        print("\n" + "=" * 60)
        
        if result['success']:
            print("✅ 模型连通性测试通过")
            return 0
        else:
            print("❌ 模型连通性测试失败")
            print("\n请检查:")
            print("  1. .env 文件是否存在且配置正确")
            print("  2. API密钥是否有效")
            print("  3. 网络连接是否正常")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)[:100]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())