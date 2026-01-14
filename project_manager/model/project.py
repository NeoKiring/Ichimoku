"""
プロジェクトモデル
プロジェクト情報と機能を定義するクラス
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseEntity
from .phase import Phase


class ProjectStatus(Enum):
    """プロジェクトの進捗状況を表す列挙型"""
    NOT_STARTED = "未着手"
    IN_PROGRESS = "進行中"
    COMPLETED = "完了"
    CANCELLED = "中止"
    ON_HOLD = "保留"


class Project(BaseEntity):
    """プロジェクトを表すクラス"""
    
    def __init__(self, name: str, description: str = "", status: ProjectStatus = ProjectStatus.NOT_STARTED):
        """
        プロジェクトの初期化
        
        Args:
            name: プロジェクト名
            description: プロジェクトの説明
            status: プロジェクトの状態
        """
        super().__init__(name, description)
        self.status = status
        self.is_status_manual = False  # 状態が手動で設定されたかどうか
    
    def add_phase(self, phase: Phase) -> None:
        """
        フェーズを追加
        
        Args:
            phase: 追加するフェーズ
        """
        self.add_child(phase)
    
    def remove_phase(self, phase_id: str) -> Optional[Phase]:
        """
        フェーズを削除
        
        Args:
            phase_id: 削除するフェーズのID
            
        Returns:
            削除されたフェーズ、存在しない場合はNone
        """
        return self.remove_child(phase_id)
    
    def find_phase(self, phase_id: str) -> Optional[Phase]:
        """
        フェーズを検索
        
        Args:
            phase_id: 検索するフェーズのID
            
        Returns:
            見つかったフェーズ、存在しない場合はNone
        """
        return self.find_child(phase_id)
    
    def get_phases(self) -> List[Phase]:
        """
        すべてのフェーズを取得
        
        Returns:
            プロジェクトに属するすべてのフェーズのリスト
        """
        return self.children
    
    def update_status(self, status: ProjectStatus, manual: bool = True) -> None:
        """
        プロジェクトの状態を更新
        
        Args:
            status: 新しいプロジェクト状態
            manual: 手動で設定された状態かどうか
        """
        self.status = status
        self.is_status_manual = manual
        self.updated_at = datetime.now()

    def determine_status(self) -> ProjectStatus:
        """
        進捗状況に基づいて自動的に状態を判定
        
        Returns:
            判定されたプロジェクト状態
        """
        # 手動設定された状態がある場合はそれを優先
        if self.is_status_manual:
            return self.status
        
        # 進捗率に基づいて状態を判定
        progress = self.calculate_progress()
        
        if progress >= 100.0:
            return ProjectStatus.COMPLETED
        
        # プロセスがあり、進捗が0より大きい場合は進行中
        has_progress = False
        for phase in self.children:
            for process in phase.children:
                if process.progress > 0:
                    has_progress = True
                    break
            if has_progress:
                break
        
        if has_progress:
            return ProjectStatus.IN_PROGRESS
        
        # それ以外は未着手
        return ProjectStatus.NOT_STARTED
    
    def release_manual_status(self) -> None:
        """
        手動設定された状態を解除し、自動判定に戻す
        """
        self.is_status_manual = False
        self.status = self.determine_status()
        self.updated_at = datetime.now()
    
    def calculate_progress(self) -> float:
        """
        プロジェクト全体の進捗状況を計算
        
        Returns:
            プロジェクトの進捗率（0〜100）
        """
        if not self.children:
            return 0.0
        
        total_progress = sum(phase.calculate_progress() for phase in self.children)
        return total_progress / len(self.children)
    
    def get_start_date(self) -> Optional[datetime]:
        """
        プロジェクトの開始日を取得
        
        Returns:
            最も早いフェーズの開始日、または該当するフェーズがない場合はNone
        """
        start_dates = [phase.get_start_date() for phase in self.children if phase.get_start_date()]
        return min(start_dates) if start_dates else None
    
    def get_end_date(self) -> Optional[datetime]:
        """
        プロジェクトの終了日を取得
        
        Returns:
            最も遅いフェーズの終了日、または該当するフェーズがない場合はNone
        """
        end_dates = [phase.get_end_date() for phase in self.children if phase.get_end_date()]
        return max(end_dates) if end_dates else None

    def to_dict(self) -> Dict[str, Any]:
        """
        プロジェクトを辞書形式に変換
        
        Returns:
            プロジェクトの辞書表現
        """
        data = super().to_dict()
        data.update({
            "status": self.status.value,
            "is_status_manual": self.is_status_manual,
            "progress": self.calculate_progress(),
            "start_date": self.get_start_date().isoformat() if self.get_start_date() else None,
            "end_date": self.get_end_date().isoformat() if self.get_end_date() else None
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        辞書からプロジェクトを生成
        
        Args:
            data: プロジェクトデータを含む辞書
            
        Returns:
            生成されたプロジェクト
        """
        from .phase import Phase  # 循環インポート回避のためここでインポート
        
        project = cls(
            name=data["name"],
            description=data["description"],
            status=ProjectStatus(data["status"])
        )
        project.id = data["id"]
        project.created_at = datetime.fromisoformat(data["created_at"])
        project.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # 手動状態フラグを復元
        project.is_status_manual = data.get("is_status_manual", False)
        
        # 子フェーズを再帰的に復元
        for child_data in data["children"]:
            phase = Phase.from_dict(child_data)
            project.add_phase(phase)
        
        return project
