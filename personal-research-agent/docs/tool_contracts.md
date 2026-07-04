# MCP风格工具契约

本文档定义了智能体使用的所有工具的契约规范。

---

## 工具1: web_search

### 基本信息
- **名称**: web_search
- **用途**: 根据查询关键词搜索网络资料

### 输入参数
| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索查询词 |
| top_k | integer | 否 | 5 | 返回结果数量，1-10 |

### 输出结构
```json
{
  "status": "success",
  "items": [
    {
      "title": "网页标题",
      "snippet": "内容摘要",
      "source": "来源URL",
      "relevance_score": 0.95
    }
  ],
  "total_found": 3
}