# project_manager/excel/excel_utils.py の変更部分

"""
Excelユーティリティ
Excel入出力のための共通機能を提供
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet


def get_cell_value(worksheet: Worksheet, cell_address: str) -> Any:
    """
    指定したセルの値を取得
    
    Args:
        worksheet: ワークシート
        cell_address: セルアドレス（例: "A1"）
    
    Returns:
        セルの値
    """
    cell = worksheet[cell_address]
    return cell.value


def set_cell_value(worksheet: Worksheet, cell_address: str, value: Any) -> None:
    """
    指定したセルに値を設定
    
    Args:
        worksheet: ワークシート
        cell_address: セルアドレス（例: "A1"）
        value: 設定する値
    """
    worksheet[cell_address] = value


def find_last_row_with_data(worksheet: Worksheet, column: str) -> int:
    """
    指定した列の最後のデータが存在する行番号を取得
    
    Args:
        worksheet: ワークシート
        column: 列（例: "A"）
    
    Returns:
        最後のデータが存在する行番号
    """
    last_row = 1
    for row in range(1, worksheet.max_row + 1):
        cell_value = worksheet[f"{column}{row}"].value
        if cell_value is not None:
            last_row = row
    return last_row


def parse_excel_date(date_value) -> Optional[datetime]:
    """
    Excelの日付値をdatetimeに変換
    
    Args:
        date_value: Excelの日付値
    
    Returns:
        datetime または None
    """
    if date_value is None:
        return None
    
    # 既にdatetime型の場合はそのまま返す
    if isinstance(date_value, datetime):
        return date_value
    
    try:
        # 文字列の場合はパース試行
        if isinstance(date_value, str):
            # トリムして空白を除去
            date_str = date_value.strip()
            
            # 空文字列の場合はNoneを返す
            if not date_str:
                return None
            
            # よく使われる日付形式のリスト
            formats = [
                "%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日",  # 標準的な形式
                "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M",      # 時刻付き
                "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y", "%d/%m/%Y",                  # 月日年形式
                "%m-%d-%Y", "%d-%m-%Y",
                "%b %d, %Y", "%d %b %Y",                 # 月名形式
                "%B %d, %Y", "%d %B %Y"
            ]
            
            # 各形式でパース試行
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # 特殊な形式: "2023.4.1" のようなドット区切り
            if "." in date_str:
                parts = date_str.split(".")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    try:
                        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    except ValueError:
                        pass
            
            # どのフォーマットでもパースできない場合
            return None
        
        # 数値の場合はExcelのシリアル値として変換
        if isinstance(date_value, (int, float)):
            try:
                return datetime(1899, 12, 30) + timedelta(days=date_value)
            except:
                return None
    except Exception as e:
        print(f"日付変換エラー: {str(e)}, 値: {date_value}, 型: {type(date_value)}")
        return None
    
    # その他の型は処理不能
    return None
