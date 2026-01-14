"""
GUIユーティリティ
GUIコンポーネント間で共通の機能を提供
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import QDateTime
from typing import List, Dict, Any, Optional, Tuple, Union

class ColorScheme:
    """
    アプリケーションのカラースキーム
    明暗どちらのテーマでも見やすい一貫した色を提供
    """
    # 一般的な色
    BACKGROUND = "#ffffff"
    TEXT = "#222222"  # より暗く
    BORDER = "#aaaaaa"  # より暗く
    HIGHLIGHT = "#d6e7f5"  # より暗く
    HIGHLIGHT_BORDER = "#0068c4"  # より暗く
    
    # ステータス色
    NOT_STARTED = "#5c6570"  # より暗く
    IN_PROGRESS = "#0068c4"  # より暗く
    COMPLETED = "#1a9735"    # より暗く
    IMPOSSIBLE = "#cc2535"   # より暗く
    CANCELLED = "#cc2535"    # より暗く
    ON_HOLD = "#ec9707"      # より暗く
    
    # テーブル色
    TABLE_HEADER = "#e8e9ea"  # より暗く
    TABLE_ALTERNATE_ROW = "#f0f0f0"  # より暗く
    
    # 優先度/警告色
    OVERDUE = "#cc2535"      # より暗く
    WARNING = "#ec9707"      # より暗く
    NORMAL = "#1a9735"       # より暗く
    
    # ボタン色
    BUTTON_PRIMARY = "#0068c4"  # より暗く
    BUTTON_PRIMARY_TEXT = "#ffffff"
    BUTTON_SECONDARY = "#5c6570"  # より暗く
    BUTTON_SECONDARY_TEXT = "#ffffff"
    BUTTON_DANGER = "#cc2535"  # より暗く
    BUTTON_DANGER_TEXT = "#ffffff"
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """
        ステータスに応じた色を取得
        
        Args:
            status: ステータス文字列
            
        Returns:
            CSS色文字列
        """
        status_colors = {
            "未着手": ColorScheme.NOT_STARTED,
            "進行中": ColorScheme.IN_PROGRESS,
            "完了": ColorScheme.COMPLETED,
            "中止": ColorScheme.CANCELLED,
            "保留": ColorScheme.ON_HOLD,
            "対応不能": ColorScheme.IMPOSSIBLE
        }
        return status_colors.get(status, ColorScheme.NOT_STARTED)

def format_date(date: Optional[Union[datetime, str]]) -> str:
    """
    日付をフォーマットする
    
    Args:
        date: 日付オブジェクト、ISO形式の日付文字列、またはNone
        
    Returns:
        フォーマットされた日付文字列、または未設定を示す文字列
    """
    if date is None:
        return "未設定"
    
    # 文字列の場合はdatetimeに変換
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            return date  # 変換できない場合は元の文字列を返す
    
    # datetimeオブジェクトの場合
    return date.strftime("%Y-%m-%d")


def format_progress(progress: float) -> str:
    """
    進捗率をフォーマットする
    
    Args:
        progress: 進捗率
        
    Returns:
        フォーマットされた進捗率文字列
    """
    return f"{progress:.1f}%"


def format_hours(hours: float) -> str:
    """
    工数をフォーマットする
    
    Args:
        hours: 工数（時間）
        
    Returns:
        フォーマットされた工数文字列
    """
    return f"{hours:.1f}h"


def datetime_to_qdatetime(dt: Optional[datetime]) -> Optional[QDateTime]:
    """
    datetimeをQDateTimeに変換
    
    Args:
        dt: 変換する日時オブジェクト、またはNone
        
    Returns:
        変換されたQDateTime、またはNone
    """
    if dt is None:
        return None
    return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


def qdatetime_to_datetime(qdt: QDateTime) -> datetime:
    """
    QDateTimeをdatetimeに変換
    
    Args:
        qdt: 変換するQDateTime
        
    Returns:
        変換されたdatetime
    """
    date = qdt.date()
    time = qdt.time()
    return datetime(date.year(), date.month(), date.day(), 
                    time.hour(), time.minute(), time.second())


def show_error_message(parent: QWidget, title: str, message: str) -> None:
    """
    エラーメッセージを表示
    
    Args:
        parent: 親ウィジェット
        title: メッセージのタイトル
        message: メッセージの内容
    """
    QMessageBox.critical(parent, title, message)


def show_info_message(parent: QWidget, title: str, message: str) -> None:
    """
    情報メッセージを表示
    
    Args:
        parent: 親ウィジェット
        title: メッセージのタイトル
        message: メッセージの内容
    """
    QMessageBox.information(parent, title, message)


def show_confirm_dialog(parent: QWidget, title: str, message: str) -> bool:
    """
    確認ダイアログを表示
    
    Args:
        parent: 親ウィジェット
        title: ダイアログのタイトル
        message: ダイアログのメッセージ
        
    Returns:
        ユーザーが確認した場合True、キャンセルした場合False
    """
    reply = QMessageBox.question(
        parent, title, message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    return reply == QMessageBox.StandardButton.Yes


def get_status_color(status: str) -> str:
    """
    状態に応じた色を取得（後方互換性のために維持）
    
    Args:
        status: 状態文字列
        
    Returns:
        色を表すCSS文字列
    """
    return ColorScheme.get_status_color(status)
