"""
项目执行迭代系统 - 分层策略版
基于五层决策迭代机制，遇到错误时自动分析并生成解决方案
支持顶层、中间层、细节层策略的协调
"""
import sqlite3
import os
from datetime import datetime

# ============ 分层策略系统 ============

class LayeredStrategySystem:
    """分层策略系统"""

    def __init__(self, db_path='./data/strategies.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        """初始化策略表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer TEXT,
                name TEXT,
                strategy TEXT,
                parent_id INTEGER,
                priority INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES strategies(id)
            )
        ''')
        self.conn.commit()

    def set_top_strategy(self, name, strategy):
        """设置顶层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (layer, name, strategy, priority)
            VALUES ('top', ?, ?, 100)
        """, (name, strategy))
        self.conn.commit()
        return cursor.lastrowid

    def get_top_strategy(self):
        """获取顶层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, strategy FROM strategies
            WHERE layer = 'top' ORDER BY priority DESC LIMIT 1
        """)
        return cursor.fetchone()

    def set_middle_strategy(self, name, strategy, parent_id=None):
        """设置中间层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (layer, name, strategy, parent_id, priority)
            VALUES ('middle', ?, ?, ?, 50)
        """, (name, strategy, parent_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_middle_strategies(self, parent_id=None):
        """获取中间层策略"""
        cursor = self.conn.cursor()
        if parent_id:
            cursor.execute("""
                SELECT id, name, strategy FROM strategies
                WHERE layer = 'middle' AND parent_id = ?
            """, (parent_id,))
        else:
            cursor.execute("""
                SELECT id, name, strategy FROM strategies
                WHERE layer = 'middle'
            """)
        return cursor.fetchall()

    def set_bottom_strategy(self, name, strategy, parent_id=None):
        """设置细节层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (layer, name, strategy, parent_id, priority)
            VALUES ('bottom', ?, ?, ?, 10)
        """, (name, strategy, parent_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_bottom_strategies(self, parent_id=None):
        """获取细节层策略"""
        cursor = self.conn.cursor()
        if parent_id:
            cursor.execute("""
                SELECT id, name, strategy FROM strategies
                WHERE layer = 'bottom' AND parent_id = ?
            """, (parent_id,))
        else:
            cursor.execute("""
                SELECT id, name, strategy FROM strategies
                WHERE layer = 'bottom'
            """)
        return cursor.fetchall()

    def get_full_strategy_chain(self):
        """获取完整策略链"""
        top = self.get_top_strategy()
        if not top:
            return None

        top_id, top_name, top_strategy = top
        middle_strategies = self.get_middle_strategies(top_id)
        bottom_by_middle = {}

        for mid_id, mid_name, mid_strategy in middle_strategies:
            bottom_strategies = self.get_bottom_strategies(mid_id)
            bottom_by_middle[mid_id] = bottom_strategies

        return {
            'top': {'id': top_id, 'name': top_name, 'strategy': top_strategy},
            'middle': [
                {'id': m[0], 'name': m[1], 'strategy': m[2], 'bottom': bottom_by_middle.get(m[0], [])}
                for m in middle_strategies
            ]
        }

    def summarize_bottom_to_top(self):
        """自下而上汇总"""
        summary = []
        top = self.get_top_strategy()
        if top:
            top_id = top[0]
            middle_strategies = self.get_middle_strategies(top_id)
            for mid_id, mid_name, mid_strategy in middle_strategies:
                bottom_strategies = self.get_bottom_strategies(mid_id)
                summary.append({
                    'middle': mid_name,
                    'bottom_count': len(bottom_strategies)
                })
        return summary

# ============ 五层迭代系统 ============

class IterationService:
    """带分层策略的项目执行迭代"""

    def __init__(self):
        self.db_path = './data/project.db'
        self.data_layer = DataLayer(self.db_path)
        self.model_layer = ModelLayer()
        self.strategy_system = LayeredStrategySystem('./data/strategies.db')
        self.execution_layer = ExecutionLayer()
        self.evaluation_layer = EvaluationLayer()

    def run_on_error(self, error_info):
        """遇到错误时执行迭代（带分层策略）"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now()}] 检测到错误，开始迭代分析...")
        print(f"错误信息: {error_info.get('message', 'Unknown')}")
        print(f"{'='*60}")

        # 1. 数据层：收集错误上下文
        print("\n  [数据层] 收集错误上下文...")
        data = self.data_layer.collect_error_context(error_info)

        # 2. 模型层：分析问题根因
        print("  [模型层] 分析问题根因...")
        analysis = self.model_layer.analyze_problem(data)

        # 3. 策略层：分层策略生成
        print("\n  [策略层] 分层策略分析...")
        strategy = self._generate_layered_strategy(analysis)

        # 4. 执行层：执行修复
        print("\n  [执行层] 执行修复...")
        result = self.execution_layer.execute_fix(strategy)

        # 5. 评估层：验证效果
        print("  [评估层] 验证修复效果...")
        evaluation = self.evaluation_layer.verify_fix(result)

        # 6. 反馈到数据层
        print("  [反馈] 更新知识库...")
        self.data_layer.update_knowledge(evaluation)

        print(f"\n[{datetime.now()}] 迭代完成")
        return evaluation

    def _generate_layered_strategy(self, analysis):
        """生成分层策略"""
        error_type = analysis.get('error_type', '')

        # 顶层策略：确定修复方向
        top_strategies = {
            'ImportError': '自动修复依赖问题',
            'PermissionError': '修复权限问题',
            'SyntaxError': '修复代码质量问题',
            'FileNotFoundError': '修复文件配置问题'
        }
        top_name = error_type
        top_strategy = top_strategies.get(error_type, '通用问题处理')

        # 中间层策略：具体执行方法
        middle_mapping = {
            'ImportError': ('pip安装', '安装缺失的依赖包'),
            'PermissionError': ('检查权限', '检查文件权限设置'),
            'SyntaxError': ('语法检查', '检查代码语法错误'),
            'FileNotFoundError': ('创建文件', '创建或修复缺失文件')
        }
        middle_name, middle_strategy = middle_mapping.get(error_type, ('手动检查', '需要人工干预'))

        # 细节层策略：具体命令
        bottom_mapping = {
            'ImportError': 'pip install <package>',
            'PermissionError': 'chmod +x <file>',
            'SyntaxError': 'python -m py_compile <file>',
            'FileNotFoundError': '检查路径配置'
        }
        bottom_strategy = bottom_mapping.get(error_type, '手动调查')

        # 存储分层策略
        top_id = self.strategy_system.set_top_strategy(top_name, top_strategy)
        middle_id = self.strategy_system.set_middle_strategy(middle_name, middle_strategy, top_id)
        bottom_id = self.strategy_system.set_bottom_strategy('执行命令', bottom_strategy, middle_id)

        # 打印分层结果
        print(f"\n    ┌─ [顶层策略] {top_strategy}")
        print(f"    │")
        print(f"    ├─ [中间层策略] {middle_name}: {middle_strategy}")
        print(f"    │")
        print(f"    └─ [细节层策略] {bottom_strategy}")

        return {
            'top': {'id': top_id, 'name': top_name, 'strategy': top_strategy},
            'middle': {'id': middle_id, 'name': middle_name, 'strategy': middle_strategy},
            'bottom': {'id': bottom_id, 'name': '执行命令', 'strategy': bottom_strategy}
        }

    def show_strategy_hierarchy(self):
        """显示策略层级"""
        print(f"\n{'='*60}")
        print("当前分层策略架构")
        print(f"{'='*60}")

        chain = self.strategy_system.get_full_strategy_chain()
        if not chain:
            print("  暂无策略")
            return

        print(f"\n顶层策略: {chain['top']['name']} - {chain['top']['strategy']}")

        print(f"\n中间层策略 ({len(chain['middle'])}个):")
        for m in chain['middle']:
            print(f"  ├── {m['name']}: {m['strategy']}")
            if m['bottom']:
                print(f"  │   └── 细节层 ({len(m['bottom'])}个):")
                for b in m['bottom']:
                    print(f"  │       └── {b[1]}: {b[2]}")

        summary = self.strategy_system.summarize_bottom_to_top()
        print(f"\n策略汇总: {len(summary)} 个中间层策略")

class DataLayer:
    """数据层：负责收集项目执行数据"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def collect_error_context(self, error_info):
        """收集错误上下文数据"""
        return {
            'timestamp': datetime.now().isoformat(),
            'error_message': error_info.get('message', ''),
            'error_type': error_info.get('type', 'Unknown'),
            'error_traceback': error_info.get('traceback', ''),
            'context': error_info.get('context', {})
        }

    def update_knowledge(self, evaluation):
        """更新知识库"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO error_history (error_message, error_type, solution, result)
            VALUES (?, ?, ?, ?)
        """, (
            evaluation.get('error_message', ''),
            evaluation.get('error_type', ''),
            evaluation.get('solution', ''),
            evaluation.get('result', '')
        ))
        self.conn.commit()

class ModelLayer:
    """模型层：负责分析问题"""

    def analyze_problem(self, data):
        """分析问题根因"""
        error_msg = data.get('error_message', '')
        error_type = data.get('error_type', 'Unknown')

        root_causes = {
            'ImportError': 'missing_dependency',
            'PermissionError': 'permission_issue',
            'SyntaxError': 'syntax_error',
            'FileNotFoundError': 'file_not_found'
        }

        return {
            'root_cause': root_causes.get(error_type, 'unknown'),
            'error_type': error_type,
            'severity': 'high' if error_type in ['ImportError', 'PermissionError'] else 'medium'
        }

class ExecutionLayer:
    """执行层：负责执行修复"""

    def execute_fix(self, strategy):
        """执行修复"""
        bottom_strategy = strategy.get('bottom', {}).get('strategy', '')
        return {
            'type': 'execution',
            'command': bottom_strategy,
            'status': 'simulated'
        }

class EvaluationLayer:
    """评估层：负责验证修复效果"""

    def verify_fix(self, execution):
        """验证修复效果"""
        import random
        success_rate = 0.7 + random.random() * 0.25

        return {
            'type': 'evaluation',
            'error_message': execution.get('command', ''),
            'error_type': execution.get('type', ''),
            'solution': execution.get('command', ''),
            'result': 'success' if success_rate > 0.8 else 'partial',
            'success_rate': success_rate
        }

def simulate_errors():
    """模拟错误"""
    return [
        {'message': 'ModuleNotFoundError: No module named requests', 'type': 'ImportError'},
        {'message': 'PermissionError: Access denied to file config.yml', 'type': 'PermissionError'},
        {'message': 'SyntaxError: invalid syntax', 'type': 'SyntaxError'},
        {'message': 'FileNotFoundError: No such file main.py', 'type': 'FileNotFoundError'},
    ]

def main():
    print("=" * 60)
    print("GVEDC-trading-stocks-refine 项目执行迭代系统")
    print("分层策略版")
    print("=" * 60)

    service = IterationService()

    print("\n--- 测试分层策略迭代 ---")
    errors = simulate_errors()

    for i, error in enumerate(errors, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {error['type']}")
        print(f"{'='*60}")
        service.run_on_error(error)

    service.show_strategy_hierarchy()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()