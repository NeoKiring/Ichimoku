"""
ガントチャートタブ
プロジェクト管理システムのガントチャートタブを提供
"""
from typing import Dict, Any, List, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QToolBar, QFrame, QSplitter, QScrollArea, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from .gantt_chart_widget import GanttChartWidget
from .utils import show_error_message, show_info_message


class GanttChartTab(QWidget):
    """
    プロジェクトのガントチャートを表示するタブ
    """
    
    def __init__(self, controller):
        """
        ガントチャートタブの初期化
        
        Args:
            controller: GUIコントローラ
        """
        super().__init__()
        
        self.controller = controller
        
        # ガントチャートウィジェット
        self.gantt_chart = GanttChartWidget()
        self.gantt_chart.item_clicked.connect(self.on_gantt_item_clicked)
        
        self.init_ui()
        
        # コントローラのシグナルを接続
        self.controller.project_changed.connect(self.refresh_gantt_chart)
        self.controller.phases_changed.connect(self.refresh_gantt_chart)
        self.controller.processes_changed.connect(self.refresh_gantt_chart)
        self.controller.tasks_changed.connect(self.refresh_gantt_chart)
    
    def init_ui(self):
        """UIの初期化"""
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # ツールバー
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))
        
        # 更新ボタン
        refresh_action = QAction("更新", self)
        refresh_action.triggered.connect(self.refresh_gantt_chart)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # ズームイン/アウト
        zoom_in_action = QAction("拡大", self)
        zoom_in_action.triggered.connect(self.gantt_chart.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("縮小", self)
        zoom_out_action.triggered.connect(self.gantt_chart.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        fit_content_action = QAction("全体表示", self)
        fit_content_action.triggered.connect(self.gantt_chart.fit_content)
        toolbar.addAction(fit_content_action)
        
        toolbar.addSeparator()
        
        # 表示設定
        toolbar.addWidget(QLabel("表示設定:"))
        
        # 表示レベル選択
        self.level_combo = QComboBox()
        self.level_combo.addItem("すべて表示", -1)
        self.level_combo.addItem("プロジェクト/フェーズ", 1)
        self.level_combo.addItem("プロジェクト/フェーズ/プロセス", 2)
        self.level_combo.addItem("タスクを含む", 3)
        self.level_combo.currentIndexChanged.connect(self.on_level_changed)
        toolbar.addWidget(self.level_combo)
        
        main_layout.addWidget(toolbar)
        
        # スプリッター
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # ガントチャート
        gantt_container = QWidget()
        gantt_layout = QVBoxLayout(gantt_container)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        gantt_layout.addWidget(self.gantt_chart)
        
        splitter.addWidget(gantt_container)
        
        # 詳細情報パネル
        details_panel = QFrame()
        details_panel.setFrameShape(QFrame.Shape.StyledPanel)
        details_panel.setMaximumHeight(200)
        
        details_layout = QVBoxLayout(details_panel)
        
        # 詳細情報ヘッダー
        self.details_header = QLabel("詳細情報")
        self.details_header.setStyleSheet("font-weight: bold;")
        details_layout.addWidget(self.details_header)
        
        # 詳細情報コンテンツ
        self.details_content = QLabel("アイテムを選択してください")
        details_layout.addWidget(self.details_content)
        
        # ボタンエリア
        buttons_layout = QHBoxLayout()
        
        # 編集ボタン
        self.edit_button = QPushButton("編集")
        self.edit_button.clicked.connect(self.edit_selected_item)
        self.edit_button.setEnabled(False)
        buttons_layout.addWidget(self.edit_button)
        
        # スケジュール調整ボタン
        self.adjust_schedule_button = QPushButton("スケジュール調整")
        self.adjust_schedule_button.clicked.connect(self.adjust_schedule)
        self.adjust_schedule_button.setEnabled(False)
        buttons_layout.addWidget(self.adjust_schedule_button)
        
        buttons_layout.addStretch()
        details_layout.addLayout(buttons_layout)
        
        splitter.addWidget(details_panel)
        
        # スプリッターの比率設定
        splitter.setSizes([700, 200])
        
        main_layout.addWidget(splitter)
        
        # 現在選択中のアイテム
        self.selected_item_type = None
        self.selected_item_id = None
    
    def refresh_gantt_chart(self):
        """ガントチャートを更新"""
        project_data = self.get_chart_data()
        
        if not project_data:
            self.gantt_chart.set_project_data(None)
            self.details_header.setText("詳細情報")
            self.details_content.setText("プロジェクトが読み込まれていません")
            self.edit_button.setEnabled(False)
            self.adjust_schedule_button.setEnabled(False)
            return
        
        # ガントチャートにデータを設定
        self.gantt_chart.set_project_data(project_data)
    
    def get_chart_data(self) -> Optional[Dict[str, Any]]:
        """
        ガントチャート用のデータを取得
        
        Returns:
            ガントチャート用のデータ、または None
        """
        # 現在のプロジェクト情報を取得
        project_data = self.controller.get_current_project()
        if not project_data:
            return None
        
        # ガントチャート用のデータ構造を作成
        chart_data = {
            "id": project_data["id"],
            "name": project_data["name"],
            "description": project_data["description"],
            "status": project_data["status"],
            "progress": project_data["progress"],
            "start_date": project_data["start_date"],
            "end_date": project_data["end_date"],
            "created_at": project_data["created_at"],
            "updated_at": project_data["updated_at"],
            "phases": []
        }
        
        # フェーズ情報を取得
        phases = self.controller.get_phases()
        for phase in phases:
            phase_data = {
                "id": phase["id"],
                "name": phase["name"],
                "description": phase.get("description", ""),
                "progress": phase["progress"],
                "start_date": phase.get("start_date"),
                "end_date": phase.get("end_date"),
                "processes": []
            }
            
            # プロセス情報を取得
            processes = self.controller.get_processes(phase["id"])
            for process in processes:
                process_data = {
                    "id": process["id"],
                    "name": process["name"],
                    "description": process.get("description", ""),
                    "assignee": process.get("assignee", ""),
                    "progress": process["progress"],
                    "start_date": process.get("start_date"),
                    "end_date": process.get("end_date"),
                    "estimated_hours": process.get("estimated_hours", 0),
                    "actual_hours": process.get("actual_hours", 0),
                    "tasks": []
                }
                
                # タスク情報を取得
                tasks = self.controller.get_tasks(phase["id"], process["id"])
                for task in tasks:
                    task_data = {
                        "id": task["id"],
                        "name": task["name"],
                        "description": task.get("description", ""),
                        "status": task["status"],
                        "created_at": task["created_at"],
                        "updated_at": task["updated_at"]
                    }
                    process_data["tasks"].append(task_data)
                
                phase_data["processes"].append(process_data)
            
            chart_data["phases"].append(phase_data)
        
        return chart_data
    
    def on_gantt_item_clicked(self, item_type: str, item_id: str):
        """
        ガントチャート上のアイテムがクリックされたときの処理
        
        Args:
            item_type: アイテムタイプ（'project', 'phase', 'process', 'task'）
            item_id: アイテムID
        """
        self.selected_item_type = item_type
        self.selected_item_id = item_id
        
        # 詳細情報を表示
        self.show_details(item_type, item_id)
        
        # ボタンの有効/無効を設定
        self.edit_button.setEnabled(True)
        self.adjust_schedule_button.setEnabled(item_type in ["project", "phase", "process"])
    
    def show_details(self, item_type: str, item_id: str):
        """
        選択されたアイテムの詳細情報を表示
        
        Args:
            item_type: アイテムタイプ
            item_id: アイテムID
        """
        if item_type == "project":
            # プロジェクトの詳細
            project_data = self.controller.get_current_project()
            if not project_data:
                return
            
            self.details_header.setText(f"プロジェクト: {project_data['name']}")
            
            details = f"""
            <p><b>ID:</b> {project_data['id']}</p>
            <p><b>説明:</b> {project_data['description']}</p>
            <p><b>状態:</b> {project_data['status']}</p>
            <p><b>進捗率:</b> {project_data['progress']:.1f}%</p>
            <p><b>開始日:</b> {project_data['start_date'].strftime('%Y-%m-%d') if project_data['start_date'] else '未設定'}</p>
            <p><b>終了日:</b> {project_data['end_date'].strftime('%Y-%m-%d') if project_data['end_date'] else '未設定'}</p>
            """
            
            self.details_content.setText(details)
            
        elif item_type == "phase":
            # フェーズの詳細
            phase_data = self.controller.get_phase_details(item_id)
            if not phase_data:
                return
            
            self.details_header.setText(f"フェーズ: {phase_data['name']}")
            
            details = f"""
            <p><b>ID:</b> {phase_data['id']}</p>
            <p><b>説明:</b> {phase_data['description']}</p>
            <p><b>進捗率:</b> {phase_data['progress']:.1f}%</p>
            <p><b>開始日:</b> {phase_data['start_date'].strftime('%Y-%m-%d') if phase_data['start_date'] else '未設定'}</p>
            <p><b>終了日:</b> {phase_data['end_date'].strftime('%Y-%m-%d') if phase_data['end_date'] else '未設定'}</p>
            """
            
            self.details_content.setText(details)
            
        elif item_type == "process":
            # プロセスの詳細（親フェーズIDを特定する必要がある）
            phase_id = self.find_parent_phase_id(item_id)
            if not phase_id:
                return
            
            process_data = self.controller.get_process_details(phase_id, item_id)
            if not process_data:
                return
            
            self.details_header.setText(f"プロセス: {process_data['name']}")
            
            details = f"""
            <p><b>ID:</b> {process_data['id']}</p>
            <p><b>説明:</b> {process_data['description']}</p>
            <p><b>担当者:</b> {process_data['assignee'] or '未割当'}</p>
            <p><b>進捗率:</b> {process_data['progress']:.1f}%</p>
            <p><b>開始日:</b> {process_data['start_date'].strftime('%Y-%m-%d') if process_data['start_date'] else '未設定'}</p>
            <p><b>終了日:</b> {process_data['end_date'].strftime('%Y-%m-%d') if process_data['end_date'] else '未設定'}</p>
            <p><b>予想工数:</b> {process_data['estimated_hours']:.1f}h</p>
            <p><b>実工数:</b> {process_data['actual_hours']:.1f}h</p>
            """
            
            self.details_content.setText(details)
            
        elif item_type == "task":
            # タスクの詳細（親プロセスとフェーズIDを特定する必要がある）
            parent_ids = self.find_parent_ids_for_task(item_id)
            if not parent_ids:
                return
            
            phase_id, process_id = parent_ids
            task_data = self.controller.get_task_details(phase_id, process_id, item_id)
            if not task_data:
                return
            
            self.details_header.setText(f"タスク: {task_data['name']}")
            
            details = f"""
            <p><b>ID:</b> {task_data['id']}</p>
            <p><b>説明:</b> {task_data['description']}</p>
            <p><b>状態:</b> {task_data['status']}</p>
            <p><b>作成日時:</b> {task_data['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
            <p><b>更新日時:</b> {task_data['updated_at'].strftime('%Y-%m-%d %H:%M')}</p>
            """
            
            self.details_content.setText(details)
    
    def find_parent_phase_id(self, process_id: str) -> Optional[str]:
        """
        プロセスの親フェーズIDを検索
        
        Args:
            process_id: プロセスID
            
        Returns:
            親フェーズID、または None
        """
        project_data = self.get_chart_data()
        if not project_data:
            return None
        
        for phase in project_data["phases"]:
            for process in phase["processes"]:
                if process["id"] == process_id:
                    return phase["id"]
        
        return None
    
    def find_parent_ids_for_task(self, task_id: str) -> Optional[tuple]:
        """
        タスクの親プロセスとフェーズIDを検索
        
        Args:
            task_id: タスクID
            
        Returns:
            (phase_id, process_id)のタプル、または None
        """
        project_data = self.get_chart_data()
        if not project_data:
            return None
        
        for phase in project_data["phases"]:
            for process in phase["processes"]:
                for task in process["tasks"]:
                    if task["id"] == task_id:
                        return (phase["id"], process["id"])
        
        return None
    
    def edit_selected_item(self):
        """選択されたアイテムを編集"""
        if not self.selected_item_type or not self.selected_item_id:
            return
        
        # 親ウィンドウのメソッドを使って適切な編集ダイアログを表示
        parent_window = self.window()
        if self.selected_item_type == "project":
            if hasattr(parent_window, 'edit_current_project'):
                parent_window.edit_current_project()
        
        elif self.selected_item_type == "phase":
            if hasattr(parent_window, 'edit_phase'):
                parent_window.edit_phase(self.selected_item_id)
        
        elif self.selected_item_type == "process":
            phase_id = self.find_parent_phase_id(self.selected_item_id)
            if phase_id and hasattr(parent_window, 'edit_process'):
                parent_window.edit_process(phase_id, self.selected_item_id)
        
        elif self.selected_item_type == "task":
            parent_ids = self.find_parent_ids_for_task(self.selected_item_id)
            if parent_ids and hasattr(parent_window, 'edit_task'):
                phase_id, process_id = parent_ids
                parent_window.edit_task(phase_id, process_id, self.selected_item_id)
    
    def adjust_schedule(self):
        """スケジュール調整ダイアログを表示"""
        if not self.selected_item_type or not self.selected_item_id:
            return
        
        # スケジュール調整は 'project', 'phase', 'process' のみ対応
        if self.selected_item_type not in ["project", "phase", "process"]:
            return
        
        # スケジュール調整ダイアログを表示（将来実装予定）
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QDateEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("スケジュール調整")
        
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        
        start_date_edit = QDateEdit()
        start_date_edit.setCalendarPopup(True)
        form_layout.addRow("開始日:", start_date_edit)
        
        end_date_edit = QDateEdit()
        end_date_edit.setCalendarPopup(True)
        form_layout.addRow("終了日:", end_date_edit)
        
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 現在の日付を設定
        if self.selected_item_type == "project":
            data = self.controller.get_current_project()
        elif self.selected_item_type == "phase":
            data = self.controller.get_phase_details(self.selected_item_id)
        elif self.selected_item_type == "process":
            phase_id = self.find_parent_phase_id(self.selected_item_id)
            if phase_id:
                data = self.controller.get_process_details(phase_id, self.selected_item_id)
            else:
                data = None
        
        if data:
            if data.get("start_date"):
                start_date = data["start_date"]
                start_date_edit.setDate(start_date)
            
            if data.get("end_date"):
                end_date = data["end_date"]
                end_date_edit.setDate(end_date)
        
        # ダイアログを表示
        result = dialog.exec()
        
        # OKが押された場合、日付を更新
        if result == QDialog.DialogCode.Accepted:
            # 実際の更新処理は将来実装予定
            show_info_message(self, "情報", "スケジュール調整機能は将来のバージョンで実装予定です。")
    
    def on_level_changed(self, index: int):
        """
        表示レベルが変更されたときの処理
        
        Args:
            index: コンボボックスのインデックス
        """
        # 現在は未実装（将来拡張予定）
        level = self.level_combo.currentData()
        # TODO: 選択されたレベルに応じてガントチャートの表示を調整
