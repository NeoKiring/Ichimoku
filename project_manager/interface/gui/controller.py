"""
GUIコントローラー
GUIとProjectManager間の連携を担当
"""
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from ...core.manager import get_project_manager
from ...models import ProjectStatus, TaskStatus


class GUIController(QObject):
    """
    GUIとコア機能の橋渡しを行うコントローラークラス
    """
    
    # モデル変更通知用シグナル
    project_changed = Signal()
    phases_changed = Signal()
    processes_changed = Signal(str)  # フェーズIDをパラメータとして渡す
    tasks_changed = Signal(str, str)  # フェーズID, プロセスIDをパラメータとして渡す
    
    def __init__(self):
        """コントローラーの初期化"""
        super().__init__()
        self.manager = get_project_manager()
        self.current_phase_id = None
        self.current_process_id = None
    
    # ===== プロジェクト操作 =====
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        すべてのプロジェクト一覧を取得
        
        Returns:
            プロジェクト一覧
        """
        return self.manager.list_projects()
    
    def create_project(self, name: str, description: str = "") -> bool:
        """
        新しいプロジェクトを作成
        
        Args:
            name: プロジェクト名
            description: プロジェクトの説明
            
        Returns:
            作成が成功したかどうか
        """
        project = self.manager.create_project(name, description)
        if project:
            self.manager.current_project = project
            self.project_changed.emit()
            return True
        return False
    
    def load_project(self, project_id: str) -> bool:
        """
        プロジェクトを読み込む
        
        Args:
            project_id: 読み込むプロジェクトのID
            
        Returns:
            読み込みが成功したかどうか
        """
        project = self.manager.load_project(project_id)
        if project:
            self.project_changed.emit()
            self.phases_changed.emit()
            self.current_phase_id = None
            self.current_process_id = None
            return True
        return False
    
    def update_project(self, name: Optional[str] = None, description: Optional[str] = None, 
                    status: Optional[ProjectStatus] = None, manual_status: bool = True) -> bool:
        """
        現在のプロジェクトを更新
        
        Args:
            name: 新しいプロジェクト名（指定された場合）
            description: 新しいプロジェクトの説明（指定された場合）
            status: 新しいプロジェクト状態（指定された場合）
            manual_status: 状態が手動で設定されたかどうか
            
        Returns:
            更新が成功したかどうか
        """
        if not self.manager.current_project:
            return False
        
        result = self.manager.update_project(name, description, status, manual_status)
        if result:
            self.project_changed.emit()
        return result
    
    def set_project_on_hold(self) -> bool:
        """
        プロジェクトを保留状態に設定
        
        Returns:
            更新が成功したかどうか
        """
        result = self.manager.set_project_on_hold()
        if result:
            self.project_changed.emit()
        return result

    def set_project_cancelled(self) -> bool:
        """
        プロジェクトを中止状態に設定
        
        Returns:
            更新が成功したかどうか
        """
        result = self.manager.set_project_cancelled()
        if result:
            self.project_changed.emit()
        return result

    def release_project_status(self) -> bool:
        """
        プロジェクトの手動設定状態を解除し、自動判定に戻す
        
        Returns:
            更新が成功したかどうか
        """
        result = self.manager.release_project_status()
        if result:
            self.project_changed.emit()
        return result

    def delete_project(self, project_id: str) -> bool:
        """
        プロジェクトを削除
        
        Args:
            project_id: 削除するプロジェクトのID
            
        Returns:
            削除が成功したかどうか
        """
        result = self.manager.delete_project(project_id)
        if result:
            # 削除されたプロジェクトが現在のプロジェクトだった場合
            if self.manager.current_project is None:
                self.project_changed.emit()
        return result
    
    def get_current_project(self) -> Optional[Dict[str, Any]]:
        """
        現在のプロジェクト情報を取得
        
        Returns:
            プロジェクト情報、または None
        """
        if not self.manager.current_project:
            return None
        
        project = self.manager.current_project
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status.value,
            "progress": project.calculate_progress(),
            "start_date": project.get_start_date(),
            "end_date": project.get_end_date(),
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
    
    def get_full_project_data(self) -> Optional[Dict[str, Any]]:
        """
        プロジェクトの完全なデータを階層構造で取得
        
        Returns:
            プロジェクト全体のデータ、または None
        """
        if not self.manager.current_project:
            return None
        
        # プロジェクトの基本情報
        project_data = self.get_current_project()
        if not project_data:
            return None
        
        # フェーズ情報を追加
        project_data["phases"] = []
        phases = self.get_phases()
        
        for phase in phases:
            phase_data = self.get_phase_details(phase["id"])
            if phase_data:
                # プロセス情報を追加
                phase_data["processes"] = []
                processes = self.get_processes(phase["id"])
                
                for process in processes:
                    process_data = self.get_process_details(phase["id"], process["id"])
                    if process_data:
                        # タスク情報を追加
                        process_data["tasks"] = []
                        tasks = self.get_tasks(phase["id"], process["id"])
                        

    # ===== フェーズ操作 =====
    
    def get_phases(self) -> List[Dict[str, Any]]:
        """
        現在のプロジェクトのフェーズ一覧を取得
        
        Returns:
            フェーズ一覧
        """
        if not self.manager.current_project:
            return []
        
        return self.manager.get_phases()
    
    def create_phase(self, name: str, description: str = "") -> bool:
        """
        新しいフェーズを作成
        
        Args:
            name: フェーズ名
            description: フェーズの説明
            
        Returns:
            作成が成功したかどうか
        """
        phase = self.manager.add_phase(name, description)
        if phase:
            self.phases_changed.emit()
            return True
        return False
    
    def update_phase(self, phase_id: str, name: Optional[str] = None, 
                    description: Optional[str] = None, end_date: Optional[datetime] = None) -> bool:
        """
        フェーズを更新
        
        Args:
            phase_id: 更新するフェーズのID
            name: 新しいフェーズ名（指定された場合）
            description: 新しいフェーズの説明（指定された場合）
            end_date: 新しい終了日（指定された場合）
            
        Returns:
            更新が成功したかどうか
        """
        result = self.manager.update_phase(phase_id, name, description, end_date)
        if result:
            self.phases_changed.emit()
        return result
    
    def delete_phase(self, phase_id: str) -> bool:
        """
        フェーズを削除
        
        Args:
            phase_id: 削除するフェーズのID
            
        Returns:
            削除が成功したかどうか
        """
        result = self.manager.remove_phase(phase_id)
        if result:
            self.phases_changed.emit()
            # 削除されたフェーズが現在のフェーズだった場合
            if self.current_phase_id == phase_id:
                self.current_phase_id = None
                self.current_process_id = None
        return result
    
    def set_current_phase(self, phase_id: str):
        """
        現在のフェーズを設定
        
        Args:
            phase_id: フェーズID
        """
        self.current_phase_id = phase_id
        self.current_process_id = None
        self.processes_changed.emit(phase_id)
    
    def get_phase_details(self, phase_id: str) -> Optional[Dict[str, Any]]:
        """
        フェーズの詳細情報を取得
        
        Args:
            phase_id: フェーズID
            
        Returns:
            フェーズ情報、または None
        """
        if not self.manager.current_project:
            return None
        
        phase = self.manager.current_project.find_phase(phase_id)
        if not phase:
            return None
        
        return {
            "id": phase.id,
            "name": phase.name,
            "description": phase.description,
            "progress": phase.calculate_progress(),
            "start_date": phase.get_start_date(),
            "end_date": phase.get_end_date(),
            "created_at": phase.created_at,
            "updated_at": phase.updated_at
        }
    
    # ===== プロセス操作 =====
    
    def get_processes(self, phase_id: str) -> List[Dict[str, Any]]:
        """
        フェーズのプロセス一覧を取得
        
        Args:
            phase_id: フェーズID
            
        Returns:
            プロセス一覧
        """
        if not self.manager.current_project:
            return []
        
        return self.manager.get_processes(phase_id)

    def get_all_processes(self) -> List[Dict[str, Any]]:
        all_processes = []
        
        # 現在のプロジェクトIDを保存
        current_project_id = None
        if self.manager.current_project:
            current_project_id = self.manager.current_project.id
        
        # すべてのプロジェクトを取得
        projects = self.manager.list_projects()
        
        for project in projects:
            project_id = project["id"]
            project_name = project["name"]
            
            # プロジェクトを読み込み
            project_obj = self.manager.load_project(project_id)
            if not project_obj:
                continue
            
            # このプロジェクトのすべてのフェーズを取得
            phases = self.get_phases()
            
            for phase in phases:
                phase_id = phase["id"]
                phase_name = phase["name"]
                
                # このフェーズのすべてのプロセスを取得
                processes = self.get_processes(phase_id)
                
                # プロセスのループを開始する前に、processes配列が空でないか確認する
                if not processes:
                    continue
                    
                for process in processes:
                    # 各プロセスにプロジェクトとフェーズのコンテキストを追加
                    process_with_context = process.copy()
                    process_with_context["project_id"] = project_id
                    process_with_context["project_name"] = project_name
                    process_with_context["phase_id"] = phase_id
                    process_with_context["phase_name"] = phase_name
                    
                    # 期限までの残り日数を計算
                    end_date = process.get("end_date")
                    if end_date:
                        if isinstance(end_date, str):
                            try:
                                end_date = datetime.fromisoformat(end_date)
                            except ValueError:
                                # 解析できない場合はNoneとする
                                end_date = None
                        
                        # datetime型の場合のみ計算を実行
                        if isinstance(end_date, datetime):
                            today = datetime.now().date()
                            end_date_date = end_date.date()
                            days_remaining = (end_date_date - today).days
                            process_with_context["days_remaining"] = days_remaining
                        else:
                            # datetime型でない場合は残り日数をNoneに設定
                            process_with_context["days_remaining"] = None
                    else:
                        process_with_context["days_remaining"] = None
                    
                    all_processes.append(process_with_context)
            
            # 元のプロジェクトを復元
            if current_project_id:
                self.manager.load_project(current_project_id)
        
        return all_processes

    def create_process(self, phase_id: str, name: str, description: str = "", assignee: str = "") -> bool:
        """
        新しいプロセスを作成
        
        Args:
            phase_id: フェーズID
            name: プロセス名
            description: プロセスの説明
            assignee: 担当者
            
        Returns:
            作成が成功したかどうか
        """
        process = self.manager.add_process(phase_id, name, description, assignee)
        if process:
            self.processes_changed.emit(phase_id)
            return True
        return False
    
    def update_process(self, phase_id: str, process_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None, assignee: Optional[str] = None,
                      start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                      estimated_hours: Optional[float] = None, actual_hours: Optional[float] = None) -> bool:
        """
        プロセスを更新
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            name: 新しいプロセス名（指定された場合）
            description: 新しいプロセスの説明（指定された場合）
            assignee: 新しい担当者（指定された場合）
            start_date: 新しい開始日（指定された場合）
            end_date: 新しい終了日（指定された場合）
            estimated_hours: 新しい予想工数（指定された場合）
            actual_hours: 新しい実工数（指定された場合）
            
        Returns:
            更新が成功したかどうか
        """
        result = self.manager.update_process(
            phase_id, process_id, name, description, assignee,
            start_date, end_date, estimated_hours, actual_hours
        )
        if result:
            self.processes_changed.emit(phase_id)
        return result
    
    def delete_process(self, phase_id: str, process_id: str) -> bool:
        """
        プロセスを削除
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            
        Returns:
            削除が成功したかどうか
        """
        result = self.manager.remove_process(phase_id, process_id)
        if result:
            self.processes_changed.emit(phase_id)
            # 削除されたプロセスが現在のプロセスだった場合
            if self.current_process_id == process_id:
                self.current_process_id = None
        return result
    
    def set_current_process(self, phase_id: str, process_id: str):
        """
        現在のプロセスを設定
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
        """
        self.current_phase_id = phase_id
        self.current_process_id = process_id
        self.tasks_changed.emit(phase_id, process_id)
    
    def get_process_details(self, phase_id: str, process_id: str) -> Optional[Dict[str, Any]]:
        """
        プロセスの詳細情報を取得
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            
        Returns:
            プロセス情報、または None
        """
        if not self.manager.current_project:
            return None
        
        phase = self.manager.current_project.find_phase(phase_id)
        if not phase:
            return None
        
        process = phase.find_process(process_id)
        if not process:
            return None
        
        return {
            "id": process.id,
            "name": process.name,
            "description": process.description,
            "assignee": process.assignee,
            "progress": process.progress,
            "start_date": process.start_date,
            "end_date": process.end_date,
            "estimated_hours": process.estimated_hours,
            "actual_hours": process.actual_hours,
            "created_at": process.created_at,
            "updated_at": process.updated_at
        }
    
    # ===== タスク操作 =====
    
    def get_tasks(self, phase_id: str, process_id: str) -> List[Dict[str, Any]]:
        """
        プロセスのタスク一覧を取得
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            
        Returns:
            タスク一覧
        """
        if not self.manager.current_project:
            return []
        
        return self.manager.get_tasks(phase_id, process_id)
    
    def create_task(self, phase_id: str, process_id: str, name: str, 
                   description: str = "", status: TaskStatus = TaskStatus.NOT_STARTED) -> bool:
        """
        新しいタスクを作成
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            name: タスク名
            description: タスクの説明
            status: タスクの状態
            
        Returns:
            作成が成功したかどうか
        """
        task = self.manager.add_task(phase_id, process_id, name, description, status)
        if task:
            self.tasks_changed.emit(phase_id, process_id)
            self.processes_changed.emit(phase_id)  # 進捗率が変わるため
            self.phases_changed.emit()  # フェーズの進捗率も変わるため
            self.project_changed.emit()  # プロジェクトの進捗率も変わるため
            return True
        return False
    
    def update_task(self, phase_id: str, process_id: str, task_id: str, name: Optional[str] = None, 
                   description: Optional[str] = None, status: Optional[TaskStatus] = None) -> bool:
        """
        タスクを更新
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            task_id: タスクID
            name: 新しいタスク名（指定された場合）
            description: 新しいタスクの説明（指定された場合）
            status: 新しいタスク状態（指定された場合）
            
        Returns:
            更新が成功したかどうか
        """
        result = self.manager.update_task(
            phase_id, process_id, task_id, name, description, status
        )
        if result:
            self.tasks_changed.emit(phase_id, process_id)
            if status is not None:  # 状態が変更された場合は上位階層の進捗率も更新
                self.processes_changed.emit(phase_id)
                self.phases_changed.emit()
                self.project_changed.emit()
        return result
    
    def delete_task(self, phase_id: str, process_id: str, task_id: str) -> bool:
        """
        タスクを削除
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            task_id: タスクID
            
        Returns:
            削除が成功したかどうか
        """
        result = self.manager.remove_task(phase_id, process_id, task_id)
        if result:
            self.tasks_changed.emit(phase_id, process_id)
            self.processes_changed.emit(phase_id)  # 進捗率が変わるため
            self.phases_changed.emit()  # フェーズの進捗率も変わるため
            self.project_changed.emit()  # プロジェクトの進捗率も変わるため
        return result
    
    def get_task_details(self, phase_id: str, process_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスクの詳細情報を取得
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            task_id: タスクID
            
        Returns:
            タスク情報、または None
        """
        if not self.manager.current_project:
            return None
        
        phase = self.manager.current_project.find_phase(phase_id)
        if not phase:
            return None
        
        process = phase.find_process(process_id)
        if not process:
            return None
        
        task = process.find_task(task_id)
        if not task:
            return None
        
        return {
            "id": task.id,
            "name": task.name,
            "description": task.description,
            "status": task.status.value,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
    
    def get_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        タスクの履歴を取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスクの履歴リスト
        """
        if not self.manager.current_project:
            return []
        
        return self.manager.get_entity_history(task_id)
    
    # ===== 通知操作 =====
    def get_notifications(self) -> List[Dict[str, Any]]:
        """
        すべての通知を取得
        
        Returns:
            通知のリスト
        """
        from ...core.notification_manager import get_notification_manager
        
        notification_manager = get_notification_manager()
        notifications = notification_manager.get_all_notifications()
        
        return [notification.to_dict() for notification in notifications]

    def get_unread_notifications_count(self) -> int:
        """
        未読通知の数を取得
        
        Returns:
            未読通知の数
        """
        from ...core.notification_manager import get_notification_manager
        
        notification_manager = get_notification_manager()
        return len(notification_manager.get_unread_notifications())

    def check_for_notifications(self) -> int:
        """
        新しい通知をチェック
        
        Returns:
            生成された新しい通知の数
        """
        from ...core.notification_manager import get_notification_manager
        
        notification_manager = get_notification_manager()
        return notification_manager.generate_notifications()
