"""
プロジェクトダイアログ
プロジェクトの作成・編集を行うダイアログ
"""
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt

from ...models import ProjectStatus


class ProjectDialog(QDialog):
    """
    プロジェクトの作成・編集を行うダイアログ
    """
    
    def __init__(self, parent=None, project_data: Optional[Dict[str, Any]] = None):
        """
        ダイアログの初期化
        
        Args:
            parent: 親ウィジェット
            project_data: 編集モードの場合の既存プロジェクトデータ
        """
        super().__init__(parent)
        
        self.project_data = project_data
        self.is_edit_mode = project_data is not None
        
        self.init_ui()
        
        # 編集モードの場合、既存のデータをフォームにセット
        if self.is_edit_mode:
            self.set_form_data(project_data)
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("プロジェクトの追加" if not self.is_edit_mode else "プロジェクトの編集")
        self.setMinimumWidth(400)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 名前入力
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("プロジェクト名を入力してください")
        form_layout.addRow("名前:", self.name_edit)
        
        # 説明入力
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("プロジェクトの説明を入力してください")
        self.description_edit.setMinimumHeight(100)
        form_layout.addRow("説明:", self.description_edit)
        
        # 状態選択（編集モードのみ）
        self.status_combo = None
        if self.is_edit_mode:
            self.status_combo = QComboBox()
            for status in ProjectStatus:
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
    
    def set_form_data(self, project_data: Dict[str, Any]):
        """
        フォームにデータをセット
        
        Args:
            project_data: プロジェクトデータ
        """
        self.name_edit.setText(project_data["name"])
        self.description_edit.setText(project_data["description"])
        
        if self.status_combo:
            index = self.status_combo.findText(project_data["status"])
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
    
    def get_project_data(self) -> Dict[str, Any]:
        """
        フォームから入力データを取得
        
        Returns:
            プロジェクトデータ
        """
        data = {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip()
        }
        
        if self.is_edit_mode and self.status_combo:
            status_text = self.status_combo.currentText()
            data["status"] = ProjectStatus(status_text)
        
        return data
