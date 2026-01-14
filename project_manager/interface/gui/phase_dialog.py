"""
フェーズダイアログ
フェーズの作成・編集を行うダイアログ
"""
from typing import Dict, Any, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QDateEdit, QPushButton, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, QDate

from .utils import datetime_to_qdatetime, qdatetime_to_datetime


class PhaseDialog(QDialog):
    """
    フェーズの作成・編集を行うダイアログ
    """
    
    def __init__(self, parent=None, phase_data: Optional[Dict[str, Any]] = None):
        """
        ダイアログの初期化
        
        Args:
            parent: 親ウィジェット
            phase_data: 編集モードの場合の既存フェーズデータ
        """
        super().__init__(parent)
        
        self.phase_data = phase_data
        self.is_edit_mode = phase_data is not None
        
        self.init_ui()
        
        # 編集モードの場合、既存のデータをフォームにセット
        if self.is_edit_mode:
            self.set_form_data(phase_data)
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("フェーズの追加" if not self.is_edit_mode else "フェーズの編集")
        self.setMinimumWidth(400)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 名前入力
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("フェーズ名を入力してください")
        form_layout.addRow("名前:", self.name_edit)
        
        # 説明入力
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("フェーズの説明を入力してください")
        self.description_edit.setMinimumHeight(100)
        form_layout.addRow("説明:", self.description_edit)
        
        # 終了日入力（編集モードのみ）
        self.end_date_edit = None
        if self.is_edit_mode:
            self.end_date_edit = QDateEdit()
            self.end_date_edit.setCalendarPopup(True)
            self.end_date_edit.setDate(QDate.currentDate())
            self.end_date_edit.setSpecialValueText("未設定")  # NULLを表す特殊値
            self.end_date_edit.setMinimumDate(QDate(2000, 1, 1))
            form_layout.addRow("終了日:", self.end_date_edit)
        
        main_layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
    
    def set_form_data(self, phase_data: Dict[str, Any]):
        """
        フォームにデータをセット
        
        Args:
            phase_data: フェーズデータ
        """
        self.name_edit.setText(phase_data["name"])
        self.description_edit.setText(phase_data["description"])
        
        if self.end_date_edit and phase_data.get("end_date"):
            end_date = phase_data["end_date"]
            qdate = QDate(end_date.year, end_date.month, end_date.day)
            self.end_date_edit.setDate(qdate)
    
    def get_phase_data(self) -> Dict[str, Any]:
        """
        フォームから入力データを取得
        
        Returns:
            フェーズデータ
        """
        data = {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip()
        }
        
        if self.is_edit_mode and self.end_date_edit:
            # 未設定の場合はNoneを返す
            if self.end_date_edit.specialValueText() == self.end_date_edit.text():
                data["end_date"] = None
            else:
                # QDateをdatetimeに変換
                qdate = self.end_date_edit.date()
                data["end_date"] = datetime(qdate.year(), qdate.month(), qdate.day())
        
        return data
