"""
ストレージパッケージの初期化
データ永続化機能をインポートして外部に公開
"""
from .data_store import DataStore, get_data_store

__all__ = [
    'DataStore',
    'get_data_store'
]
