"""
エラーハンドリングユーティリティ
システム全体で一貫したエラーハンドリングを提供
"""
import functools
import inspect
import sys
import traceback
from typing import Callable, Any, Optional, Dict, Type, Union

from .logger import get_logger, LogLevel


class ErrorHandler:
    """
    エラーハンドリングを一元管理するクラス
    デコレータとユーティリティ関数を提供
    """
    
    @staticmethod
    def get_caller_info():
        """
        呼び出し元の情報を取得
        
        Returns:
            (モジュール名, 関数名)のタプル
        """
        frame = inspect.currentframe().f_back.f_back
        module = inspect.getmodule(frame)
        module_name = module.__name__ if module else "unknown"
        function_name = frame.f_code.co_name
        return module_name, function_name
    
    @staticmethod
    def log_exception(exception: Exception, message: str = None, level: str = LogLevel.ERROR, 
                      details: Dict[str, Any] = None):
        """
        例外をログに記録
        
        Args:
            exception: 例外オブジェクト
            message: カスタムエラーメッセージ（任意）
            level: ログレベル（デフォルトはERROR）
            details: 追加の詳細情報（任意）
        """
        logger = get_logger()
        
        if message is None:
            message = str(exception)
        
        module_name, function_name = ErrorHandler.get_caller_info()
        
        logger.log_error(
            level=level,
            message=message,
            module=module_name,
            function=function_name,
            exception=exception,
            details=details
        )
    
    @staticmethod
    def handle_exception(exception: Exception, message: str = None, 
                         level: str = LogLevel.ERROR, reraise: bool = False, 
                         details: Dict[str, Any] = None) -> None:
        """
        例外をハンドリングしてログに記録
        
        Args:
            exception: 例外オブジェクト
            message: カスタムエラーメッセージ（任意）
            level: ログレベル（デフォルトはERROR）
            reraise: 例外を再送出するかどうか
            details: 追加の詳細情報（任意）
        """
        ErrorHandler.log_exception(exception, message, level, details)
        
        if reraise:
            raise exception
    
    @staticmethod
    def with_error_logging(func: Optional[Callable] = None, *, 
                          level: str = LogLevel.ERROR, 
                          reraise: bool = True,
                          exclude_exceptions: Optional[Union[Type[Exception], tuple]] = None):
        """
        関数呼び出しをエラーログ記録でラップするデコレータ
        
        Args:
            func: デコレート対象の関数
            level: ログレベル（デフォルトはERROR）
            reraise: 例外を再送出するかどうか
            exclude_exceptions: ログに記録しない例外タイプ
            
        Returns:
            デコレートされた関数
        """
        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    # 除外例外かどうかチェック
                    if exclude_exceptions and isinstance(e, exclude_exceptions):
                        # 除外例外の場合は単に再送出
                        if reraise:
                            raise
                        return None
                    
                    # モジュール名と関数名を取得
                    module_name = fn.__module__
                    function_name = fn.__name__
                    
                    # 引数情報を抽出（機密情報に注意）
                    arg_names = fn.__code__.co_varnames[:fn.__code__.co_argcount]
                    arg_dict = {}
                    
                    # self引数は除外
                    start_idx = 1 if len(arg_names) > 0 and arg_names[0] == 'self' else 0
                    
                    # 引数情報を構築（深すぎる階層や循環参照を避けるため単純化）
                    for i, arg_name in enumerate(arg_names[start_idx:], start_idx):
                        if i < len(args):
                            # 位置引数
                            arg_value = args[i]
                            # 単純な型のみ詳細を記録
                            if isinstance(arg_value, (str, int, float, bool)) or arg_value is None:
                                arg_dict[arg_name] = arg_value
                            else:
                                arg_dict[arg_name] = f"{type(arg_value).__name__} object"
                        else:
                            # キーワード引数
                            if arg_name in kwargs:
                                arg_value = kwargs[arg_name]
                                # 単純な型のみ詳細を記録
                                if isinstance(arg_value, (str, int, float, bool)) or arg_value is None:
                                    arg_dict[arg_name] = arg_value
                                else:
                                    arg_dict[arg_name] = f"{type(arg_value).__name__} object"
                    
                    # 詳細情報を構築
                    details = {
                        "args": arg_dict,
                        "exception_type": type(e).__name__
                    }
                    
                    # エラーをログに記録
                    message = f"Exception in {function_name}: {str(e)}"
                    get_logger().log_error(
                        level=level,
                        message=message,
                        module=module_name,
                        function=function_name,
                        exception=e,
                        details=details
                    )
                    
                    # 例外の再送出
                    if reraise:
                        raise
                    return None
            return wrapper
        
        # デコレータとして直接使用された場合
        if func is not None:
            return decorator(func)
        
        # パラメータ付きデコレータとして使用された場合
        return decorator


# グローバル関数として提供
def log_exception(exception: Exception, message: str = None, level: str = LogLevel.ERROR, 
                 details: Dict[str, Any] = None):
    """
    例外をログに記録するショートカット関数
    
    Args:
        exception: 例外オブジェクト
        message: カスタムエラーメッセージ（任意）
        level: ログレベル（デフォルトはERROR）
        details: 追加の詳細情報（任意）
    """
    ErrorHandler.log_exception(exception, message, level, details)


def handle_exception(exception: Exception, message: str = None, 
                    level: str = LogLevel.ERROR, reraise: bool = False, 
                    details: Dict[str, Any] = None):
    """
    例外をハンドリングしてログに記録するショートカット関数
    
    Args:
        exception: 例外オブジェクト
        message: カスタムエラーメッセージ（任意）
        level: ログレベル（デフォルトはERROR）
        reraise: 例外を再送出するかどうか
        details: 追加の詳細情報（任意）
    """
    ErrorHandler.handle_exception(exception, message, level, reraise, details)


def with_error_logging(level: str = LogLevel.ERROR, reraise: bool = True,
                      exclude_exceptions: Optional[Union[Type[Exception], tuple]] = None):
    """
    関数呼び出しをエラーログ記録でラップするデコレータ
    
    Args:
        level: ログレベル（デフォルトはERROR）
        reraise: 例外を再送出するかどうか
        exclude_exceptions: ログに記録しない例外タイプ
        
    Returns:
        デコレートされた関数
    """
    return ErrorHandler.with_error_logging(
        level=level, 
        reraise=reraise, 
        exclude_exceptions=exclude_exceptions
    )
