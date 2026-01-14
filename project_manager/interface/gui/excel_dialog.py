# project_manager/interface/gui/excel_dialog.py の変更部分

"""
Excelダイアログ
Excel入出力のためのダイアログ
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QRadioButton, QButtonGroup, QGroupBox,
    QMessageBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt

# 相対パスを使用する場合
from ...excel.excel_importer import ExcelImporter
from ...excel.excel_exporter import ExcelExporter
# 正しいインポート (相対パスを使用する場合)
from ...core.manager import get_project_manager


class ExcelOperationDialog(QDialog):
    """
    Excel入出力操作のダイアログ
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
        self.importer = ExcelImporter()
        self.exporter = ExcelExporter()
        
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        # ウィンドウの設定
        self.setWindowTitle("Excel入出力")
        self.setMinimumWidth(400)
        
        # レイアウト作成
        main_layout = QVBoxLayout(self)
        
        # 操作選択
        operation_group = QGroupBox("操作の選択")
        operation_layout = QVBoxLayout(operation_group)
        
        self.import_radio = QRadioButton("Excelからインポート")
        self.export_radio = QRadioButton("Excelにエクスポート")
        
        self.operation_group = QButtonGroup()
        self.operation_group.addButton(self.import_radio, 1)
        self.operation_group.addButton(self.export_radio, 2)
        
        # デフォルトでエクスポートを選択
        self.export_radio.setChecked(True)
        
        operation_layout.addWidget(self.import_radio)
        operation_layout.addWidget(self.export_radio)
        
        main_layout.addWidget(operation_group)
        
        # ファイル選択部分
        file_layout = QHBoxLayout()
        self.file_path_label = QLabel("ファイルが選択されていません")
        self.browse_button = QPushButton("参照...")
        self.browse_button.clicked.connect(self.browse_file)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(self.browse_button)
        
        main_layout.addLayout(file_layout)
        
        # オプション
        options_group = QGroupBox("オプション")
        options_layout = QVBoxLayout(options_group)
        
        # インポート時のオプション
        self.import_options = QGroupBox("インポートオプション")
        import_options_layout = QVBoxLayout(self.import_options)
        
        self.create_new_project_check = QCheckBox("新しいプロジェクトとして作成")
        self.create_new_project_check.setChecked(True)
        import_options_layout.addWidget(self.create_new_project_check)
        
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
        
        import_options_layout.addWidget(self.format_group)
        
        # 各フォーマットの説明
        format_info = QLabel("フォーマット情報:\n"
                           "・自動検出: シート構造を分析して最適なフォーマットを選択\n"
                           "・標準フォーマット: スケジュールシートと入力シートを持つ形式\n"
                           "・MS Project類似: タスクシートとリソースシートを持つ形式\n"
                           "・シンプルフォーマット: 単一シートのシンプルな形式")
        format_info.setWordWrap(True)
        import_options_layout.addWidget(format_info)
        
        self.import_options.setVisible(False)
        
        # エクスポート時のオプション
        self.export_options = QGroupBox("エクスポートオプション")
        export_options_layout = QVBoxLayout(self.export_options)
        
        self.include_tasks_check = QCheckBox("タスクを含める")
        self.include_tasks_check.setChecked(True)
        export_options_layout.addWidget(self.include_tasks_check)
        
        options_layout.addWidget(self.import_options)
        options_layout.addWidget(self.export_options)
        
        main_layout.addWidget(options_group)
        
        # 操作選択による表示切り替え
        self.import_radio.toggled.connect(self.toggle_operation_ui)
        self.toggle_operation_ui()
        
        # 実行・キャンセルボタン
        button_layout = QHBoxLayout()
        
        self.execute_button = QPushButton("実行")
        self.execute_button.clicked.connect(self.execute_operation)
        self.execute_button.setEnabled(False)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.execute_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def toggle_operation_ui(self):
        """操作選択による表示の切り替え"""
        is_import = self.import_radio.isChecked()
        
        self.import_options.setVisible(is_import)
        self.export_options.setVisible(not is_import)
        
        # ファイル選択ボタンのテキストを変更
        if is_import:
            self.browse_button.setText("Excelファイルを選択...")
        else:
            self.browse_button.setText("保存先を選択...")
    
    def browse_file(self):
        """ファイル選択ダイアログを表示"""
        is_import = self.import_radio.isChecked()
        
        if is_import:
            # インポート時はファイル選択
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Excelファイルを選択",
                "",
                "Excelファイル (*.xlsx *.xls *.xlsm)"
            )
        else:
            # エクスポート時は保存先選択
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存先を選択",
                "",
                "Excelファイル (*.xlsx *.xlsm)"
            )
            
            # 拡張子を付与
            if file_path and not file_path.lower().endswith(('.xlsx', '.xls', '.xlsm')):
                file_path += '.xlsx'
        
        if file_path:
            self.file_path_label.setText(file_path)
            self.execute_button.setEnabled(True)
        
        self.file_path = file_path if file_path else None
    
    def execute_operation(self):
        """選択された操作を実行"""
        if not hasattr(self, 'file_path') or not self.file_path:
            QMessageBox.warning(self, "警告", "ファイルを選択してください")
            return
        
        is_import = self.import_radio.isChecked()
        
        if is_import:
            # Excelからインポート
            self.import_from_excel()
        else:
            # Excelにエクスポート
            self.export_to_excel()
    
    def import_from_excel(self):
        """Excelからプロジェクトをインポート"""
        try:
            # デバッグ情報を追加
            print(f"インポート開始: {self.file_path}")
            
            # フォーマット選択を取得
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
            
            # ファイルからプロジェクトをインポート
            project = self.importer.import_from_file(self.file_path)
            
            if not project:
                QMessageBox.critical(self, "エラー", "プロジェクトのインポートに失敗しました。ファイル形式を確認してください。")
                return
            
            # プロジェクトをシステムに登録
            manager = get_project_manager()
            
            # 新規プロジェクトとして作成するか
            if self.create_new_project_check.isChecked():
                # 新規プロジェクトとして保存
                manager.data_store.save_project(project)
                manager.current_project = project
            else:
                # 既存プロジェクトを更新
                if manager.current_project:
                    # 既存プロジェクトの情報を維持
                    project.id = manager.current_project.id
                    project.created_at = manager.current_project.created_at
                    
                    manager.current_project = project
                    manager.save_current_project()
                else:
                    QMessageBox.warning(self, "警告", "更新するプロジェクトが開かれていません。新規プロジェクトとして保存します。")
                    manager.data_store.save_project(project)
                    manager.current_project = project
            
            # コントローラーの通知を発行
            if self.controller:
                self.controller.project_changed.emit()
                self.controller.phases_changed.emit()
            
            QMessageBox.information(self, "成功", f"Excelからプロジェクト「{project.name}」をインポートしました")
            self.accept()
            
        except Exception as e:
            # 詳細なエラー情報をコンソールに出力
            import traceback
            print(f"インポート中に例外が発生: {str(e)}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "エラー", f"プロジェクトのインポートに失敗しました。\n詳細: {str(e)}")
    
    def export_to_excel(self):
        """プロジェクトをExcelにエクスポート"""
        manager = get_project_manager()
        
        if not manager.current_project:
            QMessageBox.warning(self, "警告", "エクスポートするプロジェクトが開かれていません")
            return
        
        try:
            # プロジェクトをエクスポート
            include_tasks = self.include_tasks_check.isChecked()
            
            success = self.exporter.export_to_file(manager.current_project, self.file_path)
            
            if success:
                QMessageBox.information(self, "成功", f"プロジェクト「{manager.current_project.name}」をExcelにエクスポートしました")
                self.accept()
            else:
                QMessageBox.critical(self, "エラー", "エクスポートに失敗しました")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"エクスポート中にエラーが発生しました: {str(e)}")
