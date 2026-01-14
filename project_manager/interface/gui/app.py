"""
GUIアプリケーション
プロジェクト管理システムのGUIインターフェースのメインアプリケーション
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from .main_window import MainWindow
from .controller import GUIController


class ProjectManagerGUI:
    """
    プロジェクト管理システムのGUIアプリケーション
    """
    
    def __init__(self):
        """GUIアプリケーションの初期化"""
        # QApplicationの作成（既存の場合は再利用）
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setApplicationName("プロジェクト管理システム")
        
        # GUIコントローラーの作成
        self.controller = GUIController()
        
        # メインウィンドウの作成
        self.main_window = MainWindow(self.controller)
    
    def run(self):
        """
        アプリケーションを実行
        
        Returns:
            アプリケーションの終了コード
        """
        # メインウィンドウを表示
        self.main_window.show()
        
        # イベントループを開始
        return self.app.exec()


def run_gui():
    """
    GUIを実行
    
    Returns:
        終了コード
    """
    try:
        gui = ProjectManagerGUI()
        return gui.run()
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return 1
