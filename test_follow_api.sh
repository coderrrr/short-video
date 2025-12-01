#!/bin/bash

# 测试关注功能API

API_BASE="http://localhost:8000"

echo "=== 1. 登录获取token ==="
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/users/login" \
  -H "Content-Type: application/json" \
  -d '{"employee_id":"ADMIN001","password":"admin123"}')

echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
USER_ID=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('user', {}).get('id', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败，无法获取token"
  exit 1
fi

echo -e "\n✅ 登录成功，用户ID: $USER_ID"

# 获取一个不同的用户ID用于测试（这里使用固定ID，实际应该从数据库查询）
TARGET_USER_ID="test-user-id"

echo -e "\n=== 2. 检查关注状态 ==="
FOLLOW_STATUS=$(curl -s -X GET "$API_BASE/users/$TARGET_USER_ID/follow-status" \
  -H "Authorization: Bearer $TOKEN")

echo "$FOLLOW_STATUS" | python3 -m json.tool 2>/dev/null || echo "$FOLLOW_STATUS"

echo -e "\n=== 3. 关注用户 ==="
FOLLOW_RESPONSE=$(curl -s -X POST "$API_BASE/users/$TARGET_USER_ID/follow" \
  -H "Authorization: Bearer $TOKEN")

echo "$FOLLOW_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$FOLLOW_RESPONSE"

echo -e "\n=== 4. 再次检查关注状态 ==="
FOLLOW_STATUS2=$(curl -s -X GET "$API_BASE/users/$TARGET_USER_ID/follow-status" \
  -H "Authorization: Bearer $TOKEN")

echo "$FOLLOW_STATUS2" | python3 -m json.tool 2>/dev/null || echo "$FOLLOW_STATUS2"

echo -e "\n=== 5. 取消关注 ==="
UNFOLLOW_RESPONSE=$(curl -s -X DELETE "$API_BASE/users/$TARGET_USER_ID/follow" \
  -H "Authorization: Bearer $TOKEN")

echo "$UNFOLLOW_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UNFOLLOW_RESPONSE"

echo -e "\n=== 6. 最后检查关注状态 ==="
FOLLOW_STATUS3=$(curl -s -X GET "$API_BASE/users/$TARGET_USER_ID/follow-status" \
  -H "Authorization: Bearer $TOKEN")

echo "$FOLLOW_STATUS3" | python3 -m json.tool 2>/dev/null || echo "$FOLLOW_STATUS3"

echo -e "\n✅ 关注功能测试完成"
