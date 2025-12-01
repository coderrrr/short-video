"""
测试应用路由
"""
from app.main import app

print('FastAPI app created successfully')
print(f'Number of routes: {len(app.routes)}')
print('\nRegistered routes:')
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', [])
        print(f'  {", ".join(methods) if methods else "GET"} {route.path}')
