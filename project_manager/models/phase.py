"""
フェーズモデル
プロジェクトの各フェーズ情報と機能を定義するクラス
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import BaseEntity


class Phase(BaseEntity):
    """プロジェクトのフェーズを表すクラス"""
    
    def __init__(self, name: str, description: str = ""):
        """
        フェーズの初期化
        
        Args:
            name: フェーズ名
            description: フェーズの説明
        """
        super().__init__(name, description)
        self.end_date: Optional[datetime] = None
    
    def add_process(self, process: 'Process') -> None:
        """
        プロセスを追加
        
        Args:
            process: 追加するプロセス
        """
        self.add_child(process)
    
    def remove_process(self, process_id: str) -> Optional['Process']:
        """
        プロセスを削除
        
        Args:
            process_id: 削除するプロセスのID
            
        Returns:
            削除されたプロセス、存在しない場合はNone
        """
        return self.remove_child(process_id)
    
    def find_process(self, process_id: str) -> Optional['Process']:
        """
        プロセスを検索
        
        Args:
            process_id: 検索するプロセスのID
            
        Returns:
            見つかったプロセス、存在しない場合はNone
        """
        return self.find_child(process_id)
    
    def get_processes(self) -> List['Process']:
        """
        すべてのプロセスを取得
        
        Returns:
            フェーズに属するすべてのプロセスのリスト
        """
        return self.children
    
    def set_end_date(self, end_date: datetime) -> None:
        """
        フェーズの終了日を設定
        
        Args:
            end_date: 終了日
        """
        self.end_date = end_date
        self.updated_at = datetime.now()
    
    def calculate_progress(self) -> float:
        """
        フェーズの進捗状況を計算（すべてのプロセスの進捗率の平均）
        
        Returns:
            フェーズの進捗率（0〜100）
        """
        if not self.children:
            return 0.0
        
        total_progress = sum(process.progress for process in self.children)
        return total_progress / len(self.children)
    
    def get_start_date(self) -> Optional[datetime]:
        """
        フェーズの開始日を取得（最も早いプロセスの開始日）
        
        Returns:
            最も早いプロセスの開始日、または該当するプロセスがない場合はNone
        """
        start_dates = [process.start_date for process in self.children if process.start_date]
        return min(start_dates) if start_dates else None
    
    def get_end_date(self) -> Optional[datetime]:
        """
        フェーズの終了日を取得
        
        Returns:
            設定された終了日、または最も遅いプロセスの終了日
        """
        # 明示的に設定された終了日がある場合はそれを返す
        if self.end_date:
            return self.end_date
        
        # そうでなければ、最も遅いプロセス終了日を計算
        end_dates = [process.end_date for process in self.children if process.end_date]
        return max(end_dates) if end_dates else None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        フェーズを辞書形式に変換
        
        Returns:
            フェーズの辞書表現
        """
        data = super().to_dict()
        data.update({
            "progress": self.calculate_progress(),
            "start_date": self.get_start_date().isoformat() if self.get_start_date() else None,
            "end_date": self.get_end_date().isoformat() if self.get_end_date() else None
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Phase':
        """
        辞書からフェーズを生成
        
        Args:
            data: フェーズデータを含む辞書
            
        Returns:
            生成されたフェーズ
        """
        from .process import Process  # 循環インポート回避のためここでインポート
        
        phase = cls(
            name=data["name"],
            description=data["description"]
        )
        phase.id = data["id"]
        phase.created_at = datetime.fromisoformat(data["created_at"])
        phase.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # 終了日が設定されている場合は復元
        if data.get("end_date"):
            phase.end_date = datetime.fromisoformat(data["end_date"])
        
        # 子プロセスを再帰的に復元
        for child_data in data["children"]:
            process = Process.from_dict(child_data)
            phase.add_process(process)
        
        return phase
