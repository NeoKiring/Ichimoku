"""
データストア
プロジェクト管理データの永続化を担当
"""
import os
import json
from typing import List, Dict, Any, Optional

from ..models import Project
from ..core.logger import get_logger


class DataStore:
    """
    プロジェクトデータの保存と読み込みを担当するクラス
    JSONファイルを使用してデータを永続化
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        データストアの初期化
        
        Args:
            data_dir: データを保存するディレクトリ
        """
        self.data_dir = data_dir
        self.logger = get_logger()
        
        # データディレクトリが存在しない場合は作成
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def save_project(self, project: Project) -> bool:
        """
        プロジェクトを保存
        
        Args:
            project: 保存するプロジェクト
            
        Returns:
            保存が成功したかどうか
        """
        try:
            # プロジェクトデータを辞書に変換
            project_data = project.to_dict()
            
            # ファイルパスを生成
            file_path = os.path.join(self.data_dir, f"project_{project.id}.json")
            
            # JSONとして保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, ensure_ascii=False, indent=2)
            
            # ログに記録
            self.logger.log_action(
                action_type="save",
                entity_type="Project",
                entity_id=project.id,
                details={"name": project.name}
            )
            
            return True
        except Exception as e:
            self.logger.log_action(
                action_type="save_error",
                entity_type="Project",
                entity_id=project.id,
                details={"error": str(e)}
            )
            return False
    
    def load_project(self, project_id: str) -> Optional[Project]:
        """
        プロジェクトを読み込み
        
        Args:
            project_id: 読み込むプロジェクトのID
            
        Returns:
            読み込まれたプロジェクト、存在しない場合はNone
        """
        try:
            # ファイルパスを生成
            file_path = os.path.join(self.data_dir, f"project_{project_id}.json")
            
            # ファイルが存在しない場合はNoneを返す
            if not os.path.exists(file_path):
                return None
            
            # JSONからデータを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # プロジェクトオブジェクトに変換
            project = Project.from_dict(project_data)
            
            # ログに記録
            self.logger.log_action(
                action_type="load",
                entity_type="Project",
                entity_id=project.id,
                details={"name": project.name}
            )
            
            return project
        except Exception as e:
            self.logger.log_action(
                action_type="load_error",
                entity_type="Project",
                entity_id=project_id,
                details={"error": str(e)}
            )
            return None
    
    def delete_project(self, project_id: str) -> bool:
        """
        プロジェクトを削除
        
        Args:
            project_id: 削除するプロジェクトのID
            
        Returns:
            削除が成功したかどうか
        """
        try:
            # ファイルパスを生成
            file_path = os.path.join(self.data_dir, f"project_{project_id}.json")
            
            # ファイルが存在しない場合はFalseを返す
            if not os.path.exists(file_path):
                return False
            
            # プロジェクト情報をログのために取得
            project_name = None
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                    project_name = project_data.get("name", "Unknown")
            except:
                pass
            
            # ファイルを削除
            os.remove(file_path)
            
            # ログに記録
            self.logger.log_action(
                action_type="delete",
                entity_type="Project",
                entity_id=project_id,
                details={"name": project_name} if project_name else None
            )
            
            return True
        except Exception as e:
            self.logger.log_action(
                action_type="delete_error",
                entity_type="Project",
                entity_id=project_id,
                details={"error": str(e)}
            )
            return False
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        すべてのプロジェクトの概要情報を取得
        
        Returns:
            プロジェクト概要情報のリスト
        """
        projects = []
        
        # データディレクトリ内のすべてのJSONファイルを検索
        for filename in os.listdir(self.data_dir):
            if filename.startswith("project_") and filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.data_dir, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    
                    # 必要な情報のみを抽出
                    project_summary = {
                        "id": project_data["id"],
                        "name": project_data["name"],
                        "status": project_data["status"],
                        "progress": project_data["progress"],
                        "created_at": project_data["created_at"],
                        "updated_at": project_data["updated_at"]
                    }
                    
                    projects.append(project_summary)
                except Exception as e:
                    self.logger.log_action(
                        action_type="list_error",
                        entity_type="Project",
                        entity_id="unknown",
                        details={"filename": filename, "error": str(e)}
                    )
        
        # 更新日時でソート（最新のものが先頭）
        projects.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return projects
    def save_notification(self, notification_data: Dict[str, Any]) -> bool:
        """
        通知を保存
        
        Args:
            notification_data: 保存する通知データ
            
        Returns:
            保存が成功したかどうか
        """
        try:
            # 通知データからIDを取得
            notification_id = notification_data["id"]
            
            # ファイルパスを生成
            file_path = os.path.join(self.data_dir, f"notification_{notification_id}.json")
            
            # JSONとして保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notification_data, f, ensure_ascii=False, indent=2)
            
            # ログに記録
            self.logger.log_action(
                action_type="save",
                entity_type="Notification",
                entity_id=notification_id,
                details={"message": notification_data.get("message", "")}
            )
            
            return True
        except Exception as e:
            self.logger.log_action(
                action_type="save_error",
                entity_type="Notification",
                entity_id=notification_data.get("id", "unknown"),
                details={"error": str(e)}
            )
            return False

    def load_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        通知を読み込み
        
        Args:
            notification_id: 読み込む通知のID
            
        Returns:
            読み込まれた通知データ、存在しない場合はNone
        """
        try:
            # ファイルパスを生成
            file_path = os.path.join(self.data_dir, f"notification_{notification_id}.json")
            
            # ファイルが存在しない場合はNoneを返す
            if not os.path.exists(file_path):
                return None
            
            # JSONからデータを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                notification_data = json.load(f)
            
            # ログに記録
            self.logger.log_action(
                action_type="load",
                entity_type="Notification",
                entity_id=notification_id,
                details={"message": notification_data.get("message", "")}
            )
            
            return notification_data
        except Exception as e:
            self.logger.log_action(
                action_type="load_error",
                entity_type="Notification",
                entity_id=notification_id,
                details={"error": str(e)}
            )
            return None

    def delete_notification(self, notification_id: str) -> bool:
        """
        通知を削除
        
        Args:
            notification_id: 削除する通知のID
            
        Returns:
            削除が成功したかどうか
        """
        try:
            # ファイルパスを生成
            file_path = os.path.join(self.data_dir, f"notification_{notification_id}.json")
            
            # ファイルが存在しない場合はFalseを返す
            if not os.path.exists(file_path):
                return False
            
            # 通知情報をログのために取得
            notification_message = None
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    notification_data = json.load(f)
                    notification_message = notification_data.get("message", "Unknown")
            except:
                pass
            
            # ファイルを削除
            os.remove(file_path)
            
            # ログに記録
            self.logger.log_action(
                action_type="delete",
                entity_type="Notification",
                entity_id=notification_id,
                details={"message": notification_message} if notification_message else None
            )
            
            return True
        except Exception as e:
            self.logger.log_action(
                action_type="delete_error",
                entity_type="Notification",
                entity_id=notification_id,
                details={"error": str(e)}
            )
            return False

    def list_notifications(self) -> List[Dict[str, Any]]:
        """
        すべての通知の情報を取得
        
        Returns:
            通知情報のリスト
        """
        notifications = []
        
        # データディレクトリ内のすべての通知ファイルを検索
        for filename in os.listdir(self.data_dir):
            if filename.startswith("notification_") and filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.data_dir, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        notification_data = json.load(f)
                    
                    notifications.append(notification_data)
                except Exception as e:
                    notification_id = filename.replace("notification_", "").replace(".json", "")
                    self.logger.log_action(
                        action_type="list_error",
                        entity_type="Notification",
                        entity_id=notification_id,
                        details={"filename": filename, "error": str(e)}
                    )
        
        # 作成日時でソート（最新のものが先頭）
        notifications.sort(key=lambda x: x["created_at"], reverse=True)
        
        return notifications


# シングルトンインスタンス
_data_store = None


def get_data_store() -> DataStore:
    """
    DataStoreのシングルトンインスタンスを取得
    
    Returns:
        DataStoreのインスタンス
    """
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
    return _data_store
