@echo off
echo === GVEDC-trading-stocks-refine 备份 ===

:: 创建备份目录
set BACKUP_DIR=backups\%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
mkdir %BACKUP_DIR% 2>nul

:: 备份PostgreSQL
echo 备份PostgreSQL...
pg_dump -U postgres gvedc_relational > %BACKUP_DIR%\relational.sql

:: 备份Elasticsearch
echo 备份Elasticsearch...
curl -X POST "http://localhost:9200/_snapshot/gvedc_backup/snapshot_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%?wait_for_completion=true" -H "Content-Type: application/json" -d "{\"indices\":\"gvedc_encyclopedia\",\"include_global_state\":false}"

:: 备份InfluxDB
echo 备份InfluxDB...
curl -X POST "http://localhost:8086/query" --data-urlencode "q=SELECT * INTO gvedc_timeseries_backup..:MEASUREMENT FROM gvedc_timeseries..:MEASUREMENT GROUP BY *;"

:: 备份ChromaDB
echo 备份ChromaDB...
xcopy data\vector %BACKUP_DIR%\vector /E /I 2>nul

echo === 备份完成 ===
pause