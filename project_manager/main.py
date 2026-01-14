#!/usr/bin/env python3
"""
プロジェクト管理システム
プロジェクト、フェーズ、プロセス、タスクの管理と進捗ログを記録するシステム

このモジュールはシステムのエントリーポイントを提供し、CUIまたはGUIインターフェースを起動します。
"""
import sys
import os
import argparse
from pathlib import Path

# 親ディレクトリをPythonパスに追加（開発環境での実行をサポート）
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_manager.interface.cli import run_cli


def parse_arguments():
    """
    コマンドライン引数を解析
    
    Returns:
        解析された引数
    """
    parser = argparse.ArgumentParser(
        description="プロジェクト管理システム - プロジェクト、フェーズ、プロセス、タスクの管理と進捗ログを記録するシステム"
    )
    
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="データを保存するディレクトリのパス（デフォルト: data）"
    )
    
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="ログを保存するディレクトリのパス（デフォルト: logs）"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="GUIモードで起動"
    )
    
    return parser.parse_args()


def main():
    """
    メイン関数
    引数を解析し、適切なインターフェースを起動
    
    Returns:
        終了コード
    """
    args = parse_arguments()
    
    # 環境変数を設定（データディレクトリとログディレクトリ）
    os.environ["PM_DATA_DIR"] = args.data_dir
    os.environ["PM_LOG_DIR"] = args.log_dir
    
    # GUIモードが指定されている場合はGUIを起動
    if args.gui:
        try:
            # GUIモジュールを動的にインポート
            from project_manager.interface.gui import run_gui
            return run_gui()
        except ImportError as e:
            print(f"GUIモードの起動に失敗しました: {str(e)}")
            print("必要なパッケージがインストールされていない可能性があります。")
            print("PySide6をインストールしてください: pip install PySide6")
            return 1
    
    # CLIを実行
    return run_cli()


if __name__ == "__main__":
    sys.exit(main())
