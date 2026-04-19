import os
import time
import json
import chromadb
from datetime import datetime, timedelta

def check_daily_updates():
    """检查数据库每日更新并保存记录"""
    print("=" * 60)
    print("Daily Database Check")
    print("=" * 60)
    
    # 初始化数据库连接
    client = chromadb.PersistentClient(path=".")
    collection = client.get_or_create_collection(name="documents")
    
    # 获取今天的日期
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\nDate: {today}")
    
    # 获取数据库统计信息
    total_docs = collection.count()
    print(f"Total documents: {total_docs}")
    
    # 检查文件大小
    chroma_db_path = os.path.join(".", "chroma.sqlite3")
    gvedc_db_path = os.path.join(".", "gvedc.db")
    
    chroma_size = 0
    gvedc_size = 0
    
    if os.path.exists(chroma_db_path):
        chroma_size = os.path.getsize(chroma_db_path) / (1024 * 1024)
    
    if os.path.exists(gvedc_db_path):
        gvedc_size = os.path.getsize(gvedc_db_path) / (1024 * 1024)
    
    print(f"ChromaDB size: {chroma_size:.2f} MB")
    print(f"gvedc.db size: {gvedc_size:.2f} MB")
    
    # 尝试获取今天的文档
    try:
        # 注意：ChromaDB的where查询功能有限，这里我们使用语义搜索来查找今天的内容
        today_results = collection.query(
            query_texts=[today],
            n_results=5,
            include=["documents", "metadatas"]
        )
        
        today_docs = []
        if today_results and today_results.get('documents'):
            for idx, doc in enumerate(today_results['documents'][0]):
                meta = today_results['metadatas'][0][idx] if today_results.get('metadatas') else {}
                today_docs.append({
                    "title": meta.get('title', 'Unknown'),
                    "type": meta.get('type', 'document'),
                    "date": meta.get('date', today)
                })
        
        print(f"\nToday's documents found: {len(today_docs)}")
        for doc in today_docs:
            print(f"  - {doc['title']} ({doc['type']})")
            
    except Exception as e:
        print(f"Error querying today's documents: {e}")
        today_docs = []
    
    # 创建检查报告
    report = {
        "date": today,
        "total_documents": total_docs,
        "chroma_size_mb": round(chroma_size, 2),
        "gvedc_size_mb": round(gvedc_size, 2),
        "today_documents": today_docs,
        "timestamp": datetime.now().isoformat()
    }
    
    # 生成报告内容
    report_content = f"""# Daily Database Check Report

## Date: {today}

### Database Statistics
- Total documents: {total_docs}
- ChromaDB size: {chroma_size:.2f} MB
- gvedc.db size: {gvedc_size:.2f} MB

### Today's Documents

"""
    
    if today_docs:
        for doc in today_docs:
            report_content += f"- {doc['title']} ({doc['type']})\n"
    else:
        report_content += "No new documents found today.\n"
    
    report_content += f"\n### Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # 保存报告到数据库
    report_id = f"daily-check-{int(time.time())}"
    report_metadata = {
        "id": report_id,
        "kind": "daily_check",
        "title": f"Daily Database Check - {today}",
        "authors": ["System"],
        "date": today,
        "type": "report",
        "abstract": f"Daily database check report for {today}",
        "keywords": ["daily check", "database", "statistics"],
        "category": ["System"],
        "source": "daily_check.py"
    }
    
    collection.add(
        documents=[report_content],
        metadatas=[report_metadata],
        ids=[report_id]
    )
    
    print(f"\n✓ Report saved to database with ID: {report_id}")
    print("=" * 60)
    print("Daily check completed successfully!")
    print("=" * 60)
    
    return report

def main():
    try:
        check_daily_updates()
    except Exception as e:
        print(f"Error during daily check: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
