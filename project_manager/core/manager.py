"""
プロジェクト管理コア
プロジェクト管理システムのコアロジックを担当
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..models import Project, Phase, Process, Task, ProjectStatus, TaskStatus
from ..storage.data_store import get_data_store
from ..core.logger import get_logger
from ..core.error_handler import with_error_logging, LogLevel

class ProjectManager:
    """
    プロジェクト管理のコア機能を提供するクラス
    プロジェクト、フェーズ、プロセス、タスクの管理を統合
    """
    
    def __init__(self):
        """プロジェクトマネージャーの初期化"""
        self.data_store = get_data_store()
        self.logger = get_logger()
        self.current_project = None
    
    # ===== プロジェクト操作 =====
    
    def create_project(self, name: str, description: str = "") -> Project:
        """
        新しいプロジェクトを作成
        
        Args:
            name: プロジェクト名
            description: プロジェクトの説明
            
        Returns:
            作成されたプロジェクト
        """
        project = Project(name=name, description=description)
        self.data_store.save_project(project)
        
        self.logger.log_action(
            action_type="create",
            entity_type="Project",
            entity_id=project.id,
            details={"name": name}
        )
        
        return project
    
    # デコレータを使用してエラーハンドリングを追加
    @with_error_logging(level=LogLevel.ERROR, reraise=True)
    def load_project(self, project_id: str) -> Optional[Project]:
        """
        プロジェクトを読み込み、現在のプロジェクトとして設定
        
        Args:
            project_id: 読み込むプロジェクトのID
            
        Returns:
            読み込まれたプロジェクト、存在しない場合はNone
        """
        project = self.data_store.load_project(project_id)
        if project:
            self.current_project = project
            
            self.logger.log_action(
                action_type="load",
                entity_type="Project",
                entity_id=project.id,
                details={"name": project.name}
            )
        
        return project
    
    def save_current_project(self) -> bool:
        """
        現在のプロジェクトを保存
        
        Returns:
            保存が成功したかどうか
        """
        if not self.current_project:
            return False
        
        success = self.data_store.save_project(self.current_project)
        
        if success:
            self.logger.log_action(
                action_type="save",
                entity_type="Project",
                entity_id=self.current_project.id,
                details={"name": self.current_project.name}
            )
        
        return success
    
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
        if not self.current_project:
            return False
        
        details = {}
        
        if name is not None or description is not None:
            self.current_project.update(name, description)
            if name:
                details["name"] = name
            if description:
                details["description"] = description
        
        if status is not None:
            self.current_project.update_status(status, manual_status)
            details["status"] = status.value
            details["manual_status"] = manual_status
        elif not manual_status and not self.current_project.is_status_manual:
            # 自動判定の場合、現在のステータスを更新
            auto_status = self.current_project.determine_status()
            if auto_status != self.current_project.status:
                self.current_project.update_status(auto_status, False)
                details["status"] = auto_status.value
                details["manual_status"] = False
        
        success = self.save_current_project()
        
        if success and details:
            self.logger.log_action(
                action_type="update",
                entity_type="Project",
                entity_id=self.current_project.id,
                details=details
            )
        
        return success
    
    def set_project_on_hold(self) -> bool:
        """
        プロジェクトを保留状態に設定
        
        Returns:
            更新が成功したかどうか
        """
        return self.update_project(status=ProjectStatus.ON_HOLD, manual_status=True)

    def set_project_cancelled(self) -> bool:
        """
        プロジェクトを中止状態に設定
        
        Returns:
            更新が成功したかどうか
        """
        return self.update_project(status=ProjectStatus.CANCELLED, manual_status=True)

    def release_project_status(self) -> bool:
        """
        プロジェクトの手動設定状態を解除し、自動判定に戻す
        
        Returns:
            更新が成功したかどうか
        """
        if not self.current_project:
            return False
        
        self.current_project.release_manual_status()
        success = self.save_current_project()
        
        if success:
            self.logger.log_action(
                action_type="update",
                entity_type="Project",
                entity_id=self.current_project.id,
                details={"status": self.current_project.status.value, "manual_status": False}
            )
        
        return success

    def delete_project(self, project_id: str) -> bool:
        """
        プロジェクトを削除
        
        Args:
            project_id: 削除するプロジェクトのID
            
        Returns:
            削除が成功したかどうか
        """
        # 現在のプロジェクトの場合はクリア
        if self.current_project and self.current_project.id == project_id:
            self.current_project = None
        
        success = self.data_store.delete_project(project_id)
        
        if success:
            self.logger.log_action(
                action_type="delete",
                entity_type="Project",
                entity_id=project_id
            )
        
        return success
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        すべてのプロジェクトの概要情報を取得
        
        Returns:
            プロジェクト概要情報のリスト
        """
        return self.data_store.list_projects()
    
    # ===== フェーズ操作 =====
    
    def add_phase(self, name: str, description: str = "") -> Optional[Phase]:
        """
        現在のプロジェクトに新しいフェーズを追加
        
        Args:
            name: フェーズ名
            description: フェーズの説明
            
        Returns:
            作成されたフェーズ、現在のプロジェクトがない場合はNone
        """
        if not self.current_project:
            return None
        
        phase = Phase(name=name, description=description)
        self.current_project.add_phase(phase)
        self.save_current_project()
        
        self.logger.log_action(
            action_type="create",
            entity_type="Phase",
            entity_id=phase.id,
            details={
                "name": name,
                "project_id": self.current_project.id,
                "project_name": self.current_project.name
            }
        )
        
        return phase
    
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
        if not self.current_project:
            return False
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return False
        
        details = {}
        
        if name is not None or description is not None:
            phase.update(name, description)
            if name:
                details["name"] = name
            if description:
                details["description"] = description
        
        if end_date is not None:
            phase.set_end_date(end_date)
            details["end_date"] = end_date.isoformat()
        
        self.save_current_project()
        
        if details:
            self.logger.log_action(
                action_type="update",
                entity_type="Phase",
                entity_id=phase.id,
                details=details
            )
        
        return True
    
    def remove_phase(self, phase_id: str) -> bool:
        """
        フェーズを削除
        
        Args:
            phase_id: 削除するフェーズのID
            
        Returns:
            削除が成功したかどうか
        """
        if not self.current_project:
            return False
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return False
        
        phase_name = phase.name
        self.current_project.remove_phase(phase_id)
        self.save_current_project()
        
        self.logger.log_action(
            action_type="delete",
            entity_type="Phase",
            entity_id=phase_id,
            details={
                "name": phase_name,
                "project_id": self.current_project.id,
                "project_name": self.current_project.name
            }
        )
        
        return True
    
    def get_phases(self) -> List[Dict[str, Any]]:
        """
        現在のプロジェクトのすべてのフェーズ情報を取得
        
        Returns:
            フェーズ情報のリスト
        """
        if not self.current_project:
            return []
        
        phases = []
        for phase in self.current_project.get_phases():
            phase_info = {
                "id": phase.id,
                "name": phase.name,
                "description": phase.description,
                "progress": phase.calculate_progress(),
                "start_date": phase.get_start_date().isoformat() if phase.get_start_date() else None,
                "end_date": phase.get_end_date().isoformat() if phase.get_end_date() else None,
                "process_count": len(phase.get_processes())
            }
            phases.append(phase_info)
        
        return phases
    
    # ===== プロセス操作 =====
    
    def add_process(self, phase_id: str, name: str, description: str = "", assignee: str = "") -> Optional[Process]:
        """
        フェーズに新しいプロセスを追加
        
        Args:
            phase_id: プロセスを追加するフェーズのID
            name: プロセス名
            description: プロセスの説明
            assignee: 担当者
            
        Returns:
            作成されたプロセス、フェーズがない場合はNone
        """
        if not self.current_project:
            return None
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return None
        
        process = Process(name=name, description=description, assignee=assignee)
        phase.add_process(process)
        self.save_current_project()
        
        self.logger.log_action(
            action_type="create",
            entity_type="Process",
            entity_id=process.id,
            details={
                "name": name,
                "assignee": assignee,
                "phase_id": phase.id,
                "phase_name": phase.name,
                "project_id": self.current_project.id
            }
        )
        
        return process
    
    def update_process(self, phase_id: str, process_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None, assignee: Optional[str] = None,
                      start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                      estimated_hours: Optional[float] = None, actual_hours: Optional[float] = None) -> bool:
        """
        プロセスを更新
        
        Args:
            phase_id: プロセスが属するフェーズのID
            process_id: 更新するプロセスのID
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
        if not self.current_project:
            return False
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return False
        
        process = phase.find_process(process_id)
        if not process:
            return False
        
        details = {}
        
        # 基本情報の更新
        if name is not None or description is not None:
            process.update(name, description)
            if name:
                details["name"] = name
            if description:
                details["description"] = description
        
        # 担当者の更新
        if assignee is not None:
            process.update_assignee(assignee)
            details["assignee"] = assignee
        
        # 日付の更新
        if start_date is not None:
            process.set_start_date(start_date)
            details["start_date"] = start_date.isoformat()
        
        if end_date is not None:
            process.set_end_date(end_date)
            details["end_date"] = end_date.isoformat()
        
        # 工数の更新
        if estimated_hours is not None or actual_hours is not None:
            process.update_hours(estimated_hours, actual_hours)
            if estimated_hours is not None:
                details["estimated_hours"] = estimated_hours
            if actual_hours is not None:
                details["actual_hours"] = actual_hours
        
        self.save_current_project()
        
        if details:
            self.logger.log_action(
                action_type="update",
                entity_type="Process",
                entity_id=process.id,
                details=details
            )
        
        return True
    
    def remove_process(self, phase_id: str, process_id: str) -> bool:
        """
        プロセスを削除
        
        Args:
            phase_id: プロセスが属するフェーズのID
            process_id: 削除するプロセスのID
            
        Returns:
            削除が成功したかどうか
        """
        if not self.current_project:
            return False
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return False
        
        process = phase.find_process(process_id)
        if not process:
            return False
        
        process_name = process.name
        phase.remove_process(process_id)
        self.save_current_project()
        
        self.logger.log_action(
            action_type="delete",
            entity_type="Process",
            entity_id=process_id,
            details={
                "name": process_name,
                "phase_id": phase.id,
                "phase_name": phase.name,
                "project_id": self.current_project.id
            }
        )
        
        return True
    
    def get_processes(self, phase_id: str) -> List[Dict[str, Any]]:
        """
        フェーズのすべてのプロセス情報を取得
        
        Args:
            phase_id: プロセスを取得するフェーズのID
            
        Returns:
            プロセス情報のリスト
        """
        if not self.current_project:
            return []
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return []
        
        processes = []
        for process in phase.get_processes():
            process_info = {
                "id": process.id,
                "name": process.name,
                "description": process.description,
                "assignee": process.assignee,
                "progress": process.progress,
                "start_date": process.start_date.isoformat() if process.start_date else None,
                "end_date": process.end_date.isoformat() if process.end_date else None,
                "estimated_hours": process.estimated_hours,
                "actual_hours": process.actual_hours,
                "task_count": len(process.get_tasks())
            }
            processes.append(process_info)
        
        return processes
    
    # ===== タスク操作 =====
    
    def add_task(self, phase_id: str, process_id: str, name: str, 
                description: str = "", status: TaskStatus = TaskStatus.NOT_STARTED) -> Optional[Task]:
        """
        プロセスに新しいタスクを追加
        
        Args:
            phase_id: タスクが属するフェーズのID
            process_id: タスクを追加するプロセスのID
            name: タスク名
            description: タスクの説明
            status: タスクの状態
            
        Returns:
            作成されたタスク、プロセスがない場合はNone
        """
        if not self.current_project:
            return None
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return None
        
        process = phase.find_process(process_id)
        if not process:
            return None
        
        task = Task(name=name, description=description, status=status)
        process.add_task(task)
        self.save_current_project()
        
        self.logger.log_action(
            action_type="create",
            entity_type="Task",
            entity_id=task.id,
            details={
                "name": name,
                "status": status.value,
                "process_id": process.id,
                "process_name": process.name,
                "phase_id": phase.id,
                "project_id": self.current_project.id
            }
        )
        
        return task
    
    def update_task(self, phase_id: str, process_id: str, task_id: str, name: Optional[str] = None, 
                   description: Optional[str] = None, status: Optional[TaskStatus] = None) -> bool:
        """
        タスクを更新
        
        Args:
            phase_id: タスクが属するフェーズのID
            process_id: タスクが属するプロセスのID
            task_id: 更新するタスクのID
            name: 新しいタスク名（指定された場合）
            description: 新しいタスクの説明（指定された場合）
            status: 新しいタスク状態（指定された場合）
            
        Returns:
            更新が成功したかどうか
        """
        if not self.current_project:
            return False
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return False
        
        process = phase.find_process(process_id)
        if not process:
            return False
        
        task = process.find_task(task_id)
        if not task:
            return False
        
        details = {}
        
        # 基本情報の更新
        if name is not None or description is not None:
            task.update(name, description)
            if name:
                details["name"] = name
            if description:
                details["description"] = description
        
        # 状態の更新
        if status is not None:
            old_status = task.status
            task.update_status(status)
            details["status"] = {
                "old": old_status.value,
                "new": status.value
            }
        
        self.save_current_project()
        
        if details:
            self.logger.log_action(
                action_type="update",
                entity_type="Task",
                entity_id=task.id,
                details=details
            )
        
        return True
    
    def remove_task(self, phase_id: str, process_id: str, task_id: str) -> bool:
        """
        タスクを削除
        
        Args:
            phase_id: タスクが属するフェーズのID
            process_id: タスクが属するプロセスのID
            task_id: 削除するタスクのID
            
        Returns:
            削除が成功したかどうか
        """
        if not self.current_project:
            return False
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return False
        
        process = phase.find_process(process_id)
        if not process:
            return False
        
        task = process.find_task(task_id)
        if not task:
            return False
        
        task_name = task.name
        process.remove_task(task_id)
        self.save_current_project()
        
        self.logger.log_action(
            action_type="delete",
            entity_type="Task",
            entity_id=task_id,
            details={
                "name": task_name,
                "process_id": process.id,
                "process_name": process.name,
                "phase_id": phase.id,
                "project_id": self.current_project.id
            }
        )
        
        return True
    
    def get_tasks(self, phase_id: str, process_id: str) -> List[Dict[str, Any]]:
        """
        プロセスのすべてのタスク情報を取得
        
        Args:
            phase_id: タスクが属するフェーズのID
            process_id: タスクを取得するプロセスのID
            
        Returns:
            タスク情報のリスト
        """
        if not self.current_project:
            return []
        
        phase = self.current_project.find_phase(phase_id)
        if not phase:
            return []
        
        process = phase.find_process(process_id)
        if not process:
            return []
        
        tasks = []
        for task in process.get_tasks():
            task_info = {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat()
            }
            tasks.append(task_info)
        
        return tasks
    
    # ===== 検索・取得機能 =====
    
    def find_entity_by_id(self, entity_id: str) -> Tuple[Optional[Any], str, Optional[str], Optional[str]]:
        """
        IDからエンティティを検索
        
        Args:
            entity_id: 検索するエンティティのID
            
        Returns:
            (エンティティ, エンティティタイプ, 親ID, 祖父ID)のタプル
            エンティティが見つからない場合は(None, "", None, None)
        """
        if not self.current_project:
            return None, "", None, None
        
        # プロジェクト自身の場合
        if self.current_project.id == entity_id:
            return self.current_project, "Project", None, None
        
        # フェーズの検索
        for phase in self.current_project.get_phases():
            if phase.id == entity_id:
                return phase, "Phase", self.current_project.id, None
            
            # プロセスの検索
            for process in phase.get_processes():
                if process.id == entity_id:
                    return process, "Process", phase.id, self.current_project.id
                
                # タスクの検索
                for task in process.get_tasks():
                    if task.id == entity_id:
                        return task, "Task", process.id, phase.id
        
        return None, "", None, None
    
    def get_entity_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        エンティティの履歴を取得
        
        Args:
            entity_id: 履歴を取得するエンティティのID
            
        Returns:
            エンティティの履歴リスト
        """
        entity, entity_type, _, _ = self.find_entity_by_id(entity_id)
        if not entity:
            return []
        
        return self.logger.get_entity_history(entity_type, entity_id)


# シングルトンインスタンス
_project_manager = None


def get_project_manager() -> ProjectManager:
    """
    ProjectManagerのシングルトンインスタンスを取得
    
    Returns:
        ProjectManagerのインスタンス
    """
    global _project_manager
    if _project_manager is None:
        _project_manager = ProjectManager()
    return _project_manager
