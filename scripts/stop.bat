@echo off
echo === GVEDC-trading-stocks-refine 停止 ===

:: 停止所有Node.js服务
echo 停止Node.js服务...
taskkill /F /IM node.exe 2>nul

echo === 服务停止完成 ===
pause