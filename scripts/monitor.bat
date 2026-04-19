@echo off
echo === GVEDC-trading-stocks-refine 监控 ===

:: 检查Elasticsearch状态
echo 检查Elasticsearch状态...
curl -X GET "http://localhost:9200/_cluster/health"

:: 检查PostgreSQL状态
echo 检查PostgreSQL状态...
psql -U postgres -c "SELECT 1;"

:: 检查Neo4j状态
echo 检查Neo4j状态...
curl -X GET "http://localhost:7474/db/data/" -u neo4j:changeme

:: 检查InfluxDB状态
echo 检查InfluxDB状态...
curl -X GET "http://localhost:8086/ping"

:: 检查ChromaDB状态
echo 检查ChromaDB状态...
curl -X GET "http://localhost:8000/api/v1/collections"

:: 检查API服务状态
echo 检查API服务状态...
curl -X GET "http://localhost:3000/health"

echo === 监控完成 ===
pause