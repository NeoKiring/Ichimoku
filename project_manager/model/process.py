"""
プロセスモデル
フェーズ内のプロセス情報と機能を定義するクラス
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseEntity


class Process(BaseEntity):
    """フェーズのプロセスを表すクラス"""
    
    def __init__(self, name: str, description: str = "", assignee: str = ""):
        """
        プロセスの初期化
        
        Args:
            name: プロセス名
            description: プロセスの説明
            assignee: 担当者
        """
        super().__init__(name, description)
        self.assignee: str = assignee
        self.progress: float = 0.0  # 進捗率（0〜100）
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.estimated_hours: float = 0.0  # 予想工数（時間）
        self.actual_hours: float = 0.0  # 実工数（時間）
    
    def add_task(self, task: 'Task') -> None:
        """
        タスクを追加
        
        Args:
            task: 追加するタスク
        """
        self.add_child(task)
        self._update_progress()
    
    def remove_task(self, task_id: str) -> Optional['Task']:
        """
        タスクを削除
        
        Args:
            task_id: 削除するタスクのID
            
        Returns:
            削除されたタスク、存在しない場合はNone
        """
        task = self.remove_child(task_id)
        if task:
            self._update_progress()
        return task
    
    def find_task(self, task_id: str) -> Optional['Task']:
        """
        タスクを検索
        
        Args:
            task_id: 検索するタスクのID
            
        Returns:
            見つかったタスク、存在しない場合はNone
        """
        return self.find_child(task_id)
    
    def get_tasks(self) -> List['Task']:
        """
        すべてのタスクを取得
        
        Returns:
            プロセスに属するすべてのタスクのリスト
        """
        return self.children
    
    def _update_progress(self) -> None:
        """タスクの状態に基づいて進捗率を更新"""
        if not self.children:
            self.progress = 0.0
            return
        
        from .task import TaskStatus  # 循環インポート回避のためここでインポート
        
        completed_tasks = 0
        impossible_tasks = 0
        
        for task in self.children:
            if task.status == TaskStatus.COMPLETED:
                completed_tasks += 1
            elif task.status == TaskStatus.IMPOSSIBLE:
                impossible_tasks += 1
        
        valid_tasks = len(self.children) - impossible_tasks
        if valid_tasks > 0:
            self.progress = (completed_tasks / valid_tasks) * 100
        else:
            self.progress = 0.0
        
        self.updated_at = datetime.now()
    
    def update_assignee(self, assignee: str) -> None:
        """
        担当者を更新
        
        Args:
            assignee: 新しい担当者
        """
        self.assignee = assignee
        self.updated_at = datetime.now()
    
    def update_hours(self, estimated_hours: Optional[float] = None, actual_hours: Optional[float] = None) -> None:
        """
        工数を更新
        
        Args:
            estimated_hours: 新しい予想工数（指定された場合）
            actual_hours: 新しい実工数（指定された場合）
        """
        if estimated_hours is not None:
            self.estimated_hours = max(0.0, estimated_hours)
        if actual_hours is not None:
            self.actual_hours = max(0.0, actual_hours)
        self.updated_at = datetime.now()
    
    def set_start_date(self, start_date: datetime) -> None:
        """
        開始日を設定
        
        Args:
            start_date: 開始日
        """
        self.start_date = start_date
        self.updated_at = datetime.now()
    
    def set_end_date(self, end_date: datetime) -> None:
        """
        終了日を設定
        
        Args:
            end_date: 終了日
        """
        self.end_date = end_date
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        プロセスを辞書形式に変換
        
        Returns:
            プロセスの辞書表現
        """
        data = super().to_dict()
        data.update({
            "assignee": self.assignee,
            "progress": self.progress,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Process':
        """
        辞書からプロセスを生成
        
        Args:
            data: プロセスデータを含む辞書
            
        Returns:
            生成されたプロセス
        """
        from .task import Task  # 循環インポート回避のためここでインポート
        
        process = cls(
            name=data["name"],
            description=data["description"],
            assignee=data["assignee"]
        )
        process.id = data["id"]
        process.created_at = datetime.fromisoformat(data["created_at"])
        process.updated_at = datetime.fromisoformat(data["updated_at"])
        process.progress = data["progress"]
        process.estimated_hours = data["estimated_hours"]
        process.actual_hours = data["actual_hours"]
        
        # 日付が設定されている場合は復元
        if data.get("start_date"):
            process.start_date = datetime.fromisoformat(data["start_date"])
        if data.get("end_date"):
            process.end_date = datetime.fromisoformat(data["end_date"])
        
        # 子タスクを再帰的に復元
        for child_data in data["children"]:
            task = Task.from_dict(child_data)
            process.add_child(task)  # add_taskではなくadd_childを使用して_update_progressの重複呼び出しを回避
        
        return process
