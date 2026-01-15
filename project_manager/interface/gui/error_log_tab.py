"""
エラーログタブ
システムのエラーログを表示・検索する機能を提供
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QLineEdit, QFormLayout, QGroupBox, QTextEdit,
    QDialog, QDialogButtonBox, QCheckBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QDateTime, Signal
from PySide6.QtGui import QColor

from ...core.logger import get_logger, LogLevel
from ...core.error_handler import log_exception
from .utils import show_error_message, show_info_message


class ErrorDetailsDialog(QDialog):
    """エラー詳細を表示するダイアログ"""
    
    def __init__(self, parent=None, error_data: Dict[str, Any] = None):
        """
        ダイアログの初期化
        
        Args:
            parent: 親ウィジェット
            error_data: エラー情報
        """
        super().__init__(parent)
        
        self.error_data = error_data
        self.init_ui()
        
        if error_data:
            self.set_error_data(error_data)
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("エラー詳細")
        self.setMinimumSize(700, 500)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        
        # 基本情報
        basic_info_group = QGroupBox("基本情報")
        basic_form = QFormLayout(basic_info_group)
        
        self.timestamp_label = QLabel()
        basic_form.addRow("発生日時:", self.timestamp_label)
        
        self.level_label = QLabel()
        basic_form.addRow("レベル:", self.level_label)
        
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        basic_form.addRow("メッセージ:", self.message_label)
        
        self.location_label = QLabel()
        basic_form.addRow("発生場所:", self.location_label)
        
        main_layout.addWidget(basic_info_group)
        
        # スタックトレース
        stack_group = QGroupBox("スタックトレース")
        stack_layout = QVBoxLayout(stack_group)
        
        self.stack_trace_edit = QTextEdit()
        self.stack_trace_edit.setReadOnly(True)
        self.stack_trace_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        stack_layout.addWidget(self.stack_trace_edit)
        
        main_layout.addWidget(stack_group)
        
        # 詳細情報
        details_group = QGroupBox("詳細情報")
        details_layout = QVBoxLayout(details_group)
        
        self.details_edit = QTextEdit()
        self.details_edit.setReadOnly(True)
        details_layout.addWidget(self.details_edit)
        
        main_layout.addWidget(details_group)
        
        # ボタン
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        
        export_button = QPushButton("エクスポート")
        export_button.clicked.connect(self.export_error_data)
        button_box.addButton(export_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        main_layout.addWidget(button_box)
    
    def set_error_data(self, error_data: Dict[str, Any]):
        """
        エラーデータを設定
        
        Args:
            error_data: エラー情報
        """
        # タイムスタンプ
        if "timestamp" in error_data:
            try:
                timestamp = datetime.fromisoformat(error_data["timestamp"])
                self.timestamp_label.setText(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            except (ValueError, TypeError):
                self.timestamp_label.setText(str(error_data.get("timestamp", "不明")))
        else:
            self.timestamp_label.setText("不明")
        
        # レベル
        level = error_data.get("level", "不明")
        self.level_label.setText(level)
        
        # レベルに応じた色を設定
        if level == LogLevel.CRITICAL:
            self.level_label.setStyleSheet("color: red; font-weight: bold;")
        elif level == LogLevel.ERROR:
            self.level_label.setStyleSheet("color: red;")
        elif level == LogLevel.WARNING:
            self.level_label.setStyleSheet("color: orange;")
        
        # メッセージ
        self.message_label.setText(error_data.get("message", "不明"))
        
        # 発生場所
        module = error_data.get("module", "不明")
        function = error_data.get("function", "不明")
        self.location_label.setText(f"{module}.{function}")
        
        # スタックトレース
        stack_trace = error_data.get("stack_trace", [])
        if stack_trace:
            if isinstance(stack_trace, list):
                stack_text = ''.join(stack_trace)
            else:
                stack_text = str(stack_trace)
            self.stack_trace_edit.setText(stack_text)
        else:
            self.stack_trace_edit.setText("スタックトレースはありません")
        
        # 詳細情報
        details = error_data.get("details", {})
        if details:
            details_text = ""
            for key, value in details.items():
                details_text += f"{key}: {value}\n"
            self.details_edit.setText(details_text)
        else:
            self.details_edit.setText("詳細情報はありません")
    
    def export_error_data(self):
        """エラーデータをファイルにエクスポート"""
        if not self.error_data:
            return
        
        # エクスポート先のファイル名を選択
        options = QFileDialog.Option.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "エラー情報のエクスポート", "", "JSONファイル (*.json);;テキストファイル (*.txt)",
            options=options
        )
        
        if not filename:
            return
        
        try:
            # ファイル拡張子に応じてフォーマットを変更
            if filename.endswith('.json'):
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.error_data, f, ensure_ascii=False, indent=2)
            else:
                # テキスト形式（.txt）
                with open(filename, 'w', encoding='utf-8') as f:
                    # 基本情報
                    f.write(f"発生日時: {self.timestamp_label.text()}\n")
                    f.write(f"レベル: {self.level_label.text()}\n")
                    f.write(f"メッセージ: {self.message_label.text()}\n")
                    f.write(f"発生場所: {self.location_label.text()}\n\n")
                    
                    # スタックトレース
                    f.write("=== スタックトレース ===\n")
                    f.write(self.stack_trace_edit.toPlainText())
                    f.write("\n\n")
                    
                    # 詳細情報
                    f.write("=== 詳細情報 ===\n")
                    f.write(self.details_edit.toPlainText())
            
            show_info_message(self, "エクスポート成功", "エラー情報のエクスポートに成功しました")
        except Exception as e:
            show_error_message(self, "エクスポート失敗", f"エラー情報のエクスポートに失敗しました: {str(e)}")
            log_exception(e, "Failed to export error data")


class ErrorLogTab(QWidget):
    """
    エラーログを表示・検索するタブ
    """
    
    # エラーが選択されたときのシグナル
    error_selected = Signal(dict)
    
    def __init__(self, parent=None):
        """
        エラーログタブの初期化
        
        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        
        self.logger = get_logger()
        self.current_filters = {}
        self.error_logs = []
        
        self.init_ui()
        self.load_error_logs()
    
    def init_ui(self):
        """UIの初期化"""
        # メインレイアウト
        main_layout = QVBoxLayout(self)
        
        # フィルターエリア
        filter_group = QGroupBox("検索フィルター")
        filter_layout = QFormLayout(filter_group)
        
        # レベルフィルター
        self.level_combo = QComboBox()
        self.level_combo.addItem("すべてのレベル", None)
        self.level_combo.addItem("CRITICAL", LogLevel.CRITICAL)
        self.level_combo.addItem("ERROR", LogLevel.ERROR)
        self.level_combo.addItem("WARNING", LogLevel.WARNING)
        self.level_combo.addItem("INFO", LogLevel.INFO)
        self.level_combo.addItem("DEBUG", LogLevel.DEBUG)
        self.level_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addRow("レベル:", self.level_combo)
        
        # 日付範囲フィルター
        date_range_layout = QHBoxLayout()
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))  # デフォルトは1週間前
        date_range_layout.addWidget(self.start_date_edit)
        
        date_range_layout.addWidget(QLabel("〜"))
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())  # デフォルトは今日
        date_range_layout.addWidget(self.end_date_edit)
        
        filter_layout.addRow("日付範囲:", date_range_layout)
        
        # モジュールフィルター
        self.module_combo = QComboBox()
        self.module_combo.addItem("すべてのモジュール", None)
        self.module_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addRow("モジュール:", self.module_combo)
        
        # テキスト検索
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("テキスト検索...")
        self.search_edit.returnPressed.connect(self.apply_filters)
        filter_layout.addRow("検索:", self.search_edit)
        
        # フィルターボタン
        buttons_layout = QHBoxLayout()
        
        apply_filter_button = QPushButton("フィルター適用")
        apply_filter_button.clicked.connect(self.apply_filters)
        buttons_layout.addWidget(apply_filter_button)
        
        reset_filter_button = QPushButton("フィルターリセット")
        reset_filter_button.clicked.connect(self.reset_filters)
        buttons_layout.addWidget(reset_filter_button)
        
        filter_layout.addRow("", buttons_layout)
        
        main_layout.addWidget(filter_group)
        
        # エラー統計情報
        stats_group = QGroupBox("エラー統計")
        stats_layout = QHBoxLayout(stats_group)
        
        self.total_errors_label = QLabel("総エラー数: 0")
        stats_layout.addWidget(self.total_errors_label)
        
        stats_layout.addStretch()
        
        self.critical_count_label = QLabel("CRITICAL: 0")
        self.critical_count_label.setStyleSheet("color: red; font-weight: bold;")
        stats_layout.addWidget(self.critical_count_label)
        
        self.error_count_label = QLabel("ERROR: 0")
        self.error_count_label.setStyleSheet("color: red;")
        stats_layout.addWidget(self.error_count_label)
        
        self.warning_count_label = QLabel("WARNING: 0")
        self.warning_count_label.setStyleSheet("color: orange;")
        stats_layout.addWidget(self.warning_count_label)
        
        stats_layout.addStretch()
        
        refresh_button = QPushButton("更新")
        refresh_button.clicked.connect(self.load_error_logs)
        stats_layout.addWidget(refresh_button)
        
        export_button = QPushButton("エクスポート")
        export_button.clicked.connect(self.export_error_logs)
        stats_layout.addWidget(export_button)
        
        main_layout.addWidget(stats_group)
        
        # エラーログテーブル
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels(["発生日時", "レベル", "メッセージ", "モジュール", "関数"])
        
        # リサイズ可能に変更
        self.error_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.error_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # 初期列幅を設定
        self.error_table.setColumnWidth(0, 180)  # 発生日時
        self.error_table.setColumnWidth(1, 100)  # レベル
        self.error_table.setColumnWidth(2, 350)  # メッセージ
        self.error_table.setColumnWidth(3, 150)  # モジュール
        self.error_table.setColumnWidth(4, 150)  # 関数
        
        self.error_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.error_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.error_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # ダブルクリックで詳細表示
        self.error_table.cellDoubleClicked.connect(self.show_error_details)
        
        main_layout.addWidget(self.error_table)
        
        # 詳細ボタンエリア
        bottom_layout = QHBoxLayout()
        
        view_details_button = QPushButton("詳細を表示")
        view_details_button.clicked.connect(self.view_selected_error)
        bottom_layout.addWidget(view_details_button)
        
        bottom_layout.addStretch()
        
        main_layout.addLayout(bottom_layout)
    
    def load_error_logs(self):
        """エラーログを読み込む"""
        try:
            # フィルター条件の取得
            level = self.level_combo.currentData()
            
            start_date = self.start_date_edit.date().toPython()
            start_datetime = datetime.combine(start_date, datetime.min.time())

            end_date = self.end_date_edit.date().toPython()
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            module = self.module_combo.currentData()
            
            # エラーログを取得
            self.error_logs = self.logger.get_error_logs(
                level=level,
                start_date=start_datetime,
                end_date=end_datetime,
                module=module,
                limit=1000  # 最大1000件まで取得
            )
            
            # テーブルを更新
            self.update_error_table()
            
            # モジュールコンボボックスの選択肢を更新
            self.update_module_combo()
            
            # 統計情報を更新
            self.update_statistics()
        except Exception as e:
            show_error_message(self, "エラー", f"エラーログの読み込みに失敗しました: {str(e)}")
            log_exception(e, "Failed to load error logs")
    
    def update_error_table(self):
        """エラーログテーブルを更新"""
        # 事前にテーブルをクリア
        self.error_table.setRowCount(0)
        
        # 検索テキストでフィルタリング
        search_text = self.search_edit.text().lower()
        filtered_logs = []
        
        for log in self.error_logs:
            # 検索テキストがある場合はフィルタリング
            if search_text:
                # メッセージ、モジュール、関数名から検索
                message = str(log.get("message", "")).lower()
                module = str(log.get("module", "")).lower()
                function = str(log.get("function", "")).lower()
                
                if (search_text in message or search_text in module or search_text in function):
                    filtered_logs.append(log)
            else:
                filtered_logs.append(log)
        
        # テーブルに追加
        self.error_table.setRowCount(len(filtered_logs))
        
        for row, log in enumerate(filtered_logs):
            # 発生日時
            timestamp = "不明"
            try:
                if "timestamp" in log:
                    timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
            
            timestamp_item = QTableWidgetItem(timestamp)
            self.error_table.setItem(row, 0, timestamp_item)
            
            # レベル
            level = log.get("level", "不明")
            level_item = QTableWidgetItem(level)
            
            # レベルに応じた色を設定
            if level == LogLevel.CRITICAL:
                level_item.setForeground(QColor(255, 0, 0))  # 赤
                level_item.setFont(level_item.font())
                font = level_item.font()
                font.setBold(True)
                level_item.setFont(font)
            elif level == LogLevel.ERROR:
                level_item.setForeground(QColor(255, 0, 0))  # 赤
            elif level == LogLevel.WARNING:
                level_item.setForeground(QColor(255, 165, 0))  # オレンジ
            
            self.error_table.setItem(row, 1, level_item)
            
            # メッセージ
            message = log.get("message", "不明")
            message_item = QTableWidgetItem(message)
            self.error_table.setItem(row, 2, message_item)
            
            # モジュール
            module = log.get("module", "不明")
            module_item = QTableWidgetItem(module)
            self.error_table.setItem(row, 3, module_item)
            
            # 関数
            function = log.get("function", "不明")
            function_item = QTableWidgetItem(function)
            self.error_table.setItem(row, 4, function_item)
            
            # 元のログデータをユーザーデータとして保存
            self.error_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, log)
    
    def update_module_combo(self):
        """モジュールコンボボックスの選択肢を更新"""
        # 現在の選択を保存
        current_selection = self.module_combo.currentData()
        
        # シグナルをブロック（追加）
        self.module_combo.blockSignals(True)
        
        # コンボボックスをクリア
        self.module_combo.clear()
        self.module_combo.addItem("すべてのモジュール", None)
        
        # モジュールリストを収集
        modules = set()
        for log in self.error_logs:
            if "module" in log and log["module"]:
                modules.add(log["module"])
        
        # モジュールリストをコンボボックスに追加
        for module in sorted(modules):
            self.module_combo.addItem(module, module)
        
        # 以前の選択を復元
        if current_selection:
            index = self.module_combo.findData(current_selection)
            if index >= 0:
                self.module_combo.setCurrentIndex(index)
    
        # シグナルのブロックを解除（追加）
        self.module_combo.blockSignals(False)
    
    def update_statistics(self):
        """統計情報を更新"""
        # エラーレベル別のカウント
        critical_count = 0
        error_count = 0
        warning_count = 0
        
        for log in self.error_logs:
            level = log.get("level")
            if level == LogLevel.CRITICAL:
                critical_count += 1
            elif level == LogLevel.ERROR:
                error_count += 1
            elif level == LogLevel.WARNING:
                warning_count += 1
        
        # ラベルを更新
        self.total_errors_label.setText(f"総エラー数: {len(self.error_logs)}")
        self.critical_count_label.setText(f"CRITICAL: {critical_count}")
        self.error_count_label.setText(f"ERROR: {error_count}")
        self.warning_count_label.setText(f"WARNING: {warning_count}")
    
    def apply_filters(self):
        """フィルターを適用してログを再読み込み"""
        self.load_error_logs()
    
    def reset_filters(self):
        """フィルターをリセット"""
        self.level_combo.setCurrentIndex(0)  # すべてのレベル
        
        # 日付範囲を1週間前から今日までに設定
        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        
        self.module_combo.setCurrentIndex(0)  # すべてのモジュール
        self.search_edit.clear()  # 検索テキストをクリア
        
        # ログを再読み込み
        self.load_error_logs()
    
    def show_error_details(self, row, col):
        """
        エラーの詳細情報ダイアログを表示
        
        Args:
            row: クリックされた行
            col: クリックされた列
        """
        error_data = self.error_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if error_data:
            dialog = ErrorDetailsDialog(self, error_data)
            dialog.exec()
    
    def view_selected_error(self):
        """選択されたエラーの詳細を表示"""
        selected_items = self.error_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            error_data = self.error_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if error_data:
                dialog = ErrorDetailsDialog(self, error_data)
                dialog.exec()
    
    def export_error_logs(self):
        """現在表示されているエラーログをファイルにエクスポート"""
        if not self.error_logs:
            show_info_message(self, "エクスポート", "エクスポートするエラーログがありません")
            return
        
        # エクスポート先のファイル名を選択
        options = QFileDialog.Option.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(
            self, "エラーログのエクスポート", "", "JSONファイル (*.json);;CSVファイル (*.csv)",
            options=options
        )
        
        if not filename:
            return
        
        try:
            # 検索テキストでフィルタリングしたログを取得
            search_text = self.search_edit.text().lower()
            filtered_logs = []
            
            for log in self.error_logs:
                if search_text:
                    message = str(log.get("message", "")).lower()
                    module = str(log.get("module", "")).lower()
                    function = str(log.get("function", "")).lower()
                    
                    if (search_text in message or search_text in module or search_text in function):
                        filtered_logs.append(log)
                else:
                    filtered_logs.append(log)
            
            # ファイル拡張子に応じてフォーマットを変更
            if filename.endswith('.json'):
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(filtered_logs, f, ensure_ascii=False, indent=2)
            elif filename.endswith('.csv'):
                import csv
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    # ヘッダー行
                    writer.writerow(["発生日時", "レベル", "メッセージ", "モジュール", "関数"])
                    
                    # データ行
                    for log in filtered_logs:
                        timestamp = "不明"
                        try:
                            if "timestamp" in log:
                                timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError):
                            pass
                        
                        writer.writerow([
                            timestamp,
                            log.get("level", "不明"),
                            log.get("message", "不明"),
                            log.get("module", "不明"),
                            log.get("function", "不明")
                        ])
            
            show_info_message(self, "エクスポート成功", "エラーログのエクスポートに成功しました")
        except Exception as e:
            show_error_message(self, "エクスポート失敗", f"エラーログのエクスポートに失敗しました: {str(e)}")
            log_exception(e, "Failed to export error logs")
