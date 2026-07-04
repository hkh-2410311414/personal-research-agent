#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境变量检查工具 - 不输出敏感信息
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def check_env():
    """检查环境变量配置是否完整"""
    load_dotenv()
    
    # 所有可能的API配置
    api_configs = [
        ("COURSE_API_KEY", "课程API密钥"),
        ("COURSE_BASE_URL", "课程API地址"),
        ("DEEPSEEK_API_KEY", "DeepSeek API密钥"),
        ("DEEPSEEK_BASE_URL", "DeepSeek API地址"),
        ("MODEL_API_KEY", "模型API密钥（通用）"),
        ("MODEL_BASE_URL", "模型API地址（通用）"),
        ("MODEL_NAME", "模型名称"),
    ]
    
    # 项目配置
    project_configs = [
        ("MAX_TOKENS", "最大词元数"),
        ("TEMPERATURE", "温度参数"),
        ("BUDGET_TOKENS", "预算限制"),
        ("LOG_LEVEL", "日志级别"),
    ]
    
    print("=" * 60)
    print("🔍 环境变量检查")
    print("=" * 60)
    
    # 检查API配置
    print("\n📡 API配置:")
    print("-" * 40)
    
    has_api_key = False
    has_api_url = False
    
    for var_name, description in api_configs:
        value = os.getenv(var_name)
        if value:
            # 只显示部分信息
            if "KEY" in var_name or "SECRET" in var_name or "TOKEN" in var_name:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"  ✅ {var_name}: {masked}")
            else:
                # 对URL进行脱敏
                if value.startswith("http"):
                    from urllib.parse import urlparse
                    parsed = urlparse(value)
                    masked_url = f"{parsed.scheme}://{parsed.netloc}/[REDACTED]"
                    print(f"  ✅ {var_name}: {masked_url}")
                else:
                    print(f"  ✅ {var_name}: {value[:20]}...")
            
            if "API_KEY" in var_name:
                has_api_key = True
            if "BASE_URL" in var_name:
                has_api_url = True
        else:
            print(f"  ⚠️  {var_name}: 未设置")
    
    # 检查项目配置
    print("\n⚙️  项目配置:")
    print("-" * 40)
    
    for var_name, description in project_configs:
        value = os.getenv(var_name)
        if value:
            print(f"  ✅ {var_name}: {value}")
        else:
            print(f"  ⚠️  {var_name}: 未设置（使用默认值）")
    
    # 检查关键依赖
    print("\n📦 依赖检查:")
    print("-" * 40)
    
    try:
        import openai
        print(f"  ✅ openai: {openai.__version__}")
    except ImportError:
        print("  ❌ openai: 未安装")
    
    try:
        import dotenv
        print(f"  ✅ python-dotenv: 已安装")
    except ImportError:
        print("  ❌ python-dotenv: 未安装")
    
    # 总结
    print("\n" + "=" * 60)
    
    if has_api_key and has_api_url:
        print("✅ 环境配置完整，可以运行")
        return True
    elif has_api_key:
        print("⚠️  缺少API地址，请检查配置")
        return False
    elif has_api_url:
        print("⚠️  缺少API密钥，请检查配置")
        return False
    else:
        print("❌ 缺少API配置，请复制 .env.example 为 .env 并填写")
        print("\n示例:")
        print("  # 使用课程API")
        print("  COURSE_API_KEY=your_key_here")
        print("  COURSE_BASE_URL=https://liujinhang.com/aicampus/v1")
        print("  MODEL_NAME=gpt-3.5-turbo")
        print("\n  # 或使用DeepSeek API")
        print("  DEEPSEEK_API_KEY=sk-your_key_here")
        print("  DEEPSEEK_BASE_URL=https://api.deepseek.com")
        print("  MODEL_NAME=deepseek-v4-pro")
        return False


if __name__ == "__main__":
    sys.exit(0 if check_env() else 1)