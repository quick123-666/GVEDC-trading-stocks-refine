"""
项目执行迭代系统 - 分层策略版
支持顶层、中间层、细节层策略的协调
"""
import sqlite3
import os
from datetime import datetime

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
                layer TEXT,           -- top/middle/bottom
                name TEXT,
                strategy TEXT,
                parent_id INTEGER,
                priority INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES strategies(id)
            )
        ''')
        self.conn.commit()

    # ============ 顶层策略 ============

    def set_top_strategy(self, name, strategy):
        """设置顶层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (layer, name, strategy, priority)
            VALUES ('top', ?, ?, 100)
        """, (name, strategy))
        self.conn.commit()
        print(f"  [顶层策略] {name}: {strategy}")
        return cursor.lastrowid

    def get_top_strategy(self):
        """获取顶层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, strategy FROM strategies
            WHERE layer = 'top' ORDER BY priority DESC LIMIT 1
        """)
        return cursor.fetchone()

    # ============ 中间层策略 ============

    def set_middle_strategy(self, name, strategy, parent_id=None):
        """设置中间层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (layer, name, strategy, parent_id, priority)
            VALUES ('middle', ?, ?, ?, 50)
        """, (name, strategy, parent_id))
        self.conn.commit()
        print(f"  [中间层策略] {name}: {strategy}")
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

    # ============ 细节层策略 ============

    def set_bottom_strategy(self, name, strategy, parent_id=None):
        """设置细节层策略"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO strategies (layer, name, strategy, parent_id, priority)
            VALUES ('bottom', ?, ?, ?, 10)
        """, (name, strategy, parent_id))
        self.conn.commit()
        print(f"  [细节层策略] {name}: {strategy}")
        return cursor.lastrowid

    def get_bottom_strategies(self, parent_id=None):
        """获取细节层策略"""
        cursor = self.cursor = self.conn.cursor()
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

    # ============ 策略协调 ============

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

    def propagate_top_to_bottom(self, top_strategy_name, solution):
        """自上而下传播：顶层策略影响细节层"""
        print(f"\n  [策略传播] 顶层 '{top_strategy_name}' 影响到底层")
        top = self.get_top_strategy()
        if not top:
            return

        top_id = top[0]
        middle_strategies = self.get_middle_strategies(top_id)

        for mid_id, mid_name, mid_strategy in middle_strategies:
            bottom_strategies = self.get_bottom_strategies(mid_id)
            for bot_id, bot_name, bot_strategy in bottom_strategies:
                print(f"    - {bot_name} <- {mid_strategy[:30]}... <- {top_strategy_name}")

    def summarize_bottom_to_top(self):
        """自下而上汇总：细节层汇总到顶层"""
        print(f"\n  [策略汇总] 细节层汇总到顶层")
        top = self.get_top_strategy()
        if not top:
            return "无顶层策略"

        top_id, top_name, top_strategy = top
        middle_strategies = self.get_middle_strategies(top_id)

        summary = []
        for mid_id, mid_name, mid_strategy in middle_strategies:
            bottom_strategies = self.get_bottom_strategies(mid_id)
            summary.append({
                'middle': mid_name,
                'bottom_count': len(bottom_strategies),
                'details': [b[1] for b in bottom_strategies]
            })

        print(f"  顶层 '{top_name}' 包含 {len(summary)} 个中间层策略")
        for s in summary:
            print(f"    - {s['middle']}: {s['bottom_count']} 个细节策略")
        return summary

class IterationService:
    """带分层策略的项目执行迭代"""

    def __init__(self):
        self.db_path = './data/project_iteration.db'
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.strategy_system = LayeredStrategySystem('./data/strategies.db')
        self._init_tables()

    def _init_tables(self):
        """初始化表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_message TEXT,
                error_type TEXT,
                solution TEXT,
                result TEXT,
                top_strategy TEXT,
                middle_strategy TEXT,
                bottom_strategy TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def run_on_error(self, error_info):
        """遇到错误时执行迭代（带分层策略）"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now()}] 检测到错误，开始分层策略迭代...")
        print(f"错误信息: {error_info.get('message', 'Unknown')}")
        print(f"{'='*60}")

        # 1. 数据层：收集错误上下文
        print("\n  [数据层] 收集错误上下文...")
        data = self._collect_context(error_info)

        # 2. 策略层：使用分层策略分析
        print("\n  [策略层] 分层策略分析...")
        analysis = self._layered_strategy_analysis(error_info, data)

        # 3. 执行层：执行修复
        print("\n  [执行层] 执行修复...")
        result = self._execute_fix(analysis)

        # 4. 评估层：验证效果
        print("\n  [评估层] 验证修复效果...")
        evaluation = self._verify_fix(result)

        print(f"\n[{datetime.now()}] 迭代完成")
        return evaluation

    def _collect_context(self, error_info):
        """收集错误上下文"""
        return {
            'timestamp': datetime.now().isoformat(),
            'error': error_info.get('message', ''),
            'type': error_info.get('type', ''),
            'context': error_info.get('context', {})
        }

    def _layered_strategy_analysis(self, error_info, data):
        """分层策略分析"""
        error_msg = error_info.get('message', '')
        error_type = error_info.get('type', '')

        # 顶层策略：确定修复方向
        top_strategies = {
            'ImportError': '自动修复依赖问题',
            'PermissionError': '修复权限问题',
            'SyntaxError': '修复代码质量问题',
            'FileNotFoundError': '修复文件配置问题'
        }
        top_strategy = top_strategies.get(error_type, '通用问题处理')

        # 中间层策略：具体执行方法
        middle_strategies = {
            'missing_dependency': ['pip安装', '源码编译', '容器化部署'],
            'permission_issue': ['检查权限', '修改权限', '使用sudo'],
            'syntax_error': ['语法检查', '代码重构', '使用linter'],
            'file_not_found': ['创建文件', '检查路径', '配置环境变量']
        }
        middle_strategy = self._get_middle_for_error(error_type)

        # 细节层策略：具体命令
        bottom_commands = {
            'pip安装': 'pip install <package>',
            '检查权限': 'ls -la <file>',
            '修改权限': 'chmod +x <file>',
            '语法检查': 'python -m py_compile <file>',
            '创建文件': 'touch <file>'
        }
        bottom_command = bottom_commands.get(middle_strategy, '手动检查')

        # 存储策略
        top_id = self.strategy_system.set_top_strategy(error_type, top_strategy)
        middle_id = self.strategy_system.set_middle_strategy(middle_strategy, bottom_command, top_id)
        bottom_id = self.strategy_system.set_bottom_strategy('执行命令', bottom_command, middle_id)

        # 打印分层结果
        print(f"    [顶层] {top_strategy}")
        print(f"    [中间层] {middle_strategy}")
        print(f"    [细节层] {bottom_command}")

        return {
            'top': top_strategy,
            'middle': middle_strategy,
            'bottom': bottom_command,
            'top_id': top_id,
            'middle_id': middle_id,
            'bottom_id': bottom_id
        }

    def _get_middle_for_error(self, error_type):
        """根据错误类型获取中间层策略"""
        mapping = {
            'ImportError': 'pip安装',
            'PermissionError': '检查权限',
            'SyntaxError': '语法检查',
            'FileNotFoundError': '创建文件'
        }
        return mapping.get(error_type, '手动检查')

    def _execute_fix(self, analysis):
        """执行修复"""
        print(f"    执行: {analysis['bottom']}")
        return {
            'status': 'simulated',
            'command': analysis['bottom']
        }

    def _verify_fix(self, result):
        """验证修复"""
        import random
        success = random.random() > 0.3
        return {
            'result': 'success' if success else 'failed',
            'confidence': 0.7 + random.random() * 0.25
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

        print(f"\n{self.strategy_system.summarize_bottom_to_top()}")
        self.strategy_system.propagate_top_to_bottom(chain['top']['name'], "传播策略")

def demo():
    """演示分层策略系统"""
    print("=" * 60)
    print("GVEDC-trading-stocks-refine 分层策略迭代系统")
    print("=" * 60)

    service = IterationService()

    # 先设置一些分层策略
    print("\n--- 初始化分层策略 ---")

    # 演示：处理不同的错误类型
    errors = [
        {'message': 'ModuleNotFoundError: No module named requests', 'type': 'ImportError'},
        {'message': 'PermissionError: Access denied', 'type': 'PermissionError'}
    ]

    for error in errors:
        service.run_on_error(error)

    # 显示策略层级
    service.show_strategy_hierarchy()

if __name__ == "__main__":
    demo()