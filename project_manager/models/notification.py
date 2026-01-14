"""
通知モデル
通知情報と機能を定義するクラス
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class NotificationType(Enum):
    """通知の種類を表す列挙型"""
    DEADLINE_APPROACHING = "期限接近"  # プロセスの期限が近づいている
    DEADLINE_OVERDUE = "期限超過"      # プロセスの期限を超過している
    PROGRESS_DELAY = "進捗遅延"        # 進捗が計画より遅れている
    LOW_PROGRESS = "進捗不足"          # 期限までの時間に対して進捗が少ない


class NotificationPriority(Enum):
    """通知の優先度を表す列挙型"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class Notification:
    """通知を表すクラス"""
    
    def __init__(self, 
                 notification_type: NotificationType, 
                 message: str, 
                 entity_type: str,
                 entity_id: str,
                 project_id: str,
                 priority: NotificationPriority = NotificationPriority.MEDIUM):
        """
        通知の初期化
        
        Args:
            notification_type: 通知の種類
            message: 通知メッセージ
            entity_type: 関連するエンティティの種類（Project, Phase, Process, Task）
            entity_id: 関連するエンティティのID
            project_id: 関連するプロジェクトのID
            priority: 通知の優先度
        """
        self.id: str = str(uuid.uuid4())
        self.notification_type = notification_type
        self.message = message
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.project_id = project_id
        self.priority = priority
        self.created_at: datetime = datetime.now()
        self.read: bool = False
        self.read_at: Optional[datetime] = None
    
    def mark_as_read(self) -> None:
        """通知を既読にする"""
        self.read = True
        self.read_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        通知を辞書形式に変換
        
        Returns:
            通知の辞書表現
        """
        return {
            "id": self.id,
            "notification_type": self.notification_type.value,
            "message": self.message,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "project_id": self.project_id,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """
        辞書から通知を生成
        
        Args:
            data: 通知データを含む辞書
            
        Returns:
            生成された通知
        """
        notification = cls(
            notification_type=NotificationType(data["notification_type"]),
            message=data["message"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            project_id=data["project_id"],
            priority=NotificationPriority(data["priority"])
        )
        notification.id = data["id"]
        notification.created_at = datetime.fromisoformat(data["created_at"])
        notification.read = data["read"]
        if data["read_at"]:
            notification.read_at = datetime.fromisoformat(data["read_at"])
        
        return notification
