@echo off
echo === GVEDC-trading-stocks-refine 初始化 ===

:: 创建目录结构
echo 创建目录结构...
mkdir data 2>nul

:: 初始化SQLite数据库（Python脚本）
echo 初始化SQLite数据库...
python -c "
import sqlite3
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
c.execute('''
CREATE TABLE IF NOT EXISTS stock_sections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  stock_id INTEGER,
  title TEXT,
  content TEXT,
  level INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (stock_id) REFERENCES trading_stocks(id)
)
''')
conn.commit()
conn.close()
print('SQLite数据库初始化完成')
"

echo === 初始化完成 ===
pause