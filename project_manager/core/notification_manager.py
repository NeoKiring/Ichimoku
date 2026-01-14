"""
通知マネージャー
通知の生成、管理、チェックを担当
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.notification import Notification, NotificationType, NotificationPriority
from ..models import Project, Phase, Process, Task, ProjectStatus, TaskStatus
from ..storage.data_store import get_data_store
from ..core.logger import get_logger
from ..core.manager import get_project_manager


class NotificationManager:
    """
    通知の生成、管理、チェックを行うクラス
    """
    
    def __init__(self):
        """通知マネージャーの初期化"""
        self.data_store = get_data_store()
        self.logger = get_logger()
        
        # 通知設定（後でユーザー設定可能にする）
        self.settings = {
            "deadline_warning_days": 7,  # 期限の何日前に警告するか
            "deadline_critical_days": 3,  # 期限の何日前に重要警告するか
            "progress_threshold": 0.5,    # 進捗率のしきい値（期限の半分で進捗が何%以下なら警告するか）
            "check_interval_minutes": 30  # 通知チェックの間隔（分）
        }
    
    def generate_notifications(self) -> int:
        """
        全プロジェクトをチェックして必要な通知を生成
        
        Returns:
            生成された通知の数
        """
        project_manager = get_project_manager()
        projects = project_manager.list_projects()
        new_notifications_count = 0
        
        # プロジェクトごとに通知条件をチェック
        for project_info in projects:
            project_id = project_info["id"]
            
            # プロジェクトを読み込む
            project = project_manager.load_project(project_id)
            if not project:
                continue
                
            # プロジェクトの状態が「進行中」または「未着手」の場合のみチェック
            if project.status not in [ProjectStatus.IN_PROGRESS, ProjectStatus.NOT_STARTED]:
                continue
            
            # フェーズをチェック
            for phase in project.get_phases():
                # プロセスをチェック
                for process in phase.get_processes():
                    # 期限通知のチェック
                    if self._check_deadline_notification(project, phase, process):
                        new_notifications_count += 1
                    
                    # 進捗アラートのチェック
                    if self._check_progress_notification(project, phase, process):
                        new_notifications_count += 1
        
        self.logger.log_action(
            action_type="notification_check",
            entity_type="System",
            entity_id="notification_manager",
            details={"new_notifications": new_notifications_count}
        )
        
        return new_notifications_count
    
    def _check_deadline_notification(self, project: Project, phase: Phase, process: Process) -> bool:
        """
        プロセスの期限が近いかどうかをチェックし、必要に応じて通知を生成
        
        Args:
            project: プロジェクト
            phase: フェーズ
            process: チェック対象のプロセス
            
        Returns:
            通知が生成された場合はTrue、そうでない場合はFalse
        """
        if not process.end_date:
            return False  # 期限が設定されていない場合
        
        today = datetime.now().date()
        end_date = process.end_date.date()
        
        # 既に期限を過ぎている場合
        if end_date < today:
            days_overdue = (today - end_date).days
            
            # 既存の期限超過通知をチェック
            existing_notifications = self.get_notifications_by_criteria(
                entity_type="Process",
                entity_id=process.id,
                notification_type=NotificationType.DEADLINE_OVERDUE
            )
            
            # 既存の通知がなければ新規作成
            if not existing_notifications:
                message = f"プロセス「{process.name}」の期限を{days_overdue}日超過しています。"
                notification = Notification(
                    notification_type=NotificationType.DEADLINE_OVERDUE,
                    message=message,
                    entity_type="Process",
                    entity_id=process.id,
                    project_id=project.id,
                    priority=NotificationPriority.HIGH
                )
                self.save_notification(notification)
                return True
        
        # 期限が近づいている場合
        elif (end_date - today).days <= self.settings["deadline_warning_days"]:
            days_remaining = (end_date - today).days
            
            # 既存の期限接近通知をチェック
            existing_notifications = self.get_notifications_by_criteria(
                entity_type="Process",
                entity_id=process.id,
                notification_type=NotificationType.DEADLINE_APPROACHING
            )
            
            # 優先度の決定
            priority = (
                NotificationPriority.HIGH 
                if days_remaining <= self.settings["deadline_critical_days"] 
                else NotificationPriority.MEDIUM
            )
            
            # 既存の通知がないか、優先度が変わった場合に新規作成
            should_create_new = False
            if not existing_notifications:
                should_create_new = True
            elif existing_notifications and existing_notifications[0].priority != priority:
                # 古い通知を既読にする
                existing_notifications[0].mark_as_read()
                self.update_notification(existing_notifications[0])
                should_create_new = True
            
            if should_create_new:
                message = f"プロセス「{process.name}」の期限まであと{days_remaining}日です。"
                notification = Notification(
                    notification_type=NotificationType.DEADLINE_APPROACHING,
                    message=message,
                    entity_type="Process",
                    entity_id=process.id,
                    project_id=project.id,
                    priority=priority
                )
                self.save_notification(notification)
                return True
        
        return False
    
    def _check_progress_notification(self, project: Project, phase: Phase, process: Process) -> bool:
        """
        プロセスの進捗遅延をチェックし、必要に応じて通知を生成
        
        Args:
            project: プロジェクト
            phase: フェーズ
            process: チェック対象のプロセス
            
        Returns:
            通知が生成された場合はTrue、そうでない場合はFalse
        """
        if not process.start_date or not process.end_date:
            return False  # 開始日または終了日が設定されていない場合
        
        today = datetime.now().date()
        start_date = process.start_date.date()
        end_date = process.end_date.date()
        
        # 既に終了している場合はチェック不要
        if today > end_date:
            return False
        
        # まだ開始していない場合もチェック不要
        if today < start_date:
            return False
        
        # 進捗率と経過時間の割合を計算
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return False  # 期間が0または負の場合は計算不能
            
        elapsed_days = (today - start_date).days
        elapsed_ratio = elapsed_days / total_days  # 期間の何%が経過したか
        
        # 進捗が明らかに遅れている場合（経過時間の割合の半分以下の進捗）
        if elapsed_ratio > 0.5 and process.progress / 100 < elapsed_ratio * self.settings["progress_threshold"]:
            # 既存の進捗遅延通知をチェック
            existing_notifications = self.get_notifications_by_criteria(
                entity_type="Process",
                entity_id=process.id,
                notification_type=NotificationType.PROGRESS_DELAY
            )
            
            # 進捗の遅れが深刻かどうかでプライオリティを決定
            progress_gap = elapsed_ratio - (process.progress / 100)
            priority = (
                NotificationPriority.HIGH 
                if progress_gap > 0.5 
                else NotificationPriority.MEDIUM
            )
            
            # 既存の通知がないか、優先度が変わった場合に新規作成
            should_create_new = False
            if not existing_notifications:
                should_create_new = True
            elif existing_notifications and existing_notifications[0].priority != priority:
                # 古い通知を既読にする
                existing_notifications[0].mark_as_read()
                self.update_notification(existing_notifications[0])
                should_create_new = True
            
            if should_create_new:
                expected_progress = int(elapsed_ratio * 100)
                actual_progress = int(process.progress)
                message = f"プロセス「{process.name}」の進捗が遅れています。経過: {int(elapsed_ratio*100)}%、進捗: {actual_progress}%"
                
                notification = Notification(
                    notification_type=NotificationType.PROGRESS_DELAY,
                    message=message,
                    entity_type="Process",
                    entity_id=process.id,
                    project_id=project.id,
                    priority=priority
                )
                self.save_notification(notification)
                return True
                
        # 残り時間が少なくて進捗が低い場合
        days_remaining = (end_date - today).days
        if days_remaining <= self.settings["deadline_warning_days"] and process.progress < 50:
            # 既存の進捗不足通知をチェック
            existing_notifications = self.get_notifications_by_criteria(
                entity_type="Process",
                entity_id=process.id,
                notification_type=NotificationType.LOW_PROGRESS
            )
            
            # 進捗の遅れが深刻かどうかでプライオリティを決定
            priority = (
                NotificationPriority.HIGH 
                if days_remaining <= self.settings["deadline_critical_days"] 
                else NotificationPriority.MEDIUM
            )
            
            # 既存の通知がないか、優先度が変わった場合に新規作成
            should_create_new = False
            if not existing_notifications:
                should_create_new = True
            elif existing_notifications and existing_notifications[0].priority != priority:
                # 古い通知を既読にする
                existing_notifications[0].mark_as_read()
                self.update_notification(existing_notifications[0])
                should_create_new = True
            
            if should_create_new:
                message = f"プロセス「{process.name}」の進捗が{int(process.progress)}%ですが、期限まで残り{days_remaining}日です。"
                
                notification = Notification(
                    notification_type=NotificationType.LOW_PROGRESS,
                    message=message,
                    entity_type="Process",
                    entity_id=process.id,
                    project_id=project.id,
                    priority=priority
                )
                self.save_notification(notification)
                return True
        
        return False
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """
        指定されたIDの通知を取得
        
        Args:
            notification_id: 通知ID
            
        Returns:
            通知、存在しない場合はNone
        """
        notification_data = self.data_store.load_notification(notification_id)
        if notification_data:
            return Notification.from_dict(notification_data)
        return None
    
    def get_all_notifications(self) -> List[Notification]:
        """
        すべての通知を取得
        
        Returns:
            通知のリスト
        """
        notifications_data = self.data_store.list_notifications()
        return [Notification.from_dict(data) for data in notifications_data]
    
    def get_unread_notifications(self) -> List[Notification]:
        """
        未読の通知を取得
        
        Returns:
            未読通知のリスト
        """
        notifications = self.get_all_notifications()
        return [notification for notification in notifications if not notification.read]
    
    def get_notifications_by_criteria(self, 
                                     entity_type: Optional[str] = None, 
                                     entity_id: Optional[str] = None,
                                     project_id: Optional[str] = None,
                                     notification_type: Optional[NotificationType] = None) -> List[Notification]:
        """
        指定された条件に一致する通知を取得
        
        Args:
            entity_type: エンティティタイプでフィルタリング
            entity_id: エンティティIDでフィルタリング
            project_id: プロジェクトIDでフィルタリング
            notification_type: 通知タイプでフィルタリング
            
        Returns:
            条件に一致する通知のリスト
        """
        notifications = self.get_all_notifications()
        filtered_notifications = notifications
        
        if entity_type:
            filtered_notifications = [n for n in filtered_notifications if n.entity_type == entity_type]
        
        if entity_id:
            filtered_notifications = [n for n in filtered_notifications if n.entity_id == entity_id]
        
        if project_id:
            filtered_notifications = [n for n in filtered_notifications if n.project_id == project_id]
        
        if notification_type:
            filtered_notifications = [n for n in filtered_notifications if n.notification_type == notification_type]
        
        return filtered_notifications
    
    def save_notification(self, notification: Notification) -> bool:
        """
        通知を保存
        
        Args:
            notification: 保存する通知
            
        Returns:
            保存が成功したかどうか
        """
        return self.data_store.save_notification(notification.to_dict())
    
    def update_notification(self, notification: Notification) -> bool:
        """
        通知を更新
        
        Args:
            notification: 更新する通知
            
        Returns:
            更新が成功したかどうか
        """
        return self.data_store.save_notification(notification.to_dict())
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        通知を既読にする
        
        Args:
            notification_id: 既読にする通知のID
            
        Returns:
            更新が成功したかどうか
        """
        notification = self.get_notification(notification_id)
        if notification:
            notification.mark_as_read()
            return self.update_notification(notification)
        return False
    
    def mark_all_as_read(self) -> int:
        """
        すべての未読通知を既読にする
        
        Returns:
            既読にした通知の数
        """
        unread_notifications = self.get_unread_notifications()
        success_count = 0
        
        for notification in unread_notifications:
            notification.mark_as_read()
            if self.update_notification(notification):
                success_count += 1
        
        return success_count
    
    def delete_notification(self, notification_id: str) -> bool:
        """
        通知を削除
        
        Args:
            notification_id: 削除する通知のID
            
        Returns:
            削除が成功したかどうか
        """
        return self.data_store.delete_notification(notification_id)
    
    def delete_old_notifications(self, days: int = 30) -> int:
        """
        指定された日数より古い通知を削除
        
        Args:
            days: 何日前より古い通知を削除するか
            
        Returns:
            削除された通知の数
        """
        cut_off_date = datetime.now() - timedelta(days=days)
        notifications = self.get_all_notifications()
        deleted_count = 0
        
        for notification in notifications:
            if notification.created_at < cut_off_date:
                if self.delete_notification(notification.id):
                    deleted_count += 1
        
        return deleted_count
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        通知設定を更新
        
        Args:
            new_settings: 新しい設定値の辞書
        """
        for key, value in new_settings.items():
            if key in self.settings:
                self.settings[key] = value


# シングルトンインスタンス
_notification_manager = None


def get_notification_manager() -> NotificationManager:
    """
    NotificationManagerのシングルトンインスタンスを取得
    
    Returns:
        NotificationManagerのインスタンス
    """
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
