"""
通知タブ
プロジェクト管理システムの通知表示タブを提供
"""
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QCheckBox, QSpinBox, QFormLayout, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QColor, QIcon, QFont

from ...core.notification_manager import get_notification_manager
from ...models.notification import NotificationType, NotificationPriority, Notification
from .utils import show_error_message, show_info_message, show_confirm_dialog


class NotificationTab(QWidget):
    """
    プロジェクト管理システムの通知表示タブ
    """
    
    # 通知が選択されたときのシグナル（プロジェクト, エンティティタイプ, エンティティID）
    notification_selected = Signal(str, str, str)
    
    def __init__(self, controller):
        """
        通知タブの初期化
        
        Args:
            controller: GUIコントローラ
        """
        super().__init__()
        
        self.controller = controller
        self.notification_manager = get_notification_manager()
        
        # 自動更新タイマー
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.check_new_notifications)
        
        self.init_ui()
        
        # 初期データ読み込み
        self.load_notifications()
        
        # タイマー開始（5分ごとに更新）
        self.refresh_timer.start(5 * 60 * 1000)  # ミリ秒単位
    
    def init_ui(self):
        """UIの初期化"""
        main_layout = QVBoxLayout(self)
        
        # ヘッダーエリア
        header_layout = QHBoxLayout()
        header_label = QLabel("通知")
        header_label.setFont(QFont("", 14, QFont.Weight.Bold))
        header_layout.addWidget(header_label)
        
        # フィルタ
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("フィルタ:"))
        
        # タイプフィルタ
        self.type_filter = QComboBox()
        self.type_filter.addItem("すべての通知", None)
        for notification_type in NotificationType:
            self.type_filter.addItem(notification_type.value, notification_type.name)
        self.type_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("種類:"))
        filter_layout.addWidget(self.type_filter)
        
        # 優先度フィルタ
        self.priority_filter = QComboBox()
        self.priority_filter.addItem("すべての優先度", None)
        for priority in NotificationPriority:
            self.priority_filter.addItem(priority.value, priority.name)
        self.priority_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("優先度:"))
        filter_layout.addWidget(self.priority_filter)
        
        # 既読/未読フィルタ
        self.read_filter = QComboBox()
        self.read_filter.addItem("すべての通知", None)
        self.read_filter.addItem("未読のみ", False)
        self.read_filter.addItem("既読のみ", True)
        self.read_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("既読状態:"))
        filter_layout.addWidget(self.read_filter)
        
        header_layout.addLayout(filter_layout)
        
        # 操作ボタン
        buttons_layout = QHBoxLayout()
        
        # 通知の更新ボタン
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self.load_notifications)
        buttons_layout.addWidget(self.refresh_button)
        
        # すべて既読ボタン
        self.mark_all_read_button = QPushButton("すべて既読")
        self.mark_all_read_button.clicked.connect(self.mark_all_as_read)
        buttons_layout.addWidget(self.mark_all_read_button)
        
        # 古い通知を削除
        self.delete_old_button = QPushButton("古い通知を削除")
        self.delete_old_button.clicked.connect(self.delete_old_notifications)
        buttons_layout.addWidget(self.delete_old_button)
        
        # 設定
        self.settings_button = QPushButton("通知設定")
        self.settings_button.clicked.connect(self.show_settings_dialog)
        buttons_layout.addWidget(self.settings_button)
        
        header_layout.addLayout(buttons_layout)
        header_layout.addStretch(1)
        
        main_layout.addLayout(header_layout)
        
        # 通知テーブル
        self.notifications_table = QTableWidget()
        self.notifications_table.setColumnCount(6)
        self.notifications_table.setHorizontalHeaderLabels(["種類", "優先度", "メッセージ", "日時", "既読", "操作"])
        
        # 自動リサイズ設定
        self.notifications_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.notifications_table.horizontalHeader().setStretchLastSection(False)
        
        # 列の初期幅設定
        self.notifications_table.setColumnWidth(0, 100)  # 種類
        self.notifications_table.setColumnWidth(1, 80)   # 優先度
        self.notifications_table.setColumnWidth(2, 400)  # メッセージ
        self.notifications_table.setColumnWidth(3, 150)  # 日時
        self.notifications_table.setColumnWidth(4, 80)   # 既読
        self.notifications_table.setColumnWidth(5, 150)  # 操作
        
        self.notifications_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.notifications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # 行のダブルクリックで詳細表示
        self.notifications_table.cellDoubleClicked.connect(self.on_notification_double_clicked)
        
        main_layout.addWidget(self.notifications_table)
        
        # バッジ表示用
        self.unread_count_label = QLabel("0")
        self.unread_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unread_count_label.setStyleSheet("""
            background-color: #cc2535;
            color: white;
            border-radius: 10px;
            padding: 2px 6px;
            font-weight: bold;
        """)
        self.unread_count_label.setVisible(False)
        
        # 状態表示用ラベル
        self.status_label = QLabel("通知はありません")
        main_layout.addWidget(self.status_label)
    
    def load_notifications(self):
        """通知データを読み込む"""
        # 新規通知をチェック
        self.notification_manager.generate_notifications()
        
        # 通知データを取得
        all_notifications = self.notification_manager.get_all_notifications()
        
        # フィルターを適用
        filtered_notifications = self.filter_notifications(all_notifications)
        
        # テーブルを更新
        self.update_notification_table(filtered_notifications)
        
        # 未読数を更新
        self.update_unread_badge()
    
    def filter_notifications(self, notifications: List[Notification]) -> List[Notification]:
        """
        通知リストにフィルターを適用
        
        Args:
            notifications: 全通知リスト
            
        Returns:
            フィルター適用後の通知リスト
        """
        result = notifications
        
        # タイプフィルター
        notification_type = self.type_filter.currentData()
        if notification_type:
            result = [n for n in result if n.notification_type.name == notification_type]
        
        # 優先度フィルター
        priority = self.priority_filter.currentData()
        if priority:
            result = [n for n in result if n.priority.name == priority]
        
        # 既読フィルター
        read_status = self.read_filter.currentData()
        if read_status is not None:
            result = [n for n in result if n.read == read_status]
        
        return result
    
    def apply_filters(self):
        """フィルターを適用して通知テーブルを更新"""
        all_notifications = self.notification_manager.get_all_notifications()
        filtered_notifications = self.filter_notifications(all_notifications)
        self.update_notification_table(filtered_notifications)
    
    def update_notification_table(self, notifications: List[Notification]):
        """
        通知テーブルを更新
        
        Args:
            notifications: 表示する通知リスト
        """
        # テーブルをクリア
        self.notifications_table.setRowCount(0)
        
        if not notifications:
            self.status_label.setText("条件に一致する通知はありません")
            return
        
        # テーブルに通知を追加
        self.notifications_table.setRowCount(len(notifications))
        
        for row, notification in enumerate(notifications):
            # 種類
            type_item = QTableWidgetItem(notification.notification_type.value)
            self.notifications_table.setItem(row, 0, type_item)
            
            # 種類に応じた色を設定
            type_color = self.get_notification_type_color(notification.notification_type)
            type_item.setForeground(QColor(type_color))
            
            # 優先度
            priority_item = QTableWidgetItem(notification.priority.value)
            self.notifications_table.setItem(row, 1, priority_item)
            
            # 優先度に応じた色を設定
            priority_color = self.get_priority_color(notification.priority)
            priority_item.setForeground(QColor(priority_color))
            
            # メッセージ
            message_item = QTableWidgetItem(notification.message)
            self.notifications_table.setItem(row, 2, message_item)
            
            # 未読の場合は太字で表示
            if not notification.read:
                font = message_item.font()
                font.setBold(True)
                message_item.setFont(font)
            
            # 日時
            date_str = notification.created_at.strftime("%Y-%m-%d %H:%M")
            self.notifications_table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # 既読
            read_text = "既読" if notification.read else "未読"
            read_item = QTableWidgetItem(read_text)
            read_item.setForeground(QColor("#1a9735" if notification.read else "#cc2535"))
            self.notifications_table.setItem(row, 4, read_item)
            
            # 操作ボタン
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            # データをボタンに関連付け
            notification_id = notification.id
            entity_type = notification.entity_type
            entity_id = notification.entity_id
            project_id = notification.project_id
            
            # 詳細ボタン
            view_button = QPushButton("詳細")
            view_button.clicked.connect(lambda checked, pid=project_id, et=entity_type, eid=entity_id: 
                                        self.view_entity_detail(pid, et, eid))
            button_layout.addWidget(view_button)
            
            # 既読/削除ボタン
            if notification.read:
                delete_button = QPushButton("削除")
                delete_button.clicked.connect(lambda checked, nid=notification_id: 
                                            self.delete_notification(nid))
                button_layout.addWidget(delete_button)
            else:
                mark_read_button = QPushButton("既読")
                mark_read_button.clicked.connect(lambda checked, nid=notification_id: 
                                                self.mark_as_read(nid))
                button_layout.addWidget(mark_read_button)
            
            button_layout.setStretch(0, 1)
            button_layout.setStretch(1, 1)
            
            self.notifications_table.setCellWidget(row, 5, button_widget)
        
        self.status_label.setText(f"{len(notifications)}件の通知があります")
    
    def get_notification_type_color(self, notification_type: NotificationType) -> str:
        """
        通知タイプに応じた色を取得
        
        Args:
            notification_type: 通知タイプ
            
        Returns:
            色を表すCSSカラーコード
        """
        type_colors = {
            NotificationType.DEADLINE_APPROACHING: "#0068c4",  # 青
            NotificationType.DEADLINE_OVERDUE: "#cc2535",      # 赤
            NotificationType.PROGRESS_DELAY: "#ec9707",        # オレンジ
            NotificationType.LOW_PROGRESS: "#ec9707"           # オレンジ
        }
        return type_colors.get(notification_type, "#000000")
    
    def get_priority_color(self, priority: NotificationPriority) -> str:
        """
        優先度に応じた色を取得
        
        Args:
            priority: 優先度
            
        Returns:
            色を表すCSSカラーコード
        """
        priority_colors = {
            NotificationPriority.LOW: "#1a9735",    # 緑
            NotificationPriority.MEDIUM: "#ec9707", # オレンジ
            NotificationPriority.HIGH: "#cc2535"    # 赤
        }
        return priority_colors.get(priority, "#000000")
    
    def update_unread_badge(self):
        """未読バッジを更新"""
        unread_count = len(self.notification_manager.get_unread_notifications())
        
        if unread_count > 0:
            self.unread_count_label.setText(str(unread_count))
            self.unread_count_label.setVisible(True)
        else:
            self.unread_count_label.setVisible(False)
    
    def check_new_notifications(self):
        """新しい通知をチェック"""
        new_count = self.notification_manager.generate_notifications()
        
        if new_count > 0:
            # 新しい通知がある場合はリストを更新
            self.load_notifications()
            
            # 親ウィンドウがあれば、ステータスバーに通知
            parent_window = self.window()
            if hasattr(parent_window, 'statusBar'):
                parent_window.statusBar().showMessage(f"{new_count}件の新しい通知があります", 5000)
    
    def mark_as_read(self, notification_id: str):
        """
        通知を既読にする
        
        Args:
            notification_id: 通知ID
        """
        success = self.notification_manager.mark_as_read(notification_id)
        
        if success:
            # 通知リストを更新
            self.load_notifications()
        else:
            show_error_message(self, "エラー", "通知を既読にできませんでした")
    
    def mark_all_as_read(self):
        """すべての通知を既読にする"""
        count = self.notification_manager.mark_all_as_read()
        
        if count > 0:
            # 通知リストを更新
            self.load_notifications()
            show_info_message(self, "完了", f"{count}件の通知を既読にしました")
        else:
            show_info_message(self, "情報", "未読の通知はありません")
    
    def delete_notification(self, notification_id: str):
        """
        通知を削除する
        
        Args:
            notification_id: 通知ID
        """
        if show_confirm_dialog(self, "確認", "この通知を削除してもよろしいですか？"):
            success = self.notification_manager.delete_notification(notification_id)
            
            if success:
                # 通知リストを更新
                self.load_notifications()
            else:
                show_error_message(self, "エラー", "通知を削除できませんでした")
    
    def delete_old_notifications(self):
        """古い通知を削除するダイアログを表示"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QSpinBox, QDialogButtonBox, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("古い通知を削除")
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("指定された日数より古い通知を削除します。"))
        
        days_spin = QSpinBox()
        days_spin.setMinimum(1)
        days_spin.setMaximum(365)
        days_spin.setValue(30)
        days_spin.setSuffix(" 日")
        
        layout.addWidget(QLabel("何日前より古い通知を削除しますか？"))
        layout.addWidget(days_spin)
        
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            days = days_spin.value()
            deleted_count = self.notification_manager.delete_old_notifications(days)
            
            if deleted_count > 0:
                # 通知リストを更新
                self.load_notifications()
                show_info_message(self, "完了", f"{deleted_count}件の古い通知を削除しました")
            else:
                show_info_message(self, "情報", f"{days}日より古い通知はありませんでした")
    
    def show_settings_dialog(self):
        """通知設定ダイアログを表示"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QSpinBox, QDialogButtonBox, QLabel, QFormLayout, QGroupBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("通知設定")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # 期限通知設定
        deadline_group = QGroupBox("期限通知設定")
        deadline_layout = QFormLayout(deadline_group)
        
        warning_days_spin = QSpinBox()
        warning_days_spin.setMinimum(1)
        warning_days_spin.setMaximum(30)
        warning_days_spin.setValue(self.notification_manager.settings["deadline_warning_days"])
        warning_days_spin.setSuffix(" 日前")
        deadline_layout.addRow("期限通知の発生タイミング:", warning_days_spin)
        
        critical_days_spin = QSpinBox()
        critical_days_spin.setMinimum(1)
        critical_days_spin.setMaximum(30)
        critical_days_spin.setValue(self.notification_manager.settings["deadline_critical_days"])
        critical_days_spin.setSuffix(" 日前")
        deadline_layout.addRow("重要通知の発生タイミング:", critical_days_spin)
        
        layout.addWidget(deadline_group)
        
        # 進捗通知設定
        progress_group = QGroupBox("進捗通知設定")
        progress_layout = QFormLayout(progress_group)
        
        progress_threshold_spin = QSpinBox()
        progress_threshold_spin.setMinimum(10)
        progress_threshold_spin.setMaximum(90)
        progress_threshold_spin.setValue(int(self.notification_manager.settings["progress_threshold"] * 100))
        progress_threshold_spin.setSuffix(" %")
        progress_layout.addRow("進捗遅延のしきい値:", progress_threshold_spin)
        
        layout.addWidget(progress_group)
        
        # 通知確認設定
        check_group = QGroupBox("通知確認設定")
        check_layout = QFormLayout(check_group)
        
        check_interval_spin = QSpinBox()
        check_interval_spin.setMinimum(5)
        check_interval_spin.setMaximum(1440)  # 最大24時間（1440分）
        check_interval_spin.setValue(self.notification_manager.settings["check_interval_minutes"])
        check_interval_spin.setSuffix(" 分")
        check_layout.addRow("通知確認の間隔:", check_interval_spin)
        
        layout.addWidget(check_group)
        
        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # 設定を更新
            new_settings = {
                "deadline_warning_days": warning_days_spin.value(),
                "deadline_critical_days": critical_days_spin.value(),
                "progress_threshold": progress_threshold_spin.value() / 100,
                "check_interval_minutes": check_interval_spin.value()
            }
            
            self.notification_manager.update_settings(new_settings)
            
            # タイマーの間隔を更新
            self.refresh_timer.setInterval(new_settings["check_interval_minutes"] * 60 * 1000)
            
            show_info_message(self, "完了", "通知設定を更新しました")
    
    def view_entity_detail(self, project_id: str, entity_type: str, entity_id: str):
        """
        エンティティの詳細を表示
        
        Args:
            project_id: プロジェクトID
            entity_type: エンティティタイプ（"Project", "Phase", "Process", "Task"）
            entity_id: エンティティID
        """
        # プロジェクトを読み込む
        self.controller.load_project(project_id)
        
        # プロジェクト詳細タブに切り替え
        parent_window = self.window()
        for i in range(parent_window.tab_widget.count()):
            if parent_window.tab_widget.tabText(i) == "プロジェクト詳細":
                parent_window.tab_widget.setCurrentIndex(i)
                break
        
        # エンティティタイプに応じた処理
        if entity_type == "Project":
            # プロジェクト自体の場合は何もしない（既にプロジェクト詳細タブに切り替えた）
            pass
        elif entity_type == "Phase":
            # フェーズを選択
            self.controller.set_current_phase(entity_id)
            
            # UIで該当フェーズを選択
            if hasattr(parent_window, 'phases_tree'):
                root = parent_window.phases_tree.invisibleRootItem()
                for i in range(root.childCount()):
                    phase_item = root.child(i)
                    if phase_item.data(0, Qt.ItemDataRole.UserRole) == entity_id:
                        parent_window.phases_tree.setCurrentItem(phase_item)
                        break
        elif entity_type == "Process":
            # 親フェーズを見つける
            phase_id = None
            project = self.controller.manager.current_project
            if project:
                for phase in project.get_phases():
                    for process in phase.get_processes():
                        if process.id == entity_id:
                            phase_id = phase.id
                            break
                    if phase_id:
                        break
            
            if phase_id:
                # フェーズとプロセスを選択
                self.controller.set_current_phase(phase_id)
                self.controller.set_current_process(phase_id, entity_id)
                
                # UIで該当プロセスを選択
                if hasattr(parent_window, 'phases_tree'):
                    root = parent_window.phases_tree.invisibleRootItem()
                    for i in range(root.childCount()):
                        phase_item = root.child(i)
                        if phase_item.data(0, Qt.ItemDataRole.UserRole) == phase_id:
                            # フェーズを展開
                            phase_item.setExpanded(True)
                            
                            # プロセスを探して選択
                            for j in range(phase_item.childCount()):
                                process_item = phase_item.child(j)
                                if process_item.data(0, Qt.ItemDataRole.UserRole) == entity_id:
                                    parent_window.phases_tree.setCurrentItem(process_item)
                                    break
                            break
        
        # 通知選択シグナルを発行
        self.notification_selected.emit(project_id, entity_type, entity_id)
    
    def on_notification_double_clicked(self, row: int, column: int):
        """
        通知テーブルの行がダブルクリックされたとき
        
        Args:
            row: クリックされた行
            column: クリックされた列
        """
        # 通知IDを取得
        notification_id = None
        project_id = None
        entity_type = None
        entity_id = None
        
        # 現在表示中の通知を取得
        all_notifications = self.notification_manager.get_all_notifications()
        filtered_notifications = self.filter_notifications(all_notifications)
        
        if 0 <= row < len(filtered_notifications):
            notification = filtered_notifications[row]
            notification_id = notification.id
            project_id = notification.project_id
            entity_type = notification.entity_type
            entity_id = notification.entity_id
            
            # 既読でない場合は既読にする
            if not notification.read:
                self.notification_manager.mark_as_read(notification_id)
                self.load_notifications()
            
            # エンティティの詳細を表示
            self.view_entity_detail(project_id, entity_type, entity_id)
