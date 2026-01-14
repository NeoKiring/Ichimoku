"""
ログシステム
システム内の操作とエラーをログとして記録する機能
"""
import os
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union


class LogLevel:
    """ログレベルの定義"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionLogger:
    """
    アクションログとエラーログを記録するクラス
    システム内のすべての操作とエラーを時系列で記録する
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        ロガーの初期化
        
        Args:
            log_dir: ログファイルを保存するディレクトリ
        """
        self.log_dir = log_dir
        
        # ログディレクトリが存在しない場合は作成
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # エラーログディレクトリの作成
        self.error_log_dir = os.path.join(log_dir, "errors")
        if not os.path.exists(self.error_log_dir):
            os.makedirs(self.error_log_dir)
        
        # 基本ロガーの設定
        self.logger = logging.getLogger("project_manager")
        self.logger.setLevel(logging.DEBUG)
        
        # ハンドラがすでに設定されていないことを確認
        if not self.logger.handlers:
            # ログフォーマットの設定
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # ファイルハンドラの設定
            log_file = os.path.join(log_dir, f"actions_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # エラーログ用ファイルハンドラの設定
            error_log_file = os.path.join(self.error_log_dir, f"errors_{datetime.now().strftime('%Y%m%d')}.log")
            error_file_handler = logging.FileHandler(error_log_file, encoding='utf-8')
            error_file_handler.setFormatter(formatter)
            error_file_handler.setLevel(logging.WARNING)  # WARNING以上のみ記録
            self.logger.addHandler(error_file_handler)
            
            # コンソールハンドラの設定
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_action(self, action_type: str, entity_type: str, entity_id: str, 
                   details: Optional[Dict[str, Any]] = None, user: str = "system") -> None:
        """
        アクションをログに記録
        
        Args:
            action_type: アクションの種類 (create, update, delete など)
            entity_type: 操作対象のエンティティタイプ (Project, Phase, Process, Task)
            entity_id: 操作対象のエンティティID
            details: アクションの詳細情報（任意）
            user: アクションを実行したユーザー（デフォルトはシステム）
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user": user
        }
        
        if details:
            log_entry["details"] = details
        
        # 構造化ログとJSONログの両方を記録
        self.logger.info(f"{action_type} {entity_type} {entity_id} by {user}")
        
        # JSONログをファイルに追記
        json_log_file = os.path.join(self.log_dir, f"actions_{datetime.now().strftime('%Y%m%d')}.json")
        try:
            if os.path.exists(json_log_file):
                with open(json_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(json_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write JSON log: {str(e)}")
    
    def log_error(self, level: str, message: str, module: str, function: str, 
                  exception: Optional[Exception] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """
        エラーをログに記録
        
        Args:
            level: エラーのレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: エラーメッセージ
            module: エラーが発生したモジュール名
            function: エラーが発生した関数名
            exception: 発生した例外オブジェクト（任意）
            details: エラーの詳細情報（任意）
        """
        timestamp = datetime.now().isoformat()
        
        # スタックトレースを取得
        stack_trace = None
        if exception:
            stack_trace = traceback.format_exception(type(exception), exception, exception.__traceback__)
        
        # エラーエントリの作成
        error_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "module": module,
            "function": function,
            "stack_trace": stack_trace
        }
        
        if details:
            error_entry["details"] = details
        
        # ログレベルに応じたログ出力
        log_message = f"{message} in {module}.{function}"
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_message)
        
        # JSONエラーログをファイルに追記
        json_error_log_file = os.path.join(self.error_log_dir, f"errors_{datetime.now().strftime('%Y%m%d')}.json")
        try:
            if os.path.exists(json_error_log_file):
                with open(json_error_log_file, 'r', encoding='utf-8') as f:
                    error_logs = json.load(f)
            else:
                error_logs = []
            
            error_logs.append(error_entry)
            
            with open(json_error_log_file, 'w', encoding='utf-8') as f:
                json.dump(error_logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write JSON error log: {str(e)}")
    
    def get_entity_history(self, entity_type: str, entity_id: str) -> list:
        """
        特定のエンティティに関するアクション履歴を取得
        
        Args:
            entity_type: エンティティタイプ (Project, Phase, Process, Task)
            entity_id: エンティティID
            
        Returns:
            エンティティに関するアクション履歴のリスト
        """
        history = []
        
        # すべてのJSONログファイルを検索
        for filename in os.listdir(self.log_dir):
            if filename.startswith("actions_") and filename.endswith(".json"):
                file_path = os.path.join(self.log_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                        
                        # エンティティに関するログをフィルタリング
                        entity_logs = [log for log in logs if log["entity_type"] == entity_type and log["entity_id"] == entity_id]
                        history.extend(entity_logs)
                except Exception as e:
                    self.logger.error(f"Failed to read log file {filename}: {str(e)}")
        
        # タイムスタンプでソート
        history.sort(key=lambda x: x["timestamp"])
        return history
    
    def get_error_logs(self, level: Optional[str] = None, 
                      start_date: Optional[datetime] = None, 
                      end_date: Optional[datetime] = None,
                      module: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        エラーログを検索して取得
        
        Args:
            level: フィルタリングするエラーレベル（任意）
            start_date: 検索開始日時（任意）
            end_date: 検索終了日時（任意）
            module: フィルタリングするモジュール名（任意）
            limit: 取得する最大件数
            
        Returns:
            条件に一致するエラーログのリスト
        """
        error_logs = []
        
        # すべてのJSONエラーログファイルを検索
        for filename in os.listdir(self.error_log_dir):
            if filename.startswith("errors_") and filename.endswith(".json"):
                file_path = os.path.join(self.error_log_dir, filename)
                
                # ファイル名から日付を取得して日付フィルタリング
                file_date_str = filename.replace("errors_", "").replace(".json", "")
                try:
                    file_date = datetime.strptime(file_date_str, "%Y%m%d").date()
                    
                    # 日付フィルタリング
                    if start_date and file_date < start_date.date():
                        continue
                    if end_date and file_date > end_date.date():
                        continue
                    
                    # ファイル内のログを読み込み
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            logs = json.load(f)
                            
                            # 条件でフィルタリング
                            for log in logs:
                                # タイムスタンプフィルタリング
                                log_time = datetime.fromisoformat(log["timestamp"])
                                if start_date and log_time < start_date:
                                    continue
                                if end_date and log_time > end_date:
                                    continue
                                
                                # レベルフィルタリング
                                if level and log.get("level") != level:
                                    continue
                                
                                # モジュールフィルタリング
                                if module and log.get("module") != module:
                                    continue
                                
                                error_logs.append(log)
                                
                                # 上限に達したらループを終了
                                if len(error_logs) >= limit:
                                    break
                            
                            # 上限に達したらファイル処理を終了
                            if len(error_logs) >= limit:
                                break
                    except Exception as e:
                        self.logger.error(f"Failed to read error log file {filename}: {str(e)}")
                except ValueError:
                    # ファイル名のフォーマットが不正な場合はスキップ
                    continue
        
        # タイムスタンプでソート（新しい順）
        error_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 上限件数まで切り詰め
        return error_logs[:limit]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        エラーログの統計情報を取得
        
        Returns:
            エラーログの統計情報を含む辞書
        """
        statistics = {
            "total_errors": 0,
            "by_level": {},
            "by_module": {},
            "recent_errors": []
        }
        
        # ログファイルが存在しない場合は空の統計を返す
        if not os.path.exists(self.error_log_dir):
            return statistics
        
        # 直近の日付のエラーログファイルのみ処理
        error_log_files = [f for f in os.listdir(self.error_log_dir) if f.startswith("errors_") and f.endswith(".json")]
        error_log_files.sort(reverse=True)  # 新しい順にソート
        
        # 最近のエラーログファイルを処理（最大3ファイル）
        for filename in error_log_files[:3]:
            file_path = os.path.join(self.error_log_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    
                    # 統計情報を更新
                    statistics["total_errors"] += len(logs)
                    
                    for log in logs:
                        # レベル別統計
                        level = log.get("level", "UNKNOWN")
                        if level not in statistics["by_level"]:
                            statistics["by_level"][level] = 0
                        statistics["by_level"][level] += 1
                        
                        # モジュール別統計
                        module = log.get("module", "UNKNOWN")
                        if module not in statistics["by_module"]:
                            statistics["by_module"][module] = 0
                        statistics["by_module"][module] += 1
                        
                        # 最近のエラーを追加（最大10件）
                        if len(statistics["recent_errors"]) < 10:
                            # スタックトレースは長いので省略
                            log_copy = log.copy()
                            if "stack_trace" in log_copy:
                                del log_copy["stack_trace"]
                            statistics["recent_errors"].append(log_copy)
            except Exception as e:
                self.logger.error(f"Failed to read error log file {filename}: {str(e)}")
        
        return statistics


# シングルトンインスタンス
_logger = None


def get_logger() -> ActionLogger:
    """
    ActionLoggerのシングルトンインスタンスを取得
    
    Returns:
        ActionLoggerのインスタンス
    """
    global _logger
    if _logger is None:
        _logger = ActionLogger()
    return _logger
