"""
コマンドラインインターフェース
プロジェクト管理システムのCUIインターフェースを提供
"""
import cmd
import sys
import os
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..core.manager import get_project_manager
from ..models import ProjectStatus, TaskStatus


class ProjectManagerCLI(cmd.Cmd):
    """
    プロジェクト管理システムのコマンドラインインターフェース
    対話式のシェルを提供し、プロジェクト管理操作を実行
    """
    
    intro = """
======================================================
プロジェクト管理システム v1.0
======================================================
help でコマンド一覧を表示できます
quit または exit で終了します
------------------------------------------------------
"""
    prompt = "(PM) > "
    
    def __init__(self):
        """CLIの初期化"""
        super().__init__()
        self.manager = get_project_manager()
        
        # 端末の幅を取得
        self.terminal_width = shutil.get_terminal_size().columns
    
    # ===== ユーティリティメソッド =====
    
    def _print_header(self, title: str) -> None:
        """
        見出しを表示
        
        Args:
            title: 見出しタイトル
        """
        print("\n" + "=" * self.terminal_width)
        print(f"{title}")
        print("-" * self.terminal_width)
    
    def _print_table(self, headers: List[str], rows: List[List[str]]) -> None:
        """
        表形式でデータを表示
        
        Args:
            headers: 列見出しのリスト
            rows: 行データのリスト
        """
        if not rows:
            print("データがありません")
            return
        
        # 各列の幅を計算
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # ヘッダーを表示
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        print(header_line)
        print("-" * len(header_line))
        
        # データ行を表示
        for row in rows:
            row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(row_line)
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """
        日付文字列をフォーマット
        
        Args:
            date_str: ISO形式の日付文字列、またはNone
            
        Returns:
            フォーマットされた日付文字列、または未設定を示す文字列
        """
        if not date_str:
            return "未設定"
        
        try:
            date = datetime.fromisoformat(date_str)
            return date.strftime("%Y-%m-%d")
        except:
            return date_str
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        日付文字列を解析
        
        Args:
            date_str: 日付文字列 (YYYY-MM-DD形式)
            
        Returns:
            解析された日付、無効な場合はNone
        """
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"無効な日付形式です: {date_str} (YYYY-MM-DD形式を使用してください)")
            return None
    
    def _get_entity_path(self) -> str:
        """
        現在のエンティティパスを取得
        
        Returns:
            エンティティパスを示す文字列
        """
        path = "/"
        if self.manager.current_project:
            path += self.manager.current_project.name
        return path
    
    def _update_prompt(self) -> None:
        """プロンプトを更新"""
        path = self._get_entity_path()
        self.prompt = f"(PM {path}) > "
    
    # ===== コマンド実装 =====
    
    def do_quit(self, arg: str) -> bool:
        """
        プログラムを終了
        
        Usage: quit
        """
        print("プロジェクト管理システムを終了します")
        return True
    
    def do_exit(self, arg: str) -> bool:
        """
        プログラムを終了
        
        Usage: exit
        """
        return self.do_quit(arg)
    
    def do_help(self, arg: str) -> None:
        """
        利用可能なコマンドとその使用方法を表示
        
        Usage: help [command]
        """
        if arg:
            # 特定のコマンドのヘルプを表示
            super().do_help(arg)
        else:
            # カテゴリー別にコマンドを整理して表示
            self._print_header("利用可能なコマンド")
            
            command_categories = {
                "プロジェクト操作": [
                    "project_list", "project_create", "project_load", 
                    "project_info", "project_update", "project_delete"
                ],
                "フェーズ操作": [
                    "phase_list", "phase_create", "phase_info", 
                    "phase_update", "phase_delete"
                ],
                "プロセス操作": [
                    "process_list", "process_create", "process_info", 
                    "process_update", "process_delete"
                ],
                "タスク操作": [
                    "task_list", "task_create", "task_info", 
                    "task_update", "task_delete"
                ],
                "その他": [
                    "help", "quit", "exit"
                ]
            }
            
            for category, commands in command_categories.items():
                print(f"\n{category}:")
                for cmd_name in commands:
                    cmd_func = getattr(self, f"do_{cmd_name}")
                    cmd_doc = cmd_func.__doc__.split("\n")[0] if cmd_func.__doc__ else ""
                    print(f"  {cmd_name.ljust(15)} - {cmd_doc}")
    
    # ===== プロジェクト操作 =====
    
    def do_project_list(self, arg: str) -> None:
        """
        すべてのプロジェクトを一覧表示
        
        Usage: project_list
        """
        projects = self.manager.list_projects()
        
        self._print_header("プロジェクト一覧")
        
        if not projects:
            print("プロジェクトはありません")
            return
        
        headers = ["ID", "名前", "状態", "進捗率", "更新日時"]
        rows = []
        
        for project in projects:
            rows.append([
                project["id"][:8] + "...",  # IDは短く表示
                project["name"],
                project["status"],
                f"{project['progress']:.1f}%",
                datetime.fromisoformat(project["updated_at"]).strftime("%Y-%m-%d %H:%M")
            ])
        
        self._print_table(headers, rows)
    
    def do_project_create(self, arg: str) -> None:
        """
        新しいプロジェクトを作成
        
        Usage: project_create <名前> [説明]
        """
        args = arg.split(" ", 1)
        
        if not args[0]:
            print("プロジェクト名を指定してください")
            print("Usage: project_create <名前> [説明]")
            return
        
        name = args[0]
        description = args[1] if len(args) > 1 else ""
        
        project = self.manager.create_project(name, description)
        self.manager.current_project = project
        self._update_prompt()
        
        print(f"プロジェクト '{name}' を作成しました (ID: {project.id})")
    
    def do_project_load(self, arg: str) -> None:
        """
        プロジェクトを読み込む
        
        Usage: project_load <プロジェクトID>
        """
        if not arg:
            print("プロジェクトIDを指定してください")
            print("Usage: project_load <プロジェクトID>")
            return
        
        project = self.manager.load_project(arg)
        
        if project:
            self._update_prompt()
            print(f"プロジェクト '{project.name}' を読み込みました")
        else:
            print(f"プロジェクト ID '{arg}' が見つかりません")
    
    def do_project_info(self, arg: str) -> None:
        """
        現在のプロジェクトの詳細情報を表示
        
        Usage: project_info
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        project = self.manager.current_project
        
        self._print_header(f"プロジェクト: {project.name}")
        
        print(f"ID: {project.id}")
        print(f"説明: {project.description}")
        print(f"状態: {project.status.value}")
        print(f"進捗率: {project.calculate_progress():.1f}%")
        
        start_date = project.get_start_date()
        end_date = project.get_end_date()
        
        print(f"開始日: {start_date.strftime('%Y-%m-%d') if start_date else '未設定'}")
        print(f"終了日: {end_date.strftime('%Y-%m-%d') if end_date else '未設定'}")
        print(f"作成日時: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"更新日時: {project.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        phases = project.get_phases()
        print(f"\nフェーズ数: {len(phases)}")
        
        if phases:
            print("\nフェーズ一覧:")
            for idx, phase in enumerate(phases, 1):
                print(f"  {idx}. {phase.name} - 進捗: {phase.calculate_progress():.1f}%")
    
    def do_project_update(self, arg: str) -> None:
        """
        現在のプロジェクトを更新
        
        Usage: project_update [名前] [説明] [状態]
        状態: 未着手, 進行中, 完了, 中止, 保留
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        print("プロジェクトの更新（変更しない項目は空欄で Enter）")
        
        # 現在の値を表示
        current = self.manager.current_project
        print(f"現在の名前: {current.name}")
        print(f"現在の説明: {current.description}")
        print(f"現在の状態: {current.status.value}")
        
        # 新しい値を入力
        name = input("新しい名前: ").strip()
        description = input("新しい説明: ").strip()
        
        status_map = {
            "1": ProjectStatus.NOT_STARTED,
            "2": ProjectStatus.IN_PROGRESS,
            "3": ProjectStatus.COMPLETED,
            "4": ProjectStatus.CANCELLED,
            "5": ProjectStatus.ON_HOLD
        }
        
        print("\n状態の選択:")
        print("1. 未着手")
        print("2. 進行中")
        print("3. 完了")
        print("4. 中止")
        print("5. 保留")
        status_input = input("選択 (1-5): ").strip()
        
        # パラメータを準備
        update_params = {}
        if name:
            update_params["name"] = name
        if description:
            update_params["description"] = description
        if status_input in status_map:
            update_params["status"] = status_map[status_input]
        
        # 更新実行
        if update_params:
            if self.manager.update_project(**update_params):
                self._update_prompt()
                print("プロジェクトを更新しました")
            else:
                print("プロジェクトの更新に失敗しました")
        else:
            print("変更はありませんでした")
    
    def do_project_delete(self, arg: str) -> None:
        """
        プロジェクトを削除
        
        Usage: project_delete <プロジェクトID>
        """
        if not arg:
            print("プロジェクトIDを指定してください")
            print("Usage: project_delete <プロジェクトID>")
            return
        
        # 削除の確認
        confirm = input(f"プロジェクト ID '{arg}' を削除します。この操作は元に戻せません。続行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("削除をキャンセルしました")
            return
        
        if self.manager.delete_project(arg):
            print(f"プロジェクト ID '{arg}' を削除しました")
            
            # 削除したプロジェクトが現在のプロジェクトだった場合、プロンプトを更新
            if self.manager.current_project is None:
                self._update_prompt()
        else:
            print(f"プロジェクト ID '{arg}' の削除に失敗しました")
    
    # ===== フェーズ操作 =====
    
    def do_phase_list(self, arg: str) -> None:
        """
        現在のプロジェクトのフェーズを一覧表示
        
        Usage: phase_list
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        phases = self.manager.get_phases()
        
        self._print_header(f"プロジェクト '{self.manager.current_project.name}' のフェーズ一覧")
        
        if not phases:
            print("フェーズはありません")
            return
        
        headers = ["ID", "名前", "進捗率", "開始日", "終了日", "プロセス数"]
        rows = []
        
        for phase in phases:
            rows.append([
                phase["id"][:8] + "...",  # IDは短く表示
                phase["name"],
                f"{phase['progress']:.1f}%",
                self._format_date(phase["start_date"]),
                self._format_date(phase["end_date"]),
                phase["process_count"]
            ])
        
        self._print_table(headers, rows)
    
    def do_phase_create(self, arg: str) -> None:
        """
        現在のプロジェクトに新しいフェーズを作成
        
        Usage: phase_create <名前> [説明]
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 1)
        
        if not args[0]:
            print("フェーズ名を指定してください")
            print("Usage: phase_create <名前> [説明]")
            return
        
        name = args[0]
        description = args[1] if len(args) > 1 else ""
        
        phase = self.manager.add_phase(name, description)
        
        if phase:
            print(f"フェーズ '{name}' を作成しました (ID: {phase.id})")
        else:
            print("フェーズの作成に失敗しました")
    
    def do_phase_info(self, arg: str) -> None:
        """
        フェーズの詳細情報を表示
        
        Usage: phase_info <フェーズID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        if not arg:
            print("フェーズIDを指定してください")
            print("Usage: phase_info <フェーズID>")
            return
        
        phase = self.manager.current_project.find_phase(arg)
        
        if not phase:
            print(f"フェーズ ID '{arg}' が見つかりません")
            return
        
        self._print_header(f"フェーズ: {phase.name}")
        
        print(f"ID: {phase.id}")
        print(f"説明: {phase.description}")
        print(f"進捗率: {phase.calculate_progress():.1f}%")
        
        start_date = phase.get_start_date()
        end_date = phase.get_end_date()
        
        print(f"開始日: {start_date.strftime('%Y-%m-%d') if start_date else '未設定'}")
        print(f"終了日: {end_date.strftime('%Y-%m-%d') if end_date else '未設定'}")
        print(f"作成日時: {phase.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"更新日時: {phase.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        processes = phase.get_processes()
        print(f"\nプロセス数: {len(processes)}")
        
        if processes:
            print("\nプロセス一覧:")
            for idx, process in enumerate(processes, 1):
                print(f"  {idx}. {process.name} - 担当: {process.assignee or '未割当'} - 進捗: {process.progress:.1f}%")
    
    def do_phase_update(self, arg: str) -> None:
        """
        フェーズを更新
        
        Usage: phase_update <フェーズID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        if not arg:
            print("フェーズIDを指定してください")
            print("Usage: phase_update <フェーズID>")
            return
        
        phase = self.manager.current_project.find_phase(arg)
        
        if not phase:
            print(f"フェーズ ID '{arg}' が見つかりません")
            return
        
        print("フェーズの更新（変更しない項目は空欄で Enter）")
        
        # 現在の値を表示
        print(f"現在の名前: {phase.name}")
        print(f"現在の説明: {phase.description}")
        end_date = phase.get_end_date()
        print(f"現在の終了日: {end_date.strftime('%Y-%m-%d') if end_date else '未設定'}")
        
        # 新しい値を入力
        name = input("新しい名前: ").strip()
        description = input("新しい説明: ").strip()
        end_date_str = input("新しい終了日 (YYYY-MM-DD): ").strip()
        
        # パラメータを準備
        update_params = {
            "phase_id": arg
        }
        
        if name:
            update_params["name"] = name
        if description:
            update_params["description"] = description
        if end_date_str:
            end_date = self._parse_date(end_date_str)
            if end_date:
                update_params["end_date"] = end_date
        
        # 更新実行
        if len(update_params) > 1:  # phase_id以外のパラメータがある場合
            if self.manager.update_phase(**update_params):
                print("フェーズを更新しました")
            else:
                print("フェーズの更新に失敗しました")
        else:
            print("変更はありませんでした")
    
    def do_phase_delete(self, arg: str) -> None:
        """
        フェーズを削除
        
        Usage: phase_delete <フェーズID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        if not arg:
            print("フェーズIDを指定してください")
            print("Usage: phase_delete <フェーズID>")
            return
        
        phase = self.manager.current_project.find_phase(arg)
        
        if not phase:
            print(f"フェーズ ID '{arg}' が見つかりません")
            return
        
        # 削除の確認
        confirm = input(f"フェーズ '{phase.name}' を削除します。この操作は元に戻せません。続行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("削除をキャンセルしました")
            return
        
        if self.manager.remove_phase(arg):
            print(f"フェーズ '{phase.name}' を削除しました")
        else:
            print(f"フェーズ ID '{arg}' の削除に失敗しました")
    
    # ===== プロセス操作 =====
    
    def do_process_list(self, arg: str) -> None:
        """
        フェーズのプロセスを一覧表示
        
        Usage: process_list <フェーズID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        if not arg:
            print("フェーズIDを指定してください")
            print("Usage: process_list <フェーズID>")
            return
        
        phase = self.manager.current_project.find_phase(arg)
        
        if not phase:
            print(f"フェーズ ID '{arg}' が見つかりません")
            return
        
        processes = self.manager.get_processes(arg)
        
        self._print_header(f"フェーズ '{phase.name}' のプロセス一覧")
        
        if not processes:
            print("プロセスはありません")
            return
        
        headers = ["ID", "名前", "担当者", "進捗率", "開始日", "終了日", "予想工数", "実工数", "タスク数"]
        rows = []
        
        for process in processes:
            rows.append([
                process["id"][:8] + "...",  # IDは短く表示
                process["name"],
                process["assignee"] or "未割当",
                f"{process['progress']:.1f}%",
                self._format_date(process["start_date"]),
                self._format_date(process["end_date"]),
                f"{process['estimated_hours']:.1f}h",
                f"{process['actual_hours']:.1f}h",
                process["task_count"]
            ])
        
        self._print_table(headers, rows)
    
    def do_process_create(self, arg: str) -> None:
        """
        フェーズに新しいプロセスを作成
        
        Usage: process_create <フェーズID> <名前> [説明] [担当者]
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 3)
        
        if len(args) < 2 or not args[0] or not args[1]:
            print("フェーズIDとプロセス名を指定してください")
            print("Usage: process_create <フェーズID> <名前> [説明] [担当者]")
            return
        
        phase_id = args[0]
        name = args[1]
        description = args[2] if len(args) > 2 else ""
        assignee = args[3] if len(args) > 3 else ""
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = self.manager.add_process(phase_id, name, description, assignee)
        
        if process:
            print(f"プロセス '{name}' を作成しました (ID: {process.id})")
        else:
            print("プロセスの作成に失敗しました")
    
    def do_process_info(self, arg: str) -> None:
        """
        プロセスの詳細情報を表示
        
        Usage: process_info <フェーズID> <プロセスID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 1)
        
        if len(args) < 2 or not args[0] or not args[1]:
            print("フェーズIDとプロセスIDを指定してください")
            print("Usage: process_info <フェーズID> <プロセスID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        self._print_header(f"プロセス: {process.name}")
        
        print(f"ID: {process.id}")
        print(f"説明: {process.description}")
        print(f"担当者: {process.assignee or '未割当'}")
        print(f"進捗率: {process.progress:.1f}%")
        
        start_date = process.start_date
        end_date = process.end_date
        
        print(f"開始日: {start_date.strftime('%Y-%m-%d') if start_date else '未設定'}")
        print(f"終了日: {end_date.strftime('%Y-%m-%d') if end_date else '未設定'}")
        print(f"予想工数: {process.estimated_hours:.1f}h")
        print(f"実工数: {process.actual_hours:.1f}h")
        print(f"作成日時: {process.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"更新日時: {process.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        tasks = process.get_tasks()
        print(f"\nタスク数: {len(tasks)}")
        
        if tasks:
            print("\nタスク一覧:")
            for idx, task in enumerate(tasks, 1):
                print(f"  {idx}. {task.name} - 状態: {task.status.value}")
    
    def do_process_update(self, arg: str) -> None:
        """
        プロセスを更新
        
        Usage: process_update <フェーズID> <プロセスID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 1)
        
        if len(args) < 2 or not args[0] or not args[1]:
            print("フェーズIDとプロセスIDを指定してください")
            print("Usage: process_update <フェーズID> <プロセスID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        print("プロセスの更新（変更しない項目は空欄で Enter）")
        
        # 現在の値を表示
        print(f"現在の名前: {process.name}")
        print(f"現在の説明: {process.description}")
        print(f"現在の担当者: {process.assignee or '未割当'}")
        start_date = process.start_date
        print(f"現在の開始日: {start_date.strftime('%Y-%m-%d') if start_date else '未設定'}")
        end_date = process.end_date
        print(f"現在の終了日: {end_date.strftime('%Y-%m-%d') if end_date else '未設定'}")
        print(f"現在の予想工数: {process.estimated_hours:.1f}h")
        print(f"現在の実工数: {process.actual_hours:.1f}h")
        
        # 新しい値を入力
        name = input("新しい名前: ").strip()
        description = input("新しい説明: ").strip()
        assignee = input("新しい担当者: ").strip()
        start_date_str = input("新しい開始日 (YYYY-MM-DD): ").strip()
        end_date_str = input("新しい終了日 (YYYY-MM-DD): ").strip()
        estimated_hours_str = input("新しい予想工数 (時間): ").strip()
        actual_hours_str = input("新しい実工数 (時間): ").strip()
        
        # パラメータを準備
        update_params = {
            "phase_id": phase_id,
            "process_id": process_id
        }
        
        if name:
            update_params["name"] = name
        if description:
            update_params["description"] = description
        if assignee:
            update_params["assignee"] = assignee
        if start_date_str:
            start_date = self._parse_date(start_date_str)
            if start_date:
                update_params["start_date"] = start_date
        if end_date_str:
            end_date = self._parse_date(end_date_str)
            if end_date:
                update_params["end_date"] = end_date
        if estimated_hours_str:
            try:
                estimated_hours = float(estimated_hours_str)
                update_params["estimated_hours"] = estimated_hours
            except ValueError:
                print("予想工数には数値を入力してください")
        if actual_hours_str:
            try:
                actual_hours = float(actual_hours_str)
                update_params["actual_hours"] = actual_hours
            except ValueError:
                print("実工数には数値を入力してください")
        
        # 更新実行
        if len(update_params) > 2:  # 必須パラメータ以外のパラメータがある場合
            if self.manager.update_process(**update_params):
                print("プロセスを更新しました")
            else:
                print("プロセスの更新に失敗しました")
        else:
            print("変更はありませんでした")
    
    def do_process_delete(self, arg: str) -> None:
        """
        プロセスを削除
        
        Usage: process_delete <フェーズID> <プロセスID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 1)
        
        if len(args) < 2 or not args[0] or not args[1]:
            print("フェーズIDとプロセスIDを指定してください")
            print("Usage: process_delete <フェーズID> <プロセスID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        # 削除の確認
        confirm = input(f"プロセス '{process.name}' を削除します。この操作は元に戻せません。続行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("削除をキャンセルしました")
            return
        
        if self.manager.remove_process(phase_id, process_id):
            print(f"プロセス '{process.name}' を削除しました")
        else:
            print(f"プロセス ID '{process_id}' の削除に失敗しました")
    
    # ===== タスク操作 =====
    
    def do_task_list(self, arg: str) -> None:
        """
        プロセスのタスクを一覧表示
        
        Usage: task_list <フェーズID> <プロセスID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 1)
        
        if len(args) < 2 or not args[0] or not args[1]:
            print("フェーズIDとプロセスIDを指定してください")
            print("Usage: task_list <フェーズID> <プロセスID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        tasks = self.manager.get_tasks(phase_id, process_id)
        
        self._print_header(f"プロセス '{process.name}' のタスク一覧")
        
        if not tasks:
            print("タスクはありません")
            return
        
        headers = ["ID", "名前", "状態", "作成日時", "更新日時"]
        rows = []
        
        for task in tasks:
            rows.append([
                task["id"][:8] + "...",  # IDは短く表示
                task["name"],
                task["status"],
                datetime.fromisoformat(task["created_at"]).strftime("%Y-%m-%d"),
                datetime.fromisoformat(task["updated_at"]).strftime("%Y-%m-%d")
            ])
        
        self._print_table(headers, rows)
    
    def do_task_create(self, arg: str) -> None:
        """
        プロセスに新しいタスクを作成
        
        Usage: task_create <フェーズID> <プロセスID> <名前> [説明] [状態]
        状態: 未着手, 進行中, 完了, 対応不能
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 4)
        
        if len(args) < 3 or not args[0] or not args[1] or not args[2]:
            print("フェーズID、プロセスID、タスク名を指定してください")
            print("Usage: task_create <フェーズID> <プロセスID> <名前> [説明] [状態]")
            return
        
        phase_id = args[0]
        process_id = args[1]
        name = args[2]
        description = args[3] if len(args) > 3 else ""
        status_str = args[4] if len(args) > 4 else ""
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        status = TaskStatus.NOT_STARTED  # デフォルト値
        
        if status_str:
            status_map = {
                "未着手": TaskStatus.NOT_STARTED,
                "進行中": TaskStatus.IN_PROGRESS,
                "完了": TaskStatus.COMPLETED,
                "対応不能": TaskStatus.IMPOSSIBLE
            }
            
            if status_str in status_map:
                status = status_map[status_str]
            else:
                print(f"無効な状態です: {status_str}")
                print("有効な状態: 未着手, 進行中, 完了, 対応不能")
                return
        
        task = self.manager.add_task(phase_id, process_id, name, description, status)
        
        if task:
            print(f"タスク '{name}' を作成しました (ID: {task.id})")
        else:
            print("タスクの作成に失敗しました")
    
    def do_task_info(self, arg: str) -> None:
        """
        タスクの詳細情報を表示
        
        Usage: task_info <フェーズID> <プロセスID> <タスクID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 2)
        
        if len(args) < 3 or not args[0] or not args[1] or not args[2]:
            print("フェーズID、プロセスID、タスクIDを指定してください")
            print("Usage: task_info <フェーズID> <プロセスID> <タスクID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        task_id = args[2]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        task = process.find_task(task_id)
        
        if not task:
            print(f"タスク ID '{task_id}' が見つかりません")
            return
        
        self._print_header(f"タスク: {task.name}")
        
        print(f"ID: {task.id}")
        print(f"説明: {task.description}")
        print(f"状態: {task.status.value}")
        print(f"作成日時: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"更新日時: {task.updated_at.strftime('%Y-%m-%d %H:%M')}")
        
        # タスクの履歴を表示
        history = self.manager.get_entity_history(task.id)
        
        if history:
            print("\n変更履歴:")
            for idx, entry in enumerate(history, 1):
                timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                print(f"  {idx}. {timestamp} - {entry['action_type']}")
                
                if "details" in entry and "status" in entry["details"]:
                    status_change = entry["details"]["status"]
                    print(f"     状態変更: {status_change['old']} -> {status_change['new']}")
    
    def do_task_update(self, arg: str) -> None:
        """
        タスクを更新
        
        Usage: task_update <フェーズID> <プロセスID> <タスクID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 2)
        
        if len(args) < 3 or not args[0] or not args[1] or not args[2]:
            print("フェーズID、プロセスID、タスクIDを指定してください")
            print("Usage: task_update <フェーズID> <プロセスID> <タスクID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        task_id = args[2]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        task = process.find_task(task_id)
        
        if not task:
            print(f"タスク ID '{task_id}' が見つかりません")
            return
        
        print("タスクの更新（変更しない項目は空欄で Enter）")
        
        # 現在の値を表示
        print(f"現在の名前: {task.name}")
        print(f"現在の説明: {task.description}")
        print(f"現在の状態: {task.status.value}")
        
        # 新しい値を入力
        name = input("新しい名前: ").strip()
        description = input("新しい説明: ").strip()
        
        status_map = {
            "1": TaskStatus.NOT_STARTED,
            "2": TaskStatus.IN_PROGRESS,
            "3": TaskStatus.COMPLETED,
            "4": TaskStatus.IMPOSSIBLE
        }
        
        print("\n状態の選択:")
        print("1. 未着手")
        print("2. 進行中")
        print("3. 完了")
        print("4. 対応不能")
        status_input = input("選択 (1-4): ").strip()
        
        # パラメータを準備
        update_params = {
            "phase_id": phase_id,
            "process_id": process_id,
            "task_id": task_id
        }
        
        if name:
            update_params["name"] = name
        if description:
            update_params["description"] = description
        if status_input in status_map:
            update_params["status"] = status_map[status_input]
        
        # 更新実行
        if len(update_params) > 3:  # 必須パラメータ以外のパラメータがある場合
            if self.manager.update_task(**update_params):
                print("タスクを更新しました")
            else:
                print("タスクの更新に失敗しました")
        else:
            print("変更はありませんでした")
    
    def do_task_delete(self, arg: str) -> None:
        """
        タスクを削除
        
        Usage: task_delete <フェーズID> <プロセスID> <タスクID>
        """
        if not self.manager.current_project:
            print("プロジェクトが読み込まれていません")
            return
        
        args = arg.split(" ", 2)
        
        if len(args) < 3 or not args[0] or not args[1] or not args[2]:
            print("フェーズID、プロセスID、タスクIDを指定してください")
            print("Usage: task_delete <フェーズID> <プロセスID> <タスクID>")
            return
        
        phase_id = args[0]
        process_id = args[1]
        task_id = args[2]
        
        phase = self.manager.current_project.find_phase(phase_id)
        
        if not phase:
            print(f"フェーズ ID '{phase_id}' が見つかりません")
            return
        
        process = phase.find_process(process_id)
        
        if not process:
            print(f"プロセス ID '{process_id}' が見つかりません")
            return
        
        task = process.find_task(task_id)
        
        if not task:
            print(f"タスク ID '{task_id}' が見つかりません")
            return
        
        # 削除の確認
        confirm = input(f"タスク '{task.name}' を削除します。この操作は元に戻せません。続行しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("削除をキャンセルしました")
            return
        
        if self.manager.remove_task(phase_id, process_id, task_id):
            print(f"タスク '{task.name}' を削除しました")
        else:
            print(f"タスク ID '{task_id}' の削除に失敗しました")


def run_cli():
    """
    CLIを実行
    
    Returns:
        終了コード
    """
    try:
        # 端末サイズに合わせてインスタンスを作成
        cli = ProjectManagerCLI()
        cli.cmdloop()
        return 0
    except KeyboardInterrupt:
        print("\nプロジェクト管理システムを終了します")
        return 0
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return 1
