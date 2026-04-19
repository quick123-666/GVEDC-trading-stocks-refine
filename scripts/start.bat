@echo off
echo ========================================
echo GVEDC-trading-stocks-refine 决策系统
echo ========================================
echo.

:: 创建数据目录
echo 创建数据目录...
mkdir data 2>nul

:: 检查Python
echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 安装依赖
echo 安装依赖...
pip install chromadb --quiet 2>nul

:: 初始化数据库
echo 初始化数据库...
python -c "
import sqlite3
import os
os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data\gvedc.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS trading_stocks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_symbol TEXT,
  stock_name TEXT,
  content TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()
print('数据库初始化完成')
"

echo.
echo ========================================
echo 启动决策迭代系统...
echo ========================================
echo.
echo 按 Ctrl+C 停止系统
echo.

:: 启动决策迭代服务
python services\iteration\main.py

pause