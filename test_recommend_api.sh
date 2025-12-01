#!/bin/bash

# 测试推荐API

API_BASE="http://localhost:8000"

echo "=== 1. 登录获取token ==="
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/users/login" \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"ADMIN001","password":"admin123"}')

echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败，无法获取token"
  exit 1
fi

echo -e "\n✅ 登录成功，token: ${TOKEN:0:20}..."

echo -e "\n=== 2. 测试推荐API ==="
RECOMMEND_RESPONSE=$(curl -s -X GET "$API_BASE/contents/recommended?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN")

echo "$RECOMMEND_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RECOMMEND_RESPONSE"

# 检查返回结果
CONTENT_COUNT=$(echo "$RECOMMEND_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('contents', [])))" 2>/dev/null)

if [ -n "$CONTENT_COUNT" ]; then
  echo -e "\n✅ 推荐API返回 $CONTENT_COUNT 条内容"
else
  echo -e "\n❌ 推荐API返回格式异常"
fi
