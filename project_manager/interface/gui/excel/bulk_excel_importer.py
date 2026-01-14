"""
Excelファイル一括インポーター
指定したディレクトリから【Gantt】で始まるExcelファイルを一括インポート
"""
import os
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from ..models import Project
from .excel_importer import ExcelImporter

class BulkExcelImporter:
    """
    ディレクトリ内のExcelファイルを一括インポートするクラス
    """
    
    def __init__(self):
        """一括インポーターの初期化"""
        self.importer = ExcelImporter()
        
    def set_format_type(self, format_type: str):
        """
        インポートするフォーマットタイプを設定
        
        Args:
            format_type: フォーマットタイプ ('auto', 'standard', 'ms_project', 'simple')
        """
        self.importer.set_format_type(format_type)
    
    def bulk_import_from_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        指定ディレクトリの一階層下にある【Ganttから始まるExcelファイルを一括インポート
        
        Args:
            directory_path: 最上位ディレクトリパス
            
        Returns:
            インポート結果の辞書（成功件数、失敗件数、詳細など）
        """
        result = {
            "success_count": 0,
            "fail_count": 0,
            "details": [],
            "projects": []
        }
        
        try:
            # ディレクトリの存在確認
            if not os.path.isdir(directory_path):
                result["error"] = f"指定されたパス '{directory_path}' はディレクトリではありません"
                return result
            
            # 一階層下のディレクトリを取得
            subdirs = [d for d in os.listdir(directory_path) 
                      if os.path.isdir(os.path.join(directory_path, d))]
            
            print(f"検索対象サブディレクトリ: {len(subdirs)}個")
            
            # 各サブディレクトリ内の【Ganttから始まるExcelファイルをインポート
            for subdir in subdirs:
                subdir_path = os.path.join(directory_path, subdir)
                excel_files = []
                
                # 【Ganttから始まるExcelファイルを検索
                for ext in ['xlsx', 'xls', 'xlsm']:
                    pattern = os.path.join(subdir_path, "【Gantt*." + ext)
                    excel_files.extend(glob.glob(pattern))
                
                print(f"サブディレクトリ '{subdir}' 内のExcelファイル数: {len(excel_files)}個")
                
                # 各ファイルをインポート
                for file_path in excel_files:
                    file_name = os.path.basename(file_path)
                    import_result = {
                        "file_path": file_path,
                        "file_name": file_name,
                        "subdirectory": subdir,
                        "status": "未処理"
                    }
                    
                    try:
                        print(f"インポート開始: {file_path}")
                        project = self.importer.import_from_file(file_path)
                        
                        if project:
                            # ファイル名からプロジェクト名を設定（既に設定されている場合は上書きしない）
                            if project.name == "Excelからインポートしたプロジェクト" or not project.name:
                                # ファイル名から【Gantt Chart】などの部分を除去してプロジェクト名に設定
                                clean_name = file_name.replace(".xlsx", "").replace(".xls", "").replace(".xlsm", "")
                                # 【Gantt Chart】などの部分を除去
                                if "【" in clean_name and "】" in clean_name:
                                    start_idx = clean_name.find("【")
                                    end_idx = clean_name.find("】") + 1
                                    prefix = clean_name[start_idx:end_idx]
                                    clean_name = clean_name.replace(prefix, "").strip()
                                project.name = clean_name or subdir
                            
                            # プロジェクト説明にファイルパス情報を追加
                            if not project.description or project.description == "Excelからインポートされました":
                                project.description = f"サブディレクトリ '{subdir}' のファイル '{file_name}' からインポート"
                            else:
                                project.description += f"\n\nサブディレクトリ '{subdir}' のファイル '{file_name}' からインポート"
                            
                            result["success_count"] += 1
                            result["projects"].append(project)
                            import_result["status"] = "成功"
                            import_result["project_name"] = project.name
                            import_result["phase_count"] = len(project.get_phases())
                        else:
                            result["fail_count"] += 1
                            import_result["status"] = "失敗"
                            import_result["error"] = "インポートできませんでした（無効なフォーマットの可能性があります）"
                    except Exception as e:
                        result["fail_count"] += 1
                        import_result["status"] = "エラー"
                        import_result["error"] = str(e)
                        print(f"ファイル '{file_path}' のインポート中にエラーが発生: {str(e)}")
                    
                    result["details"].append(import_result)
            
            return result
            
        except Exception as e:
            result["error"] = f"一括インポート処理中にエラーが発生: {str(e)}"
            print(f"一括インポート処理中にエラーが発生: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return result
