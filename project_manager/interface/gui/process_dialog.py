"""
プロセスダイアログ
プロセスの作成・編集を行うダイアログ
"""
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QDateEdit, QDoubleSpinBox, QPushButton, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate

from .utils import datetime_to_qdatetime, qdatetime_to_datetime


class ProcessDialog(QDialog):
    """
    プロセスの作成・編集を行うダイアログ
    """
    
    def __init__(self, parent=None, process_data: Optional[Dict[str, Any]] = None):
        """
        ダイアログの初期化
        
        Args:
            parent: 親ウィジェット
            process_data: 編集モードの場合の既存プロセスデータ
        """
        super().__init__(parent)
        
        self.process_data = process_data
        self.is_edit_mode = process_data is not None
        
        self.init_ui()
        
        # 編集モードの場合、既存のデータをフォームにセット
        if self.is_edit_mode:
            self.set_form_data(process_data)
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("プロセスの追加" if not self.is_edit_mode else "プロセスの編集")
        self.setMinimumWidth(450)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 名前入力
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("プロセス名を入力してください")
        form_layout.addRow("名前:", self.name_edit)
        
        # 説明入力
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("プロセスの説明を入力してください")
        self.description_edit.setMinimumHeight(80)
        form_layout.addRow("説明:", self.description_edit)
        
        # 担当者入力
        self.assignee_edit = QLineEdit()
        self.assignee_edit.setPlaceholderText("担当者名を入力してください")
        form_layout.addRow("担当者:", self.assignee_edit)
        
        # 編集モードの場合の追加フィールド
        if self.is_edit_mode:
            # 開始日入力
            self.start_date_edit = QDateEdit()
            self.start_date_edit.setCalendarPopup(True)
            self.start_date_edit.setDate(QDate.currentDate())
            self.start_date_edit.setSpecialValueText("未設定")
            self.start_date_edit.setMinimumDate(QDate(2000, 1, 1))
            form_layout.addRow("開始日:", self.start_date_edit)
            
            # 終了日入力
            self.end_date_edit = QDateEdit()
            self.end_date_edit.setCalendarPopup(True)
            self.end_date_edit.setDate(QDate.currentDate())
            self.end_date_edit.setSpecialValueText("未設定")
            self.end_date_edit.setMinimumDate(QDate(2000, 1, 1))
            form_layout.addRow("終了日:", self.end_date_edit)
            
            # 予想工数入力
            self.estimated_hours_spin = QDoubleSpinBox()
            self.estimated_hours_spin.setRange(0, 9999.9)
            self.estimated_hours_spin.setDecimals(1)
            self.estimated_hours_spin.setSuffix(" 時間")
            self.estimated_hours_spin.setSingleStep(0.5)
            form_layout.addRow("予想工数:", self.estimated_hours_spin)
            
            # 実工数入力
            self.actual_hours_spin = QDoubleSpinBox()
            self.actual_hours_spin.setRange(0, 9999.9)
            self.actual_hours_spin.setDecimals(1)
            self.actual_hours_spin.setSuffix(" 時間")
            self.actual_hours_spin.setSingleStep(0.5)
            form_layout.addRow("実工数:", self.actual_hours_spin)
        
        main_layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
    
    def set_form_data(self, process_data: Dict[str, Any]):
        """
        フォームにデータをセット
        
        Args:
            process_data: プロセスデータ
        """
        self.name_edit.setText(process_data["name"])
        self.description_edit.setText(process_data["description"])
        self.assignee_edit.setText(process_data.get("assignee", ""))
        
        if self.is_edit_mode:
            # 開始日
            if process_data.get("start_date"):
                start_date = process_data["start_date"]
                qdate = QDate(start_date.year, start_date.month, start_date.day)
                self.start_date_edit.setDate(qdate)
            
            # 終了日
            if process_data.get("end_date"):
                end_date = process_data["end_date"]
                qdate = QDate(end_date.year, end_date.month, end_date.day)
                self.end_date_edit.setDate(qdate)
            
            # 予想工数
            self.estimated_hours_spin.setValue(process_data.get("estimated_hours", 0.0))
            
            # 実工数
            self.actual_hours_spin.setValue(process_data.get("actual_hours", 0.0))
    
    def get_process_data(self) -> Dict[str, Any]:
        """
        フォームから入力データを取得
        
        Returns:
            プロセスデータ
        """
        data = {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "assignee": self.assignee_edit.text().strip()
        }
        
        if self.is_edit_mode:
            # 開始日
            if self.start_date_edit.specialValueText() != self.start_date_edit.text():
                qdate = self.start_date_edit.date()
                data["start_date"] = datetime(qdate.year(), qdate.month(), qdate.day())
            
            # 終了日
            if self.end_date_edit.specialValueText() != self.end_date_edit.text():
                qdate = self.end_date_edit.date()
                data["end_date"] = datetime(qdate.year(), qdate.month(), qdate.day())
            
            # 予想工数
            data["estimated_hours"] = self.estimated_hours_spin.value()
            
            # 実工数
            data["actual_hours"] = self.actual_hours_spin.value()
        
        return data
