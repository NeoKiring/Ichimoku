"""
タスクモデル
プロセス内のタスク情報と機能を定義するクラス
"""
from enum import Enum
from typing import Dict, Any
from datetime import datetime

from .base import BaseEntity


class TaskStatus(Enum):
    """タスクの状態を表す列挙型"""
    NOT_STARTED = "未着手"
    IN_PROGRESS = "進行中"
    COMPLETED = "完了"
    IMPOSSIBLE = "対応不能"


class Task(BaseEntity):
    """プロセスのタスクを表すクラス"""
    
    def __init__(self, name: str, description: str = "", status: TaskStatus = TaskStatus.NOT_STARTED):
        """
        タスクの初期化
        
        Args:
            name: タスク名
            description: タスクの説明
            status: タスクの状態
        """
        super().__init__(name, description)
        self.status = status
    
    def update_status(self, status: TaskStatus) -> None:
        """
        タスクの状態を更新
        
        Args:
            status: 新しいタスク状態
        """
        self.status = status
        self.updated_at = datetime.now()
        
        # 親プロセスの進捗状況を更新
        if self.parent:
            from .process import Process  # 循環インポート回避のためここでインポート
            if isinstance(self.parent, Process):
                self.parent._update_progress()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        タスクを辞書形式に変換
        
        Returns:
            タスクの辞書表現
        """
        data = super().to_dict()
        data.update({
            "status": self.status.value
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        辞書からタスクを生成
        
        Args:
            data: タスクデータを含む辞書
            
        Returns:
            生成されたタスク
        """
        task = cls(
            name=data["name"],
            description=data["description"],
            status=TaskStatus(data["status"])
        )
        task.id = data["id"]
        task.created_at = datetime.fromisoformat(data["created_at"])
        task.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return task
