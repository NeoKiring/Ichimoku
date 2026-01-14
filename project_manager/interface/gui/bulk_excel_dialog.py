"""
Excel一括インポートダイアログ
複数のExcelファイルを一括でインポートするためのダイアログ
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QRadioButton, QButtonGroup, QGroupBox,
    QMessageBox, QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QProgressBar,
    QTextEdit
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal

# 相対パスを使用する場合
from ...excel.bulk_excel_importer import BulkExcelImporter
from ...core.manager import get_project_manager


class BulkExcelImportDialog(QDialog):
    """
    Excel一括インポート操作のダイアログ
    """
    
    def __init__(self, parent=None, controller=None):
        """
        ダイアログの初期化
        
        Args:
            parent: 親ウィジェット
            controller: GUIコントローラー
        """
        super().__init__(parent)
        
        self.parent = parent
        self.controller = controller
        self.importer = BulkExcelImporter()
        self.selected_directory = None
        self.import_results = None
        
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("Excel一括インポート")
        self.resize(800, 600)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        
        # ディレクトリ選択部分
        directory_layout = QHBoxLayout()
        self.directory_path_label = QLabel("ディレクトリが選択されていません")
        self.browse_button = QPushButton("ディレクトリを選択...")
        self.browse_button.clicked.connect(self.browse_directory)
        
        directory_layout.addWidget(QLabel("インポート対象ディレクトリ:"))
        directory_layout.addWidget(self.directory_path_label, 1)
        directory_layout.addWidget(self.browse_button)
        
        main_layout.addLayout(directory_layout)
        
        # フォーマット選択グループ
        self.format_group = QGroupBox("フォーマット設定")
        format_layout = QVBoxLayout(self.format_group)
        
        self.format_auto_radio = QRadioButton("自動検出")
        self.format_standard_radio = QRadioButton("標準フォーマット")
        self.format_ms_project_radio = QRadioButton("MS Project類似")
        self.format_simple_radio = QRadioButton("シンプルフォーマット")
        
        self.format_group_btn = QButtonGroup()
        self.format_group_btn.addButton(self.format_auto_radio, 1)
        self.format_group_btn.addButton(self.format_standard_radio, 2)
        self.format_group_btn.addButton(self.format_ms_project_radio, 3)
        self.format_group_btn.addButton(self.format_simple_radio, 4)
        
        # デフォルトで自動検出を選択
        self.format_auto_radio.setChecked(True)
        
        format_layout.addWidget(self.format_auto_radio)
        format_layout.addWidget(self.format_standard_radio)
        format_layout.addWidget(self.format_ms_project_radio)
        format_layout.addWidget(self.format_simple_radio)
        
        # 各フォーマットの説明
        format_info = QLabel("フォーマット情報:\n"
                           "・自動検出: シート構造を分析して最適なフォーマットを選択\n"
                           "・標準フォーマット: スケジュールシートと入力シートを持つ形式\n"
                           "・MS Project類似: タスクシートとリソースシートを持つ形式\n"
                           "・シンプルフォーマット: 単一シートのシンプルな形式")
        format_info.setWordWrap(True)
        format_layout.addWidget(format_info)
        
        main_layout.addWidget(self.format_group)
        
        # オプショングループ
        options_group = QGroupBox("インポートオプション")
        options_layout = QVBoxLayout(options_group)
        
        self.create_new_project_check = QCheckBox("すべて新しいプロジェクトとして作成")
        self.create_new_project_check.setChecked(True)
        options_layout.addWidget(self.create_new_project_check)
        
        main_layout.addWidget(options_group)
        
        # 進捗バー（初期状態では非表示）
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 結果表示エリア（初期状態では非表示）
        self.result_group = QGroupBox("インポート結果")
        self.result_group.setVisible(False)
        result_layout = QVBoxLayout(self.result_group)
        
        self.result_summary_label = QLabel("インポート結果サマリー")
        result_layout.addWidget(self.result_summary_label)
        
        # 結果詳細テーブル
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["ファイル名", "サブディレクトリ", "状態", "プロジェクト名", "詳細"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        result_layout.addWidget(self.result_table)
        
        main_layout.addWidget(self.result_group)
        
        # 実行・キャンセルボタン
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("一括インポート実行")
        self.execute_button.clicked.connect(self.execute_bulk_import)
        self.execute_button.setEnabled(False)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.execute_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def browse_directory(self):
        """ディレクトリ選択ダイアログを表示"""
        directory_path = QFileDialog.getExistingDirectory(
            self,
            "インポート対象ディレクトリを選択",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory_path:
            self.directory_path_label.setText(directory_path)
            self.selected_directory = directory_path
            self.execute_button.setEnabled(True)
    
    def execute_bulk_import(self):
        """一括インポートを実行"""
        if not self.selected_directory:
            QMessageBox.warning(self, "警告", "ディレクトリを選択してください")
            return
        
        # フォーマットタイプを設定
        if self.format_standard_radio.isChecked():
            format_type = "standard"
        elif self.format_ms_project_radio.isChecked():
            format_type = "ms_project"
        elif self.format_simple_radio.isChecked():
            format_type = "simple"
        else:
            format_type = "auto"  # 自動検出
        
        # インポーターにフォーマット情報を渡す
        self.importer.set_format_type(format_type)
        
        # UI状態更新
        self.execute_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.format_group.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(10)
        
        try:
            # インポート実行
            self.import_results = self.importer.bulk_import_from_directory(self.selected_directory)
            
            # 進捗更新
            self.progress_bar.setValue(90)
            
            # 結果を表示
            self.show_import_results()
            
            # インポートしたプロジェクトをシステムに登録
            manager = get_project_manager()
            create_new = self.create_new_project_check.isChecked()
            
            for project in self.import_results.get("projects", []):
                # 新規プロジェクトとして保存
                manager.data_store.save_project(project)
            
            # 最後にインポートしたプロジェクトを現在のプロジェクトとして設定
            if self.import_results.get("projects"):
                manager.current_project = self.import_results["projects"][-1]
                
                # コントローラーの通知を発行
                if self.controller:
                    self.controller.project_changed.emit()
                    self.controller.phases_changed.emit()
            
            # 完了
            self.progress_bar.setValue(100)
            
        except Exception as e:
            # エラー処理
            import traceback
            print(f"一括インポート中に例外が発生: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"一括インポート中にエラーが発生しました。\n詳細: {str(e)}")
            
            # UI状態を元に戻す
            self.execute_button.setEnabled(True)
            self.browse_button.setEnabled(True)
            self.format_group.setEnabled(True)
            self.progress_bar.setVisible(False)
    
    def show_import_results(self):
        """インポート結果の表示"""
        if not self.import_results:
            return
        
        # サマリーの表示
        success_count = self.import_results.get("success_count", 0)
        fail_count = self.import_results.get("fail_count", 0)
        total_count = success_count + fail_count
        
        summary_text = (f"インポート結果: 合計 {total_count} ファイル中、"
                      f"成功: {success_count} ファイル、"
                      f"失敗: {fail_count} ファイル")
        
        if "error" in self.import_results:
            summary_text += f"\nエラー: {self.import_results['error']}"
        
        self.result_summary_label.setText(summary_text)
        
        # 詳細テーブルの表示
        details = self.import_results.get("details", [])
        self.result_table.setRowCount(len(details))
        
        for row, detail in enumerate(details):
            # ファイル名
            self.result_table.setItem(row, 0, QTableWidgetItem(detail.get("file_name", "")))
            
            # サブディレクトリ
            self.result_table.setItem(row, 1, QTableWidgetItem(detail.get("subdirectory", "")))
            
            # 状態
            status_item = QTableWidgetItem(detail.get("status", ""))
            if detail.get("status") == "成功":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif detail.get("status") in ["失敗", "エラー"]:
                status_item.setForeground(Qt.GlobalColor.red)
            self.result_table.setItem(row, 2, status_item)
            
            # プロジェクト名
            self.result_table.setItem(row, 3, QTableWidgetItem(detail.get("project_name", "")))
            
            # 詳細
            error_detail = detail.get("error", "")
            phase_count = detail.get("phase_count", 0)
            
            if detail.get("status") == "成功":
                detail_text = f"フェーズ数: {phase_count}"
            else:
                detail_text = error_detail
                
            self.result_table.setItem(row, 4, QTableWidgetItem(detail_text))
        
        # 列幅を調整
        self.result_table.resizeColumnsToContents()
        
        # 結果グループを表示
        self.result_group.setVisible(True)
        
        # UI状態を更新
        self.cancel_button.setText("閉じる")
