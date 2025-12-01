#!/usr/bin/env python3
"""
健康检查脚本
用于 Docker 容器健康检查
"""
import sys
import requests

def check_health():
    """检查应用健康状态"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("健康检查通过")
            return 0
        else:
            print(f"健康检查失败：HTTP {response.status_code}")
            return 1
    except requests.exceptions.RequestException as e:
        print(f"健康检查失败：{e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
