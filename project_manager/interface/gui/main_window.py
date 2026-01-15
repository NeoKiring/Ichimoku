"""
メインウィンドウ
プロジェクト管理システムのメインGUI画面
"""
from typing import Dict, Any, Optional, List
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QTreeWidget, QTreeWidgetItem, QProgressBar, QMenu,
    QMessageBox, QComboBox, QStatusBar, QToolBar, QApplication
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QColor, QFont

from .controller import GUIController
from .project_dialog import ProjectDialog
from .phase_dialog import PhaseDialog
from .process_dialog import ProcessDialog
from .task_dialog import TaskDialog
from .gantt_chart_tab import GanttChartTab
from .utils import (
    ColorScheme, format_date, format_progress, format_hours, 
    show_error_message, show_info_message, show_confirm_dialog,
    get_status_color
)

from ...models import ProjectStatus, TaskStatus


class MainWindow(QMainWindow):
    """
    プロジェクト管理システムのメインウィンドウ
    """
    
    def __init__(self, controller: GUIController):
        """
        メインウィンドウの初期化
        
        Args:
            controller: GUIコントローラー
        """
        super().__init__()
        
        self.controller = controller
        
        # モデル更新通知のシグナル接続
        self.controller.project_changed.connect(self.refresh_project_view)
        self.controller.phases_changed.connect(self.refresh_phases_view)
        self.controller.processes_changed.connect(self.refresh_processes_view)
        self.controller.tasks_changed.connect(self.refresh_tasks_view)
        
        # 更新タイマー（自動保存用）
        self.save_timer = QTimer(self)
        self.save_timer.setInterval(30000)  # 30秒ごとに保存
        self.save_timer.timeout.connect(self.auto_save_project)
        
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        
        # プロジェクト一覧を読み込み
        self.load_projects()
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("プロジェクト管理システム")
        self.setMinimumSize(1280, 800)
        self.resize(1400, 900)  # デフォルトサイズを設定
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # プロジェクト一覧タブ
        self.projects_tab = QWidget()
        self.setup_projects_tab()
        self.tab_widget.addTab(self.projects_tab, "プロジェクト一覧")
        
        # プロジェクト詳細タブ
        self.project_detail_tab = QWidget()
        self.setup_project_detail_tab()
        self.tab_widget.addTab(self.project_detail_tab, "プロジェクト詳細")
        
        # ガントチャートタブ
        from .gantt_chart_tab import GanttChartTab
        self.gantt_chart_tab = GanttChartTab(self.controller)
        self.tab_widget.addTab(self.gantt_chart_tab, "ガントチャート")

        # 全プロセスタブ
        self.all_processes_tab = QWidget()
        self.setup_all_processes_tab()
        self.tab_widget.addTab(self.all_processes_tab, "全プロセス一覧")

        # エラーログタブ
        from .error_log_tab import ErrorLogTab
        self.error_log_tab = ErrorLogTab()
        self.tab_widget.addTab(self.error_log_tab, "エラーログ")

        # 通知タブ
        from .notification_tab import NotificationTab
        self.notification_tab = NotificationTab(self.controller)
        self.tab_widget.addTab(self.notification_tab, "通知")

        # タブ切り替え時の処理
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

    def init_menu(self):
        """メニューの初期化"""
        # メニューバーの作成
        menu_bar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menu_bar.addMenu("ファイル")
        
        # 新規プロジェクト
        new_project_action = QAction("新規プロジェクト", self)
        new_project_action.triggered.connect(self.create_new_project)
        file_menu.addAction(new_project_action)
        
        # プロジェクトを開く
        open_project_action = QAction("プロジェクトを開く", self)
        open_project_action.triggered.connect(self.show_project_list)
        file_menu.addAction(open_project_action)
        
        file_menu.addSeparator()
        
        # 現在のプロジェクトを保存
        save_project_action = QAction("現在のプロジェクトを保存", self)
        save_project_action.triggered.connect(self.save_current_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        # 終了
        exit_action = QAction("終了", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # プロジェクトメニュー
        project_menu = menu_bar.addMenu("プロジェクト")
        
        # プロジェクト編集
        edit_project_action = QAction("プロジェクト編集", self)
        edit_project_action.triggered.connect(self.edit_current_project)
        project_menu.addAction(edit_project_action)
        
        # プロジェクト削除
        delete_project_action = QAction("プロジェクト削除", self)
        delete_project_action.triggered.connect(self.delete_current_project)
        project_menu.addAction(delete_project_action)
        
        project_menu.addSeparator()
        
        # フェーズ追加
        add_phase_action = QAction("フェーズ追加", self)
        add_phase_action.triggered.connect(self.create_new_phase)
        project_menu.addAction(add_phase_action)
        
        # 表示メニュー
        view_menu = menu_bar.addMenu("表示")

        # ガントチャート表示
        show_gantt_action = QAction("ガントチャート表示", self)
        show_gantt_action.triggered.connect(self.show_gantt_chart)
        view_menu.addAction(show_gantt_action)

        # エラーログ表示
        show_error_log_action = QAction("エラーログ表示", self)
        show_error_log_action.triggered.connect(self.show_error_log)
        view_menu.addAction(show_error_log_action)

        # 通知表示
        show_notifications_action = QAction("通知表示", self)
        show_notifications_action.triggered.connect(self.show_notifications)
        view_menu.addAction(show_notifications_action)

        # ヘルプメニュー
        help_menu = menu_bar.addMenu("ヘルプ")
        
        # バージョン情報
        about_action = QAction("バージョン情報", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # ファイルメニューにExcelインポート/エクスポートを追加
        file_menu.addSeparator()
        
        # Excel入出力
        excel_action = QAction("Excel入出力...", self)
        excel_action.triggered.connect(self.show_excel_dialog)
        file_menu.addAction(excel_action)
        
        # Excel一括インポート機能追加
        excel_bulk_import_action = QAction("Excel一括インポート...", self)
        excel_bulk_import_action.triggered.connect(self.show_bulk_excel_dialog)
        file_menu.addAction(excel_bulk_import_action)

    def show_bulk_excel_dialog(self):
        """Excel一括インポートダイアログを表示"""
        from .bulk_excel_dialog import BulkExcelImportDialog
        
        dialog = BulkExcelImportDialog(self, self.controller)
        dialog.exec()

    def init_toolbar(self):
        """ツールバーの初期化"""
        # メインツールバー
        main_toolbar = QToolBar("メインツールバー", self)
        main_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(main_toolbar)
        
        # 新規プロジェクト
        new_project_action = QAction("新規プロジェクト", self)
        new_project_action.triggered.connect(self.create_new_project)
        main_toolbar.addAction(new_project_action)
        
        # プロジェクトを開く
        open_project_action = QAction("プロジェクトを開く", self)
        open_project_action.triggered.connect(self.show_project_list)
        main_toolbar.addAction(open_project_action)
        
        # 保存
        save_project_action = QAction("保存", self)
        save_project_action.triggered.connect(self.save_current_project)
        main_toolbar.addAction(save_project_action)
        
        main_toolbar.addSeparator()
        
        # フェーズ追加
        add_phase_action = QAction("フェーズ追加", self)
        add_phase_action.triggered.connect(self.create_new_phase)
        main_toolbar.addAction(add_phase_action)
        
        # プロセス追加
        add_process_action = QAction("プロセス追加", self)
        add_process_action.triggered.connect(self.create_new_process)
        main_toolbar.addAction(add_process_action)
        
        # タスク追加
        add_task_action = QAction("タスク追加", self)
        add_task_action.triggered.connect(self.create_new_task)
        main_toolbar.addAction(add_task_action)

        main_toolbar.addSeparator()

        # ガントチャート表示
        show_gantt_action = QAction("ガントチャート", self)
        show_gantt_action.triggered.connect(self.show_gantt_chart)
        main_toolbar.addAction(show_gantt_action)

        # 通知ボタン
        self.notification_button = QPushButton()
        self.notification_button.setToolTip("通知を表示")
        self.notification_button.clicked.connect(self.show_notifications)

        # 通知バッジ（未読数表示）
        self.notification_badge = QLabel("0")
        self.notification_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notification_badge.setStyleSheet("""
            background-color: #cc2535;
            color: white;
            border-radius: 10px;
            padding: 2px 6px;
            font-weight: bold;
            min-width: 16px;
        """)
        self.notification_badge.setVisible(False)

        # ボタンとバッジを含むウィジェット
        notification_widget = QWidget()
        notification_layout = QHBoxLayout(notification_widget)
        notification_layout.setContentsMargins(0, 0, 0, 0)
        notification_layout.addWidget(self.notification_button)
        notification_layout.addWidget(self.notification_badge)

        main_toolbar.addWidget(notification_widget)

    def init_statusbar(self):
        """ステータスバーの初期化"""
        self.statusBar().showMessage("準備完了")
    
    def setup_projects_tab(self):
        """プロジェクト一覧タブの設定"""
        layout = QVBoxLayout(self.projects_tab)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("プロジェクト一覧"))
        
        # 新規プロジェクトボタン
        new_project_button = QPushButton("新規プロジェクト")
        new_project_button.clicked.connect(self.create_new_project)
        header_layout.addWidget(new_project_button)
        
        # 更新ボタン
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.load_projects)
        header_layout.addWidget(refresh_button)
        
        # 右寄せ
        header_layout.addStretch(1)
        
        layout.addLayout(header_layout)
        
        # プロジェクト一覧テーブル
        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(6)
        self.projects_table.setHorizontalHeaderLabels(["ID", "名前", "状態", "進捗率", "更新日時", "操作"])
        
        # リサイズ可能に変更
        self.projects_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.projects_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # 初期列幅を設定（合計: 1200px）
        self.projects_table.setColumnWidth(0, 120)  # ID
        self.projects_table.setColumnWidth(1, 350)  # 名前
        self.projects_table.setColumnWidth(2, 120)  # 状態
        self.projects_table.setColumnWidth(3, 100)  # 進捗率
        self.projects_table.setColumnWidth(4, 180)  # 更新日時
        self.projects_table.setColumnWidth(5, 230)  # 操作

        self.projects_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.projects_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # ダブルクリックでプロジェクトを開く
        self.projects_table.cellDoubleClicked.connect(self.on_project_double_clicked)
        
        layout.addWidget(self.projects_table)
    
    def setup_project_detail_tab(self):
        """プロジェクト詳細タブの設定"""
        layout = QVBoxLayout(self.project_detail_tab)
        
        # プロジェクト情報ヘッダー
        self.project_header = QLabel("プロジェクトが選択されていません")
        self.project_header.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(self.project_header)
        
        # プロジェクト情報
        self.project_info_layout = QHBoxLayout()
        
        # 左側: プロジェクト基本情報
        self.project_basic_info = QLabel()
        self.project_info_layout.addWidget(self.project_basic_info, 1)
        
        # 右側: プロジェクト進捗状況
        self.project_progress_info = QLabel()
        self.project_info_layout.addWidget(self.project_progress_info, 1)
        
        layout.addLayout(self.project_info_layout)
        
        # 状態変更ボタンエリア
        status_buttons_layout = QHBoxLayout()
        
        # 保留ボタン
        self.on_hold_button = QPushButton("保留")
        self.on_hold_button.clicked.connect(self.set_project_on_hold)
        status_buttons_layout.addWidget(self.on_hold_button)
        
        # 中止ボタン
        self.cancel_button = QPushButton("中止")
        self.cancel_button.clicked.connect(self.set_project_cancelled)
        status_buttons_layout.addWidget(self.cancel_button)
        
        # 解除ボタン
        self.release_button = QPushButton("解除")
        self.release_button.clicked.connect(self.release_project_status)
        status_buttons_layout.addWidget(self.release_button)
        
        # 右寄せ
        status_buttons_layout.addStretch(1)
        
        layout.addLayout(status_buttons_layout)
        
        # メインスプリッタ
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # 左側: フェーズツリー
        self.phases_tree = QTreeWidget()
        self.phases_tree.setHeaderLabels(["フェーズ/プロセス/タスク", "進捗", "担当者", "状態"])
        self.phases_tree.setColumnWidth(0, 250)
        self.phases_tree.setColumnWidth(1, 80)   # 進捗
        self.phases_tree.setColumnWidth(2, 100)  # 担当者
        self.phases_tree.setColumnWidth(3, 70)   # 状態
        self.phases_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.phases_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.phases_tree.itemSelectionChanged.connect(self.on_tree_selection_changed)
        splitter.addWidget(self.phases_tree)
        
        # 右側: 詳細表示エリア
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        
        # 詳細情報ヘッダー
        self.detail_header = QLabel("詳細情報")
        self.detail_header.setFont(QFont("", 12, QFont.Weight.Bold))
        self.detail_layout.addWidget(self.detail_header)
        
        # 詳細情報内容
        self.detail_content = QLabel("項目を選択してください")
        self.detail_layout.addWidget(self.detail_content)
        
        # タスク一覧表（プロセス選択時のみ表示）
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(5)
        self.tasks_table.setHorizontalHeaderLabels(["ID", "名前", "状態", "更新日時", "操作"])

        # リサイズ可能に変更
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tasks_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # 初期列幅を設定（合計: 750px）
        self.tasks_table.setColumnWidth(0, 100)  # ID
        self.tasks_table.setColumnWidth(1, 250)  # 名前
        self.tasks_table.setColumnWidth(2, 100)  # 状態
        self.tasks_table.setColumnWidth(3, 150)  # 更新日時
        self.tasks_table.setColumnWidth(4, 150)  # 操作

        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tasks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tasks_table.setVisible(False)
        
        self.detail_layout.addWidget(self.tasks_table)
        
        # ボタンエリア
        self.detail_buttons_layout = QHBoxLayout()
        
        # 編集ボタン
        self.edit_detail_button = QPushButton("編集")
        self.edit_detail_button.clicked.connect(self.edit_selected_item)
        self.detail_buttons_layout.addWidget(self.edit_detail_button)
        
        # 削除ボタン
        self.delete_detail_button = QPushButton("削除")
        self.delete_detail_button.clicked.connect(self.delete_selected_item)
        self.detail_buttons_layout.addWidget(self.delete_detail_button)
        
        # 追加ボタン（プロセスの場合はタスク追加、フェーズの場合はプロセス追加）
        self.add_child_button = QPushButton("子要素追加")
        self.add_child_button.clicked.connect(self.add_child_to_selected)
        self.detail_buttons_layout.addWidget(self.add_child_button)
        
        self.detail_buttons_layout.addStretch(1)
        
        self.detail_layout.addLayout(self.detail_buttons_layout)
        
        # ボタンは最初は無効化
        self.edit_detail_button.setEnabled(False)
        self.delete_detail_button.setEnabled(False)
        self.add_child_button.setEnabled(False)
        
        splitter.addWidget(self.detail_widget)

        # スプリッターの初期サイズ比率設定（ウィンドウサイズ拡大に合わせて調整）
        splitter.setSizes([500, 800])

        layout.addWidget(splitter)
    
    def setup_all_processes_tab(self):
        """全プロセスタブのセットアップ"""
        layout = QVBoxLayout(self.all_processes_tab)
        
        # ヘッダー部分
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("全プロジェクトのプロセス一覧"))
        
        # フィルターオプション
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("フィルタ:"))
        
        # 担当者フィルター
        self.assignee_filter = QComboBox()
        self.assignee_filter.addItem("すべての担当者", None)
        self.assignee_filter.currentIndexChanged.connect(self.apply_process_filters)
        filter_layout.addWidget(QLabel("担当者:"))
        filter_layout.addWidget(self.assignee_filter)
        
        # 状態フィルター
        self.status_filter = QComboBox()
        self.status_filter.addItem("すべての状態", None)
        self.status_filter.addItem("未着手", "未着手")
        self.status_filter.addItem("進行中", "進行中")
        self.status_filter.addItem("完了", "完了")
        self.status_filter.addItem("対応不能", "対応不能")
        self.status_filter.currentIndexChanged.connect(self.apply_process_filters)
        filter_layout.addWidget(QLabel("状態:"))
        filter_layout.addWidget(self.status_filter)
        
        # 期限フィルター
        self.deadline_filter = QComboBox()
        self.deadline_filter.addItem("すべての期限", 0)
        self.deadline_filter.addItem("期限切れ", -1)
        self.deadline_filter.addItem("今日まで", 0)
        self.deadline_filter.addItem("1週間以内", 7)
        self.deadline_filter.addItem("1ヶ月以内", 30)
        self.deadline_filter.currentIndexChanged.connect(self.apply_process_filters)
        filter_layout.addWidget(QLabel("期限:"))
        filter_layout.addWidget(self.deadline_filter)
        
        # 更新ボタン
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.refresh_all_processes)
        filter_layout.addWidget(refresh_button)
        
        # フィルターレイアウトをヘッダーに追加
        header_layout.addLayout(filter_layout)
        
        # 右寄せ
        header_layout.addStretch(1)
        
        layout.addLayout(header_layout)
        
        # プロセステーブル
        self.processes_table = QTableWidget()
        self.processes_table.setColumnCount(9)
        self.processes_table.setHorizontalHeaderLabels([
            "プロジェクト", "フェーズ", "プロセス名", "担当者", "進捗率", 
            "開始日", "終了日", "残り日数", "操作"
        ])

        # リサイズ可能に変更
        self.processes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.processes_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # 初期列幅を設定（合計: 1200px）
        self.processes_table.setColumnWidth(0, 140)  # プロジェクト
        self.processes_table.setColumnWidth(1, 130)  # フェーズ
        self.processes_table.setColumnWidth(2, 200)  # プロセス名
        self.processes_table.setColumnWidth(3, 100)  # 担当者
        self.processes_table.setColumnWidth(4, 80)   # 進捗率
        self.processes_table.setColumnWidth(5, 110)  # 開始日
        self.processes_table.setColumnWidth(6, 110)  # 終了日
        self.processes_table.setColumnWidth(7, 100)  # 残り日数
        self.processes_table.setColumnWidth(8, 180)  # 操作

        self.processes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.processes_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.processes_table.setSortingEnabled(True)
        
        layout.addWidget(self.processes_table)

    def load_projects(self):
        """プロジェクト一覧を読み込む"""
        projects = self.controller.get_projects()
        
        self.projects_table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # ID
            id_item = QTableWidgetItem(project["id"][:8] + "...")
            id_item.setData(Qt.ItemDataRole.UserRole, project["id"])
            self.projects_table.setItem(row, 0, id_item)
            
            # 名前
            self.projects_table.setItem(row, 1, QTableWidgetItem(project["name"]))
            
            # 状態
            status_item = QTableWidgetItem(project["status"])
            status_item.setForeground(QColor(get_status_color(project["status"])))
            self.projects_table.setItem(row, 2, status_item)
            
            # 進捗率
            self.projects_table.setItem(row, 3, QTableWidgetItem(format_progress(project["progress"])))
            
            # 更新日時
            update_time = datetime.fromisoformat(project["updated_at"])
            self.projects_table.setItem(row, 4, QTableWidgetItem(update_time.strftime("%Y-%m-%d %H:%M")))
            
            # 操作ボタン
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            # 開くボタン
            open_button = QPushButton("開く")
            open_button.setProperty("project_id", project["id"])
            open_button.clicked.connect(lambda checked, pid=project["id"]: self.open_project(pid))
            button_layout.addWidget(open_button)
            
            # 削除ボタン
            delete_button = QPushButton("削除")
            delete_button.setProperty("project_id", project["id"])
            delete_button.clicked.connect(lambda checked, pid=project["id"]: self.delete_project(pid))
            button_layout.addWidget(delete_button)
            
            button_layout.setStretch(0, 1)
            button_layout.setStretch(1, 1)
            
            self.projects_table.setCellWidget(row, 5, button_widget)
        
        self.statusBar().showMessage(f"{len(projects)}件のプロジェクトを読み込みました")
    
    def create_new_project(self):
        """新規プロジェクトを作成"""
        dialog = ProjectDialog(self)
        if dialog.exec():
            project_data = dialog.get_project_data()
            
            if not project_data["name"]:
                show_error_message(self, "エラー", "プロジェクト名を入力してください")
                return
            
            success = self.controller.create_project(
                project_data["name"],
                project_data["description"]
            )
            
            if success:
                show_info_message(self, "成功", f"プロジェクト「{project_data['name']}」を作成しました")
                self.load_projects()
                self.tab_widget.setCurrentIndex(1)  # プロジェクト詳細タブに切り替え
                
                # 自動保存タイマーを開始
                self.save_timer.start()
            else:
                show_error_message(self, "エラー", "プロジェクトの作成に失敗しました")
    
    def open_project(self, project_id: str):
        """
        プロジェクトを開く
        
        Args:
            project_id: 開くプロジェクトのID
        """
        success = self.controller.load_project(project_id)
        
        if success:
            self.tab_widget.setCurrentIndex(1)  # プロジェクト詳細タブに切り替え
            self.statusBar().showMessage("プロジェクトを読み込みました")
            
            # 自動保存タイマーを開始
            self.save_timer.start()
        else:
            show_error_message(self, "エラー", "プロジェクトの読み込みに失敗しました")
    
    def delete_project(self, project_id: str):
        """
        プロジェクトを削除
        
        Args:
            project_id: 削除するプロジェクトのID
        """
        if show_confirm_dialog(self, "確認", "このプロジェクトを削除してもよろしいですか？この操作は元に戻せません。"):
            success = self.controller.delete_project(project_id)
            
            if success:
                show_info_message(self, "成功", "プロジェクトを削除しました")
                self.load_projects()
            else:
                show_error_message(self, "エラー", "プロジェクトの削除に失敗しました")
    
    def edit_current_project(self):
        """現在のプロジェクトを編集"""
        project_data = self.controller.get_current_project()
        
        if not project_data:
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        dialog = ProjectDialog(self, project_data)
        if dialog.exec():
            updated_data = dialog.get_project_data()
            
            if not updated_data["name"]:
                show_error_message(self, "エラー", "プロジェクト名を入力してください")
                return
            
            success = self.controller.update_project(
                name=updated_data["name"],
                description=updated_data["description"],
                status=updated_data.get("status")
            )
            
            if success:
                show_info_message(self, "成功", "プロジェクトを更新しました")
            else:
                show_error_message(self, "エラー", "プロジェクトの更新に失敗しました")
    
    def delete_current_project(self):
        """現在のプロジェクトを削除"""
        project_data = self.controller.get_current_project()
        
        if not project_data:
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        if show_confirm_dialog(self, "確認", f"プロジェクト「{project_data['name']}」を削除してもよろしいですか？\nこの操作は元に戻せません。"):
            success = self.controller.delete_project(project_data["id"])
            
            if success:
                show_info_message(self, "成功", "プロジェクトを削除しました")
                self.tab_widget.setCurrentIndex(0)  # プロジェクト一覧タブに切り替え
                self.load_projects()
                
                # 自動保存タイマーを停止
                self.save_timer.stop()
            else:
                show_error_message(self, "エラー", "プロジェクトの削除に失敗しました")
    
    def save_current_project(self):
        """現在のプロジェクトを保存"""
        if not self.controller.get_current_project():
            return
        
        success = self.controller.manager.save_current_project()
        
        if success:
            self.statusBar().showMessage("プロジェクトを保存しました", 3000)
        else:
            show_error_message(self, "エラー", "プロジェクトの保存に失敗しました")
    
    def set_project_on_hold(self):
        """プロジェクトを保留状態に設定"""
        if not self.controller.get_current_project():
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        if self.controller.set_project_on_hold():
            show_info_message(self, "成功", "プロジェクトを保留状態に設定しました")
        else:
            show_error_message(self, "エラー", "プロジェクトの状態更新に失敗しました")

    def set_project_cancelled(self):
        """プロジェクトを中止状態に設定"""
        if not self.controller.get_current_project():
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        if show_confirm_dialog(self, "確認", "このプロジェクトを中止してもよろしいですか？"):
            if self.controller.set_project_cancelled():
                show_info_message(self, "成功", "プロジェクトを中止状態に設定しました")
            else:
                show_error_message(self, "エラー", "プロジェクトの状態更新に失敗しました")

    def release_project_status(self):
        """プロジェクトの手動設定状態を解除"""
        if not self.controller.get_current_project():
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        if self.controller.release_project_status():
            show_info_message(self, "成功", "プロジェクトの状態を自動判定に戻しました")
        else:
            show_error_message(self, "エラー", "プロジェクトの状態更新に失敗しました")

    def auto_save_project(self):
        """自動保存処理"""
        self.save_current_project()
    
    def create_new_phase(self):
        """新しいフェーズを作成"""
        if not self.controller.get_current_project():
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        dialog = PhaseDialog(self)
        if dialog.exec():
            phase_data = dialog.get_phase_data()
            
            if not phase_data["name"]:
                show_error_message(self, "エラー", "フェーズ名を入力してください")
                return
            
            success = self.controller.create_phase(
                phase_data["name"],
                phase_data["description"]
            )
            
            if success:
                show_info_message(self, "成功", f"フェーズ「{phase_data['name']}」を作成しました")
            else:
                show_error_message(self, "エラー", "フェーズの作成に失敗しました")
    
    def create_new_process(self):
        """新しいプロセスを作成"""
        if not self.controller.get_current_project():
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        # 現在選択されているフェーズを特定
        current_item = self.get_selected_tree_item()
        phase_id = None
        
        if current_item:
            item_type, item_id = self.get_item_type_and_id(current_item)
            
            if item_type == "phase":
                phase_id = item_id
            elif item_type == "process":
                # プロセスが選択されている場合は親のフェーズを取得
                phase_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            elif item_type == "task":
                # タスクが選択されている場合は祖父のフェーズを取得
                phase_id = current_item.parent().parent().data(0, Qt.ItemDataRole.UserRole)
        
        if not phase_id:
            # フェーズが選択されていない場合、フェーズ選択ダイアログを表示
            phases = self.controller.get_phases()
            if not phases:
                show_error_message(self, "エラー", "フェーズが存在しません。先にフェーズを作成してください。")
                return
            
            # フェーズ選択ダイアログ
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("フェーズ選択")
            layout = QVBoxLayout(dialog)
            
            label = QLabel("プロセスを追加するフェーズを選択してください:")
            layout.addWidget(label)
            
            combo = QComboBox()
            for phase in phases:
                combo.addItem(phase["name"], phase["id"])
            layout.addWidget(combo)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec():
                phase_id = combo.currentData()
            else:
                return
        
        # プロセス作成ダイアログ
        dialog = ProcessDialog(self)
        if dialog.exec():
            process_data = dialog.get_process_data()
            
            if not process_data["name"]:
                show_error_message(self, "エラー", "プロセス名を入力してください")
                return
            
            success = self.controller.create_process(
                phase_id,
                process_data["name"],
                process_data["description"],
                process_data["assignee"]
            )
            
            if success:
                show_info_message(self, "成功", f"プロセス「{process_data['name']}」を作成しました")
                # 選択中のフェーズを開いた状態にする
                self.controller.set_current_phase(phase_id)
            else:
                show_error_message(self, "エラー", "プロセスの作成に失敗しました")
    
    def create_new_task(self):
        """新しいタスクを作成"""
        if not self.controller.get_current_project():
            show_error_message(self, "エラー", "プロジェクトが読み込まれていません")
            return
        
        # 現在選択されているプロセスを特定
        current_item = self.get_selected_tree_item()
        phase_id = None
        process_id = None
        
        if current_item:
            item_type, item_id = self.get_item_type_and_id(current_item)
            
            if item_type == "process":
                process_id = item_id
                phase_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            elif item_type == "task":
                # タスクが選択されている場合は親のプロセスと祖父のフェーズを取得
                process_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
                phase_id = current_item.parent().parent().data(0, Qt.ItemDataRole.UserRole)
        
        if not process_id or not phase_id:
            # プロセスが選択されていない場合、プロセス選択ダイアログを表示
            phases = self.controller.get_phases()
            if not phases:
                show_error_message(self, "エラー", "フェーズが存在しません。先にフェーズを作成してください。")
                return
            
            # フェーズとプロセスの選択ダイアログ
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("プロセス選択")
            layout = QVBoxLayout(dialog)
            
            # フェーズ選択
            phase_label = QLabel("フェーズを選択:")
            layout.addWidget(phase_label)
            
            phase_combo = QComboBox()
            for phase in phases:
                phase_combo.addItem(phase["name"], phase["id"])
            layout.addWidget(phase_combo)
            
            # プロセス選択（フェーズに依存）
            process_label = QLabel("プロセスを選択:")
            layout.addWidget(process_label)
            
            process_combo = QComboBox()
            layout.addWidget(process_combo)
            
            # フェーズ変更時にプロセスリストを更新
            def update_processes():
                process_combo.clear()
                selected_phase_id = phase_combo.currentData()
                processes = self.controller.get_processes(selected_phase_id)
                for process in processes:
                    process_combo.addItem(process["name"], process["id"])
            
            phase_combo.currentIndexChanged.connect(update_processes)
            update_processes()  # 初期化
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec():
                phase_id = phase_combo.currentData()
                process_id = process_combo.currentData()
                if not process_id:
                    show_error_message(self, "エラー", "選択したフェーズにプロセスが存在しません。先にプロセスを作成してください。")
                    return
            else:
                return
        
        # タスク作成ダイアログ
        dialog = TaskDialog(self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            
            if not task_data["name"]:
                show_error_message(self, "エラー", "タスク名を入力してください")
                return
            
            success = self.controller.create_task(
                phase_id,
                process_id,
                task_data["name"],
                task_data["description"],
                task_data["status"]
            )
            
            if success:
                show_info_message(self, "成功", f"タスク「{task_data['name']}」を作成しました")
                # 選択中のプロセスを開いた状態にする
                self.controller.set_current_process(phase_id, process_id)
            else:
                show_error_message(self, "エラー", "タスクの作成に失敗しました")
    
    def edit_selected_item(self):
        """選択されたアイテムを編集"""
        current_item = self.get_selected_tree_item()
        if not current_item:
            return
        
        item_type, item_id = self.get_item_type_and_id(current_item)
        
        if item_type == "phase":
            self.edit_phase(item_id)
        elif item_type == "process":
            phase_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            self.edit_process(phase_id, item_id)
        elif item_type == "task":
            process_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            phase_id = current_item.parent().parent().data(0, Qt.ItemDataRole.UserRole)
            self.edit_task(phase_id, process_id, item_id)
    
    def delete_selected_item(self):
        """選択されたアイテムを削除"""
        current_item = self.get_selected_tree_item()
        if not current_item:
            return
        
        item_type, item_id = self.get_item_type_and_id(current_item)
        
        if item_type == "phase":
            self.delete_phase(item_id)
        elif item_type == "process":
            phase_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            self.delete_process(phase_id, item_id)
        elif item_type == "task":
            process_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            phase_id = current_item.parent().parent().data(0, Qt.ItemDataRole.UserRole)
            self.delete_task(phase_id, process_id, item_id)
    
    def add_child_to_selected(self):
        """選択されたアイテムに子要素を追加"""
        current_item = self.get_selected_tree_item()
        if not current_item:
            return
        
        item_type, item_id = self.get_item_type_and_id(current_item)
        
        if item_type == "phase":
            # フェーズにプロセスを追加
            self.create_new_process()
        elif item_type == "process":
            # プロセスにタスクを追加
            phase_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            process_id = item_id
            
            dialog = TaskDialog(self)
            if dialog.exec():
                task_data = dialog.get_task_data()
                
                if not task_data["name"]:
                    show_error_message(self, "エラー", "タスク名を入力してください")
                    return
                
                success = self.controller.create_task(
                    phase_id,
                    process_id,
                    task_data["name"],
                    task_data["description"],
                    task_data["status"]
                )
                
                if success:
                    show_info_message(self, "成功", f"タスク「{task_data['name']}」を作成しました")
                    self.controller.set_current_process(phase_id, process_id)
                else:
                    show_error_message(self, "エラー", "タスクの作成に失敗しました")
    
    def edit_phase(self, phase_id: str):
        """
        フェーズを編集
        
        Args:
            phase_id: 編集するフェーズのID
        """
        phase_data = self.controller.get_phase_details(phase_id)
        if not phase_data:
            return
        
        dialog = PhaseDialog(self, phase_data)
        if dialog.exec():
            updated_data = dialog.get_phase_data()
            
            if not updated_data["name"]:
                show_error_message(self, "エラー", "フェーズ名を入力してください")
                return
            
            success = self.controller.update_phase(
                phase_id,
                updated_data["name"],
                updated_data["description"],
                updated_data.get("end_date")
            )
            
            if success:
                show_info_message(self, "成功", "フェーズを更新しました")
            else:
                show_error_message(self, "エラー", "フェーズの更新に失敗しました")
    
    def delete_phase(self, phase_id: str):
        """
        フェーズを削除
        
        Args:
            phase_id: 削除するフェーズのID
        """
        phase_data = self.controller.get_phase_details(phase_id)
        if not phase_data:
            return
        
        if show_confirm_dialog(self, "確認", f"フェーズ「{phase_data['name']}」とその中のすべてのプロセス、タスクを削除してもよろしいですか？\nこの操作は元に戻せません。"):
            success = self.controller.delete_phase(phase_id)
            
            if success:
                show_info_message(self, "成功", "フェーズを削除しました")
            else:
                show_error_message(self, "エラー", "フェーズの削除に失敗しました")
    
    def edit_process(self, phase_id: str, process_id: str):
        """
        プロセスを編集
        
        Args:
            phase_id: フェーズID
            process_id: 編集するプロセスのID
        """
        process_data = self.controller.get_process_details(phase_id, process_id)
        if not process_data:
            return
        
        dialog = ProcessDialog(self, process_data)
        if dialog.exec():
            updated_data = dialog.get_process_data()
            
            if not updated_data["name"]:
                show_error_message(self, "エラー", "プロセス名を入力してください")
                return
            
            success = self.controller.update_process(
                phase_id,
                process_id,
                updated_data["name"],
                updated_data["description"],
                updated_data["assignee"],
                updated_data.get("start_date"),
                updated_data.get("end_date"),
                updated_data.get("estimated_hours"),
                updated_data.get("actual_hours")
            )
            
            if success:
                show_info_message(self, "成功", "プロセスを更新しました")
            else:
                show_error_message(self, "エラー", "プロセスの更新に失敗しました")
    
    def delete_process(self, phase_id: str, process_id: str):
        """
        プロセスを削除
        
        Args:
            phase_id: フェーズID
            process_id: 削除するプロセスのID
        """
        process_data = self.controller.get_process_details(phase_id, process_id)
        if not process_data:
            return
        
        if show_confirm_dialog(self, "確認", f"プロセス「{process_data['name']}」とその中のすべてのタスクを削除してもよろしいですか？\nこの操作は元に戻せません。"):
            success = self.controller.delete_process(phase_id, process_id)
            
            if success:
                show_info_message(self, "成功", "プロセスを削除しました")
            else:
                show_error_message(self, "エラー", "プロセスの削除に失敗しました")
    
    def edit_task(self, phase_id: str, process_id: str, task_id: str):
        """
        タスクを編集
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            task_id: 編集するタスクのID
        """
        task_data = self.controller.get_task_details(phase_id, process_id, task_id)
        if not task_data:
            return
        
        dialog = TaskDialog(self, task_data)
        if dialog.exec():
            updated_data = dialog.get_task_data()
            
            if not updated_data["name"]:
                show_error_message(self, "エラー", "タスク名を入力してください")
                return
            
            success = self.controller.update_task(
                phase_id,
                process_id,
                task_id,
                updated_data["name"],
                updated_data["description"],
                updated_data["status"]
            )
            
            if success:
                show_info_message(self, "成功", "タスクを更新しました")
            else:
                show_error_message(self, "エラー", "タスクの更新に失敗しました")
    
    def delete_task(self, phase_id: str, process_id: str, task_id: str):
        """
        タスクを削除
        
        Args:
            phase_id: フェーズID
            process_id: プロセスID
            task_id: 削除するタスクのID
        """
        task_data = self.controller.get_task_details(phase_id, process_id, task_id)
        if not task_data:
            return
        
        if show_confirm_dialog(self, "確認", f"タスク「{task_data['name']}」を削除してもよろしいですか？\nこの操作は元に戻せません。"):
            success = self.controller.delete_task(phase_id, process_id, task_id)
            
            if success:
                show_info_message(self, "成功", "タスクを削除しました")
            else:
                show_error_message(self, "エラー", "タスクの削除に失敗しました")
    
    def refresh_project_view(self):
        """プロジェクト詳細ビューを更新"""
        project_data = self.controller.get_current_project()
        
        if not project_data:
            self.project_header.setText("プロジェクトが選択されていません")
            self.project_basic_info.setText("")
            self.project_progress_info.setText("")
            self.on_hold_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.release_button.setEnabled(False)
            return
        
        # プロジェクトヘッダー更新
        self.project_header.setText(project_data["name"])
        
        # ボタン有効化
        self.on_hold_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.release_button.setEnabled(True)
        
        # 手動設定状態の場合は視覚的に示す
        is_manual = project_data.get("is_status_manual", False)
        status_text = project_data["status"]
        if is_manual:
            status_text += " (手動設定)"
        
        # 基本情報更新
        basic_info = f"""
        <p><b>ID:</b> {project_data['id']}</p>
        <p><b>説明:</b> {project_data['description']}</p>
        <p><b>状態:</b> <span style="color: {get_status_color(project_data['status'])}">{status_text}</span></p>
        <p><b>作成日時:</b> {project_data['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
        <p><b>更新日時:</b> {project_data['updated_at'].strftime('%Y-%m-%d %H:%M')}</p>
        """
        self.project_basic_info.setText(basic_info)
        
        # 進捗情報更新
        progress_info = f"""
        <p><b>進捗率:</b> {format_progress(project_data['progress'])}</p>
        <p><b>開始日:</b> {format_date(project_data['start_date'])}</p>
        <p><b>終了日:</b> {format_date(project_data['end_date'])}</p>
        """
        self.project_progress_info.setText(progress_info)
    
    def refresh_phases_view(self):
        """フェーズツリーを更新"""
        project_data = self.controller.get_current_project()
        
        if not project_data:
            self.phases_tree.clear()
            return
        
        # 現在の展開状態を記憶
        expanded_items = {}
        current_root = self.phases_tree.invisibleRootItem()
        for i in range(current_root.childCount()):
            phase_item = current_root.child(i)
            phase_id = phase_item.data(0, Qt.ItemDataRole.UserRole)
            expanded_items[phase_id] = phase_item.isExpanded()
            
            for j in range(phase_item.childCount()):
                process_item = phase_item.child(j)
                process_id = process_item.data(0, Qt.ItemDataRole.UserRole)
                expanded_items[process_id] = process_item.isExpanded()
        
        # ツリーをクリア
        self.phases_tree.clear()
        
        # フェーズデータ取得
        phases = self.controller.get_phases()
        
        # フェーズをツリーに追加
        for phase in phases:
            phase_item = QTreeWidgetItem(self.phases_tree)
            phase_item.setText(0, phase["name"])
            phase_item.setText(1, format_progress(phase["progress"]))
            phase_item.setText(2, "")  # フェーズには担当者がない
            phase_item.setText(3, "")  # フェーズには状態がない
            phase_item.setData(0, Qt.ItemDataRole.UserRole, phase["id"])
            phase_item.setData(0, Qt.ItemDataRole.UserRole + 1, "phase")
            
            # 保存した展開状態を復元
            if phase["id"] in expanded_items:
                phase_item.setExpanded(expanded_items[phase["id"]])
            
            # プロセスデータ取得
            processes = self.controller.get_processes(phase["id"])
            
            # プロセスをツリーに追加
            for process in processes:
                process_item = QTreeWidgetItem(phase_item)
                process_item.setText(0, process["name"])
                process_item.setText(1, format_progress(process["progress"]))
                process_item.setText(2, process["assignee"] or "未割当")
                process_item.setText(3, "")  # プロセスには状態がない
                process_item.setData(0, Qt.ItemDataRole.UserRole, process["id"])
                process_item.setData(0, Qt.ItemDataRole.UserRole + 1, "process")
                
                # 保存した展開状態を復元
                if process["id"] in expanded_items:
                    process_item.setExpanded(expanded_items[process["id"]])
                
                # タスクデータ取得
                tasks = self.controller.get_tasks(phase["id"], process["id"])
                
                # タスクをツリーに追加
                for task in tasks:
                    task_item = QTreeWidgetItem(process_item)
                    task_item.setText(0, task["name"])
                    task_item.setText(1, "")  # タスクには進捗率がない
                    task_item.setText(2, "")  # タスクには担当者がない
                    
                    # 状態に応じた色を設定
                    task_item.setText(3, task["status"])
                    task_item.setForeground(3, QColor(get_status_color(task["status"])))
                    
                    task_item.setData(0, Qt.ItemDataRole.UserRole, task["id"])
                    task_item.setData(0, Qt.ItemDataRole.UserRole + 1, "task")
    
    def refresh_processes_view(self, phase_id: str):
        """
        指定したフェーズのプロセスビューを更新
        
        Args:
            phase_id: 更新するフェーズのID
        """
        # フェーズを探してプロセスを更新
        root = self.phases_tree.invisibleRootItem()
        for i in range(root.childCount()):
            phase_item = root.child(i)
            current_phase_id = phase_item.data(0, Qt.ItemDataRole.UserRole)
            
            if current_phase_id == phase_id:
                # 展開状態を保持
                expanded_state = {}
                for j in range(phase_item.childCount()):
                    process_item = phase_item.child(j)
                    process_id = process_item.data(0, Qt.ItemDataRole.UserRole)
                    expanded_state[process_id] = process_item.isExpanded()
                
                # 子アイテムをクリア
                while phase_item.childCount() > 0:
                    phase_item.removeChild(phase_item.child(0))
                
                # プロセスを再取得
                processes = self.controller.get_processes(phase_id)
                
                # プロセスをツリーに追加
                for process in processes:
                    process_item = QTreeWidgetItem(phase_item)
                    process_item.setText(0, process["name"])
                    process_item.setText(1, format_progress(process["progress"]))
                    process_item.setText(2, process["assignee"] or "未割当")
                    process_item.setText(3, "")
                    process_item.setData(0, Qt.ItemDataRole.UserRole, process["id"])
                    process_item.setData(0, Qt.ItemDataRole.UserRole + 1, "process")
                    
                    # 以前の展開状態を復元
                    if process["id"] in expanded_state:
                        process_item.setExpanded(expanded_state[process["id"]])
                    
                    # タスクを取得して追加
                    tasks = self.controller.get_tasks(phase_id, process["id"])
                    
                    for task in tasks:
                        task_item = QTreeWidgetItem(process_item)
                        task_item.setText(0, task["name"])
                        task_item.setText(1, "")
                        task_item.setText(2, "")
                        
                        # 状態に応じた色を設定
                        task_item.setText(3, task["status"])
                        task_item.setForeground(3, QColor(get_status_color(task["status"])))
                        
                        task_item.setData(0, Qt.ItemDataRole.UserRole, task["id"])
                        task_item.setData(0, Qt.ItemDataRole.UserRole + 1, "task")
                
                # フェーズの情報も更新
                phase_data = self.controller.get_phase_details(phase_id)
                if phase_data:
                    phase_item.setText(0, phase_data["name"])
                    phase_item.setText(1, format_progress(phase_data["progress"]))
                
                break
    
    def refresh_tasks_view(self, phase_id: str, process_id: str):
        """
        指定したプロセスのタスクビューを更新
        
        Args:
            phase_id: フェーズID
            process_id: 更新するプロセスのID
        """
        # タスク一覧を更新（テーブルとツリー両方）
        tasks = self.controller.get_tasks(phase_id, process_id)
        
        # タスクテーブルを更新
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # ID
            id_item = QTableWidgetItem(task["id"][:8] + "...")
            id_item.setData(Qt.ItemDataRole.UserRole, task["id"])
            self.tasks_table.setItem(row, 0, id_item)
            
            # 名前
            self.tasks_table.setItem(row, 1, QTableWidgetItem(task["name"]))
            
            # 状態
            status_item = QTableWidgetItem(task["status"])
            status_item.setForeground(QColor(get_status_color(task["status"])))
            self.tasks_table.setItem(row, 2, status_item)
            
            # 更新日時
            update_time = datetime.fromisoformat(task["updated_at"])
            self.tasks_table.setItem(row, 3, QTableWidgetItem(update_time.strftime("%Y-%m-%d %H:%M")))
            
            # 操作ボタン
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            # 編集ボタン
            edit_button = QPushButton("編集")
            edit_button.clicked.connect(lambda checked, p=phase_id, pr=process_id, t=task["id"]: 
                                        self.edit_task(p, pr, t))
            button_layout.addWidget(edit_button)
            
            # 削除ボタン
            delete_button = QPushButton("削除")
            delete_button.clicked.connect(lambda checked, p=phase_id, pr=process_id, t=task["id"]: 
                                         self.delete_task(p, pr, t))
            button_layout.addWidget(delete_button)
            
            button_layout.setStretch(0, 1)
            button_layout.setStretch(1, 1)
            
            self.tasks_table.setCellWidget(row, 4, button_widget)
        
        # ツリー内のプロセスを探してタスクを更新
        root = self.phases_tree.invisibleRootItem()
        for i in range(root.childCount()):
            phase_item = root.child(i)
            current_phase_id = phase_item.data(0, Qt.ItemDataRole.UserRole)
            
            if current_phase_id == phase_id:
                for j in range(phase_item.childCount()):
                    process_item = phase_item.child(j)
                    current_process_id = process_item.data(0, Qt.ItemDataRole.UserRole)
                    
                    if current_process_id == process_id:
                        # プロセスの情報を更新
                        process_data = self.controller.get_process_details(phase_id, process_id)
                        if process_data:
                            process_item.setText(0, process_data["name"])
                            process_item.setText(1, format_progress(process_data["progress"]))
                            process_item.setText(2, process_data["assignee"] or "未割当")
                        
                        # 子アイテムをクリア
                        while process_item.childCount() > 0:
                            process_item.removeChild(process_item.child(0))
                        
                        # タスクを追加
                        for task in tasks:
                            task_item = QTreeWidgetItem(process_item)
                            task_item.setText(0, task["name"])
                            task_item.setText(1, "")
                            task_item.setText(2, "")
                            
                            # 状態に応じた色を設定
                            task_item.setText(3, task["status"])
                            task_item.setForeground(3, QColor(get_status_color(task["status"])))
                            
                            task_item.setData(0, Qt.ItemDataRole.UserRole, task["id"])
                            task_item.setData(0, Qt.ItemDataRole.UserRole + 1, "task")
                        
                        break
                break
    
    def refresh_all_processes(self):
        """全プロセス一覧を更新"""
        # 担当者フィルターを更新
        self.update_assignee_filter()
        
        # プロセスデータを取得
        processes = self.controller.get_all_processes()
        
        # フィルタリングを適用
        self.filtered_processes = self.filter_processes(processes)
        
        # テーブルを更新
        self.populate_processes_table()

    def update_assignee_filter(self):
        """担当者フィルターの選択肢を更新"""
        current_assignee = self.assignee_filter.currentData()
        
        self.assignee_filter.clear()
        self.assignee_filter.addItem("すべての担当者", None)
        
        assignees = set()
        processes = self.controller.get_all_processes()
        
        for process in processes:
            if process.get("assignee"):
                assignees.add(process["assignee"])
        
        for assignee in sorted(assignees):
            self.assignee_filter.addItem(assignee, assignee)
        
        # 以前の選択を復元
        if current_assignee:
            index = self.assignee_filter.findData(current_assignee)
            if index >= 0:
                self.assignee_filter.setCurrentIndex(index)

    def filter_processes(self, processes):
        """プロセスをフィルタリング"""
        filtered = processes
        
        # 担当者でフィルター
        assignee = self.assignee_filter.currentData()
        if assignee:
            filtered = [p for p in filtered if p.get("assignee") == assignee]
        
        # 状態でフィルター
        status = self.status_filter.currentData()
        if status:
            filtered = [p for p in filtered if p.get("status") == status]
        
        # 期限でフィルター
        deadline_days = self.deadline_filter.currentData()
        if deadline_days is not None and deadline_days != 0:
            if deadline_days < 0:
                # 期限切れ
                filtered = [p for p in filtered if p.get("days_remaining") is not None and p.get("days_remaining") < 0]
            else:
                # X日以内
                filtered = [p for p in filtered if p.get("days_remaining") is not None and 0 <= p.get("days_remaining") <= deadline_days]
        
        return filtered

    def apply_process_filters(self):
        """フィルターを適用してプロセス一覧を更新"""
        processes = self.controller.get_all_processes()
        self.filtered_processes = self.filter_processes(processes)
        self.populate_processes_table()

    def populate_processes_table(self):
        """プロセステーブルにデータを設定"""
        self.processes_table.setRowCount(len(self.filtered_processes))
        
        for row, process in enumerate(self.filtered_processes):
            # プロジェクト
            self.processes_table.setItem(row, 0, QTableWidgetItem(process["project_name"]))
            
            # フェーズ
            self.processes_table.setItem(row, 1, QTableWidgetItem(process["phase_name"]))
            
            # プロセス名
            self.processes_table.setItem(row, 2, QTableWidgetItem(process["name"]))
            
            # 担当者
            self.processes_table.setItem(row, 3, QTableWidgetItem(process.get("assignee", "")))
            
            # 進捗率
            progress_item = QTableWidgetItem(format_progress(process["progress"]))
            self.processes_table.setItem(row, 4, progress_item)
            
            # 開始日
            start_date = process.get("start_date")
            self.processes_table.setItem(row, 5, QTableWidgetItem(format_date(start_date)))
            
            # 終了日
            end_date = process.get("end_date")
            self.processes_table.setItem(row, 6, QTableWidgetItem(format_date(end_date)))
            
            # 残り日数
            days_remaining = process.get("days_remaining")
            days_item = QTableWidgetItem(str(days_remaining) if days_remaining is not None else "未設定")
            
            # 期限切れは赤、1週間以内は黄色で表示
            if days_remaining is not None:
                if days_remaining < 0:
                    days_item.setForeground(QColor(ColorScheme.OVERDUE))
                elif days_remaining <= 7:
                    days_item.setForeground(QColor(ColorScheme.WARNING))
                else:
                    days_item.setForeground(QColor(ColorScheme.NORMAL))
                    
            self.processes_table.setItem(row, 7, days_item)
            
            # 操作ボタン
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            
            # 詳細ボタン
            view_button = QPushButton("詳細")
            view_button.clicked.connect(lambda checked, p=process: self.view_process_detail(p))
            button_layout.addWidget(view_button)
            
            # 編集ボタン
            edit_button = QPushButton("編集")
            edit_button.clicked.connect(lambda checked, p=process: self.edit_process_from_list(p))
            button_layout.addWidget(edit_button)
            
            button_layout.setStretch(0, 1)
            button_layout.setStretch(1, 1)
            
            self.processes_table.setCellWidget(row, 8, button_widget)

    def view_process_detail(self, process):
        """プロセスの詳細ページを表示"""
        project_id = process["project_id"]
        phase_id = process["phase_id"]
        process_id = process["id"]
        
        # プロジェクトを読み込む
        self.controller.load_project(project_id)
        
        # プロジェクト詳細タブに切り替え
        self.tab_widget.setCurrentIndex(1)
        
        # フェーズとプロセスを選択
        self.controller.set_current_phase(phase_id)
        self.controller.set_current_process(phase_id, process_id)
        
        # ツリービューでプロセスを選択
        self.select_process_in_tree(phase_id, process_id)

    def edit_process_from_list(self, process):
        """プロセス一覧からプロセスを編集"""
        project_id = process["project_id"]
        phase_id = process["phase_id"]
        process_id = process["id"]
        
        # プロジェクトを読み込む（一時的に）
        current_project_id = None
        if self.controller.manager.current_project:
            current_project_id = self.controller.manager.current_project.id
        
        self.controller.load_project(project_id)
        
        # プロセス編集ダイアログを表示
        self.edit_process(phase_id, process_id)
        
        # 元のプロジェクトに戻す（必要な場合）
        if current_project_id and current_project_id != project_id:
            self.controller.load_project(current_project_id)
        
        # プロセス一覧を更新
        self.refresh_all_processes()

    def select_process_in_tree(self, phase_id, process_id):
        """ツリービューでプロセスを選択"""
        root = self.phases_tree.invisibleRootItem()
        
        # フェーズを検索
        for i in range(root.childCount()):
            phase_item = root.child(i)
            if phase_item.data(0, Qt.ItemDataRole.UserRole) == phase_id:
                
                # フェーズを展開
                phase_item.setExpanded(True)
                
                # プロセスを検索
                for j in range(phase_item.childCount()):
                    process_item = phase_item.child(j)
                    if process_item.data(0, Qt.ItemDataRole.UserRole) == process_id:
                        
                        # プロセスを選択
                        self.phases_tree.setCurrentItem(process_item)
                        return

    def on_tab_changed(self, index: int):
        """タブ切り替え時の処理"""
        if index == 0:  # プロジェクト一覧タブ
            self.load_projects()
        elif index == 1:  # プロジェクト詳細タブ
            self.refresh_project_view()
            self.refresh_phases_view()
        elif index == 2:  # ガントチャートタブ
            if hasattr(self, 'gantt_chart_tab'):
                self.gantt_chart_tab.refresh_gantt_chart()
        elif index == 3:  # 全プロセスタブ
            self.refresh_all_processes()
        elif index == 4:  # エラーログタブ
            if hasattr(self, 'error_log_tab'):
                self.error_log_tab.load_error_logs()
        elif index == 5:  # 通知タブ
            if hasattr(self, 'notification_tab'):
                self.notification_tab.load_notifications()

    
    def on_project_double_clicked(self, row: int, col: int):
        """プロジェクト一覧のダブルクリック処理"""
        id_item = self.projects_table.item(row, 0)
        if id_item:
            project_id = id_item.data(Qt.ItemDataRole.UserRole)
            self.open_project(project_id)
    
    def on_tree_selection_changed(self):
        """ツリーの選択変更時の処理"""
        current_item = self.get_selected_tree_item()
        
        if not current_item:
            self.edit_detail_button.setEnabled(False)
            self.delete_detail_button.setEnabled(False)
            self.add_child_button.setEnabled(False)
            self.tasks_table.setVisible(False)
            self.detail_header.setText("詳細情報")
            self.detail_content.setText("項目を選択してください")
            return
        
        item_type, item_id = self.get_item_type_and_id(current_item)
        
        # 詳細情報の表示
        if item_type == "phase":
            # フェーズの詳細表示
            phase_data = self.controller.get_phase_details(item_id)
            if phase_data:
                self.detail_header.setText(f"フェーズ: {phase_data['name']}")
                
                detail_text = f"""
                <p><b>ID:</b> {phase_data['id']}</p>
                <p><b>説明:</b> {phase_data['description']}</p>
                <p><b>進捗率:</b> {format_progress(phase_data['progress'])}</p>
                <p><b>開始日:</b> {format_date(phase_data['start_date'])}</p>
                <p><b>終了日:</b> {format_date(phase_data['end_date'])}</p>
                <p><b>作成日時:</b> {phase_data['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                <p><b>更新日時:</b> {phase_data['updated_at'].strftime('%Y-%m-%d %H:%M')}</p>
                """
                
                self.detail_content.setText(detail_text)
                self.tasks_table.setVisible(False)
            
            # ボタンの有効化
            self.edit_detail_button.setEnabled(True)
            self.delete_detail_button.setEnabled(True)
            self.add_child_button.setEnabled(True)
            self.add_child_button.setText("プロセス追加")
            
        elif item_type == "process":
            # プロセスの詳細表示
            phase_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            process_data = self.controller.get_process_details(phase_id, item_id)
            
            if process_data:
                self.detail_header.setText(f"プロセス: {process_data['name']}")
                
                detail_text = f"""
                <p><b>ID:</b> {process_data['id']}</p>
                <p><b>説明:</b> {process_data['description']}</p>
                <p><b>担当者:</b> {process_data['assignee'] or '未割当'}</p>
                <p><b>進捗率:</b> {format_progress(process_data['progress'])}</p>
                <p><b>開始日:</b> {format_date(process_data['start_date'])}</p>
                <p><b>終了日:</b> {format_date(process_data['end_date'])}</p>
                <p><b>予想工数:</b> {format_hours(process_data['estimated_hours'])}</p>
                <p><b>実工数:</b> {format_hours(process_data['actual_hours'])}</p>
                <p><b>作成日時:</b> {process_data['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                <p><b>更新日時:</b> {process_data['updated_at'].strftime('%Y-%m-%d %H:%M')}</p>
                """
                
                self.detail_content.setText(detail_text)
                
                # タスク一覧を表示
                self.tasks_table.setVisible(True)
                self.controller.set_current_process(phase_id, item_id)
            
            # ボタンの有効化
            self.edit_detail_button.setEnabled(True)
            self.delete_detail_button.setEnabled(True)
            self.add_child_button.setEnabled(True)
            self.add_child_button.setText("タスク追加")
            
        elif item_type == "task":
            # タスクの詳細表示
            process_id = current_item.parent().data(0, Qt.ItemDataRole.UserRole)
            phase_id = current_item.parent().parent().data(0, Qt.ItemDataRole.UserRole)
            task_data = self.controller.get_task_details(phase_id, process_id, item_id)
            
            if task_data:
                self.detail_header.setText(f"タスク: {task_data['name']}")
                
                detail_text = f"""
                <p><b>ID:</b> {task_data['id']}</p>
                <p><b>説明:</b> {task_data['description']}</p>
                <p><b>状態:</b> <span style="color: {get_status_color(task_data['status'])}">{task_data['status']}</span></p>
                <p><b>作成日時:</b> {task_data['created_at'].strftime('%Y-%m-%d %H:%M')}</p>
                <p><b>更新日時:</b> {task_data['updated_at'].strftime('%Y-%m-%d %H:%M')}</p>
                """
                
                # タスク履歴を追加
                history = self.controller.get_task_history(item_id)
                if history:
                    detail_text += "<p><b>履歴:</b></p><ul>"
                    for entry in history:
                        timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                        action = entry["action_type"]
                        
                        history_item = f"<li>{timestamp} - {action}"
                        
                        if "details" in entry and "status" in entry["details"]:
                            status_change = entry["details"]["status"]
                            if isinstance(status_change, dict) and 'old' in status_change and 'new' in status_change:
                                # 辞書型の場合（想定していた形式）
                                history_item += f" (状態変更: {status_change['old']} → {status_change['new']})"
                            else:
                                # 文字列型の場合
                                history_item += f" (状態変更: {status_change})"
                                
                        history_item += "</li>"
                        detail_text += history_item
                    
                    detail_text += "</ul>"
                
                self.detail_content.setText(detail_text)
                self.tasks_table.setVisible(False)
            
            # ボタンの有効化
            self.edit_detail_button.setEnabled(True)
            self.delete_detail_button.setEnabled(True)
            self.add_child_button.setEnabled(False)
    
    def get_selected_tree_item(self) -> Optional[QTreeWidgetItem]:
        """
        現在選択されているツリーアイテムを取得
        
        Returns:
            選択されているQTreeWidgetItem、または None
        """
        selected_items = self.phases_tree.selectedItems()
        if not selected_items:
            return None
        return selected_items[0]
    
    def get_item_type_and_id(self, item: QTreeWidgetItem) -> tuple:
        """
        ツリーアイテムのタイプとIDを取得
        
        Args:
            item: QTreeWidgetItem
            
        Returns:
            (item_type, item_id)のタプル
        """
        item_id = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        return item_type, item_id
    
    def show_tree_context_menu(self, pos):
        """
        ツリービューのコンテキストメニューを表示
        
        Args:
            pos: メニュー表示位置
        """
        item = self.phases_tree.itemAt(pos)
        if not item:
            return
        
        item_type, item_id = self.get_item_type_and_id(item)
        
        # コンテキストメニュー作成
        menu = QMenu(self)
        
        if item_type == "phase":
            # フェーズ用メニュー
            edit_action = menu.addAction("フェーズを編集")
            edit_action.triggered.connect(lambda: self.edit_phase(item_id))
            
            delete_action = menu.addAction("フェーズを削除")
            delete_action.triggered.connect(lambda: self.delete_phase(item_id))
            
            menu.addSeparator()
            
            add_process_action = menu.addAction("プロセスを追加")
            add_process_action.triggered.connect(self.create_new_process)
            
        elif item_type == "process":
            # プロセス用メニュー
            phase_id = item.parent().data(0, Qt.ItemDataRole.UserRole)
            
            edit_action = menu.addAction("プロセスを編集")
            edit_action.triggered.connect(lambda: self.edit_process(phase_id, item_id))
            
            delete_action = menu.addAction("プロセスを削除")
            delete_action.triggered.connect(lambda: self.delete_process(phase_id, item_id))
            
            menu.addSeparator()
            
            add_task_action = menu.addAction("タスクを追加")
            add_task_action.triggered.connect(lambda: self.add_child_to_selected())
            
        elif item_type == "task":
            # タスク用メニュー
            process_id = item.parent().data(0, Qt.ItemDataRole.UserRole)
            phase_id = item.parent().parent().data(0, Qt.ItemDataRole.UserRole)
            
            edit_action = menu.addAction("タスクを編集")
            edit_action.triggered.connect(lambda: self.edit_task(phase_id, process_id, item_id))
            
            delete_action = menu.addAction("タスクを削除")
            delete_action.triggered.connect(lambda: self.delete_task(phase_id, process_id, item_id))
            
            menu.addSeparator()
            
            # 状態変更サブメニュー
            status_menu = menu.addMenu("状態を変更")
            
            for status in TaskStatus:
                status_action = status_menu.addAction(status.value)
                status_action.triggered.connect(
                    lambda checked, p=phase_id, pr=process_id, t=item_id, s=status:
                    self.controller.update_task(p, pr, t, status=s)
                )
        
        if menu.actions():
            menu.exec(self.phases_tree.viewport().mapToGlobal(pos))
    
    def show_about_dialog(self):
        """バージョン情報ダイアログを表示"""
        QMessageBox.about(
            self,
            "バージョン情報",
            "プロジェクト管理システム v1.0\n\n"
            "プロジェクト、フェーズ、プロセス、タスクの管理と進捗ログを記録するシステム"
        )
    
    # 追加するメソッド
    def show_excel_dialog(self):
        """Excel入出力ダイアログを表示"""
        from .excel_dialog import ExcelOperationDialog
        
        dialog = ExcelOperationDialog(self, self.controller)
        dialog.exec()

    def show_project_list(self):
        """プロジェクト一覧タブに切り替え"""
        self.tab_widget.setCurrentIndex(0)
    
    def show_gantt_chart(self):
        """ガントチャートタブに切り替え"""
        for i in range(self.tab_widget.count()):
            if isinstance(self.tab_widget.widget(i), GanttChartTab):
                self.tab_widget.setCurrentIndex(i)
                break

    def show_error_log(self):
        """エラーログタブに切り替え"""
        for i in range(self.tab_widget.count()):
            if isinstance(self.tab_widget.widget(i), ErrorLogTab):
                self.tab_widget.setCurrentIndex(i)
                break

    def closeEvent(self, event):
        """ウィンドウ終了時の処理"""
        # 現在のプロジェクトがあれば保存
        if self.controller.get_current_project():
            self.save_current_project()
        
        # 通知タブのタイマーを停止
        if hasattr(self, 'notification_tab') and self.notification_tab.refresh_timer.isActive():
            self.notification_tab.refresh_timer.stop()

        # タイマーを停止
        if self.save_timer.isActive():
            self.save_timer.stop()
        
        event.accept()

    def show_bulk_excel_dialog(self):
        """Excel一括インポートダイアログを表示"""
        from .bulk_excel_dialog import BulkExcelImportDialog
        
        dialog = BulkExcelImportDialog(self, self.controller)
        dialog.exec()

    def show_notifications(self):
        """通知タブに切り替え"""
        for i in range(self.tab_widget.count()):
            if isinstance(self.tab_widget.widget(i), NotificationTab):
                self.tab_widget.setCurrentIndex(i)
                break

    def update_notification_badge(self):
        """通知バッジを更新"""
        unread_count = self.controller.get_unread_notifications_count()
        
        if unread_count > 0:
            self.notification_badge.setText(str(unread_count))
            self.notification_badge.setVisible(True)
        else:
            self.notification_badge.setVisible(False)
