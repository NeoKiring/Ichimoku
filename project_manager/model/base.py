"""
基底エンティティクラス
すべてのモデルクラスの基底となるクラスを定義
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any


class BaseEntity:
    """すべてのエンティティの基底クラス"""
    
    def __init__(self, name: str, description: str = ""):
        """
        基底エンティティの初期化
        
        Args:
            name: エンティティの名前
            description: エンティティの説明
        """
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.description: str = description
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.parent = None
        self.children: List[BaseEntity] = []
    
    def update(self, name: Optional[str] = None, description: Optional[str] = None) -> None:
        """
        エンティティの基本情報を更新
        
        Args:
            name: 新しい名前（指定された場合）
            description: 新しい説明（指定された場合）
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = datetime.now()
    
    def add_child(self, child: 'BaseEntity') -> None:
        """
        子エンティティを追加
        
        Args:
            child: 追加する子エンティティ
        """
        child.parent = self
        self.children.append(child)
        self.updated_at = datetime.now()
    
    def remove_child(self, child_id: str) -> Optional['BaseEntity']:
        """
        子エンティティを削除
        
        Args:
            child_id: 削除する子エンティティのID
            
        Returns:
            削除された子エンティティ、存在しない場合はNone
        """
        for i, child in enumerate(self.children):
            if child.id == child_id:
                removed_child = self.children.pop(i)
                removed_child.parent = None
                self.updated_at = datetime.now()
                return removed_child
        return None
    
    def find_child(self, child_id: str) -> Optional['BaseEntity']:
        """
        子エンティティを検索
        
        Args:
            child_id: 検索する子エンティティのID
            
        Returns:
            見つかった子エンティティ、存在しない場合はNone
        """
        for child in self.children:
            if child.id == child_id:
                return child
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        エンティティを辞書形式に変換
        
        Returns:
            エンティティの辞書表現
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "children": [child.to_dict() for child in self.children]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEntity':
        """
        辞書からエンティティを生成する抽象メソッド
        サブクラスで実装する必要がある
        
        Args:
            data: エンティティのデータを含む辞書
            
        Returns:
            生成されたエンティティ
        """
        raise NotImplementedError("Subclasses must implement from_dict method")
