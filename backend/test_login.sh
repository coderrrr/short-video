#!/bin/bash
# 测试登录功能

echo "=========================================="
echo "测试登录功能"
echo "=========================================="
echo ""

# 测试1: 正确的凭据
echo "测试1: 使用正确的凭据登录"
echo "员工ID: ADMIN001, 密码: admin123"
echo ""
response=$(curl -s -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "ADMIN001", "password": "admin123"}')

if echo "$response" | grep -q "access_token"; then
    echo "✅ 登录成功！"
    echo ""
    echo "响应："
    echo "$response" | python3 -m json.tool
else
    echo "❌ 登录失败！"
    echo "$response"
fi

echo ""
echo "=========================================="
echo ""

# 测试2: 错误的密码
echo "测试2: 使用错误的密码"
echo "员工ID: ADMIN001, 密码: wrong_password"
echo ""
response=$(curl -s -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "ADMIN001", "password": "wrong_password"}')

if echo "$response" | grep -q "认证失败"; then
    echo "✅ 正确拒绝了错误密码！"
    echo ""
    echo "响应："
    echo "$response" | python3 -m json.tool
else
    echo "❌ 安全问题：接受了错误密码！"
    echo "$response"
fi

echo ""
echo "=========================================="
echo ""

# 测试3: 不存在的用户
echo "测试3: 使用不存在的员工ID"
echo "员工ID: NOTEXIST, 密码: any_password"
echo ""
response=$(curl -s -X POST "http://localhost:8000/users/login" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "NOTEXIST", "password": "any_password"}')

if echo "$response" | grep -q "认证失败"; then
    echo "✅ 正确拒绝了不存在的用户！"
    echo ""
    echo "响应："
    echo "$response" | python3 -m json.tool
else
    echo "❌ 安全问题：接受了不存在的用户！"
    echo "$response"
fi

echo ""
echo "=========================================="
echo "测试完成！"
echo "=========================================="
