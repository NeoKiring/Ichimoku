"""
タスクダイアログ
タスクの作成・編集を行うダイアログ
"""
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt

from ...models import TaskStatus


class TaskDialog(QDialog):
    """
    タスクの作成・編集を行うダイアログ
    """
    
    def __init__(self, parent=None, task_data: Optional[Dict[str, Any]] = None):
        """
        ダイアログの初期化
        
        Args:
            parent: 親ウィジェット
            task_data: 編集モードの場合の既存タスクデータ
        """
        super().__init__(parent)
        
        self.task_data = task_data
        self.is_edit_mode = task_data is not None
        
        self.init_ui()
        
        # 編集モードの場合、既存のデータをフォームにセット
        if self.is_edit_mode:
            self.set_form_data(task_data)
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("タスクの追加" if not self.is_edit_mode else "タスクの編集")
        self.setMinimumWidth(400)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 名前入力
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("タスク名を入力してください")
        form_layout.addRow("名前:", self.name_edit)
        
        # 説明入力
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("タスクの説明を入力してください")
        self.description_edit.setMinimumHeight(80)
        form_layout.addRow("説明:", self.description_edit)
        
        # 状態選択
        self.status_combo = QComboBox()
        for status in TaskStatus:
            self.status_combo.addItem(status.value)
        form_layout.addRow("状態:", self.status_combo)
        
        main_layout.addLayout(form_layout)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout.addWidget(button_box)
    
    def set_form_data(self, task_data: Dict[str, Any]):
        """
        フォームにデータをセット
        
        Args:
            task_data: タスクデータ
        """
        self.name_edit.setText(task_data["name"])
        self.description_edit.setText(task_data["description"])
        
        # 状態
        if "status" in task_data:
            index = self.status_combo.findText(task_data["status"])
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
    
    def get_task_data(self) -> Dict[str, Any]:
        """
        フォームから入力データを取得
        
        Returns:
            タスクデータ
        """
        data = {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "status": TaskStatus(self.status_combo.currentText())
        }
        
        return data
