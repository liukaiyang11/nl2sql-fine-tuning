#!/bin/bash
# 测试后端API是否正常工作

echo "========================================="
echo "测试后端API服务"
echo "========================================="

API_URL="${API_URL:-http://localhost:8000}"

echo ""
echo "1. 测试健康检查..."
curl -s "${API_URL}/health" | jq '.' || echo "❌ 健康检查失败"

echo ""
echo "2. 测试状态API..."
curl -s "${API_URL}/api/status" | jq '.' || echo "❌ 状态API失败"

echo ""
echo "3. 测试API文档..."
curl -s -o /dev/null -w "%{http_code}" "${API_URL}/docs" | grep -q "200" && echo "✅ API文档可访问" || echo "❌ API文档不可访问"

echo ""
echo "========================================="
echo "测试完成"
echo "========================================="

