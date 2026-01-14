@echo off
setlocal enabledelayedexpansion

REM ===================================================================
REM プロジェクト管理システム 実行バッチファイル
REM ===================================================================
REM 機能: プロジェクト管理システムをGUIモードまたはCLIモードで起動します
REM 使用方法: このバッチファイルをダブルクリックして実行してください
REM 作成日: 2025-04-11
REM ===================================================================

title プロジェクト管理システム

REM 依存関係のチェック
echo 環境チェックを実行しています...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo エラー: Pythonがインストールされていません。
    echo Python 3.8以上をインストールしてください。
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

REM データディレクトリとログディレクトリの設定
set DATA_DIR=data
set LOG_DIR=logs

REM データディレクトリが存在しない場合は作成
if not exist %DATA_DIR% (
    echo データディレクトリを作成しています...
    mkdir %DATA_DIR%
)

REM ログディレクトリが存在しない場合は作成
if not exist %LOG_DIR% (
    echo ログディレクトリを作成しています...
    mkdir %LOG_DIR%
)

:MENU
cls
echo ===================================================================
echo                    プロジェクト管理システム
echo ===================================================================
echo.
echo 実行モードを選択してください:
echo.
echo  [1] GUIモード（グラフィカルインターフェース）
echo  [2] CLIモード（コマンドラインインターフェース）
echo  [3] 設定の変更
echo  [4] 終了
echo.
set /p OPTION="選択 (1-4): "

if "%OPTION%"=="1" goto GUI
if "%OPTION%"=="2" goto CLI
if "%OPTION%"=="3" goto SETTINGS
if "%OPTION%"=="4" goto EOF

echo 無効な選択です。もう一度お試しください。
timeout /t 2 >nul
goto MENU

:GUI
cls
echo GUIモードを起動しています...
echo.
echo PyQt6が必要です。インストールされていない場合はインストールされます。
echo.

REM PyQt6のチェックとインストール
python -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo PyQt6をインストールしています...
    pip install PyQt6 >nul
    if %errorlevel% neq 0 (
        echo エラー: PyQt6のインストールに失敗しました。
        echo 手動でインストールしてください: pip install PyQt6
        pause
        goto MENU
    )
    echo PyQt6がインストールされました。
)

echo プロジェクト管理システムを起動しています（GUIモード）...
echo ウィンドウが表示されるまでお待ちください...
echo.
echo 終了するには、アプリケーションウィンドウを閉じてください。
echo.

python project_manager/main.py --gui --data-dir %DATA_DIR% --log-dir %LOG_DIR%

echo.
echo GUIモードが終了しました。
timeout /t 3 >nul
goto MENU

:CLI
cls
echo CLIモードを起動しています...
echo.
echo プロジェクト管理システムを起動しています（CLIモード）...
echo.
echo CLIモードでの操作方法:
echo  - help: コマンド一覧を表示
echo  - quit または exit: CLIモードを終了
echo.
echo CLIモードを終了すると、このメニューに戻ります。
echo.
pause

python project_manager/main.py --data-dir %DATA_DIR% --log-dir %LOG_DIR%

echo.
echo CLIモードが終了しました。
timeout /t 3 >nul
goto MENU

:SETTINGS
cls
echo ===================================================================
echo                         設定の変更
echo ===================================================================
echo.
echo 現在の設定:
echo  データディレクトリ: %DATA_DIR%
echo  ログディレクトリ: %LOG_DIR%
echo.
echo 設定を変更しますか？
echo  [1] データディレクトリの変更
echo  [2] ログディレクトリの変更
echo  [3] 設定をリセット
echo  [4] メニューに戻る
echo.
set /p SETTING_OPTION="選択 (1-4): "

if "%SETTING_OPTION%"=="1" (
    set /p NEW_DATA_DIR="新しいデータディレクトリ名: "
    if not "!NEW_DATA_DIR!"=="" (
        set DATA_DIR=!NEW_DATA_DIR!
        if not exist !DATA_DIR! mkdir !DATA_DIR!
        echo データディレクトリを !DATA_DIR! に変更しました。
    )
    timeout /t 2 >nul
    goto SETTINGS
)

if "%SETTING_OPTION%"=="2" (
    set /p NEW_LOG_DIR="新しいログディレクトリ名: "
    if not "!NEW_LOG_DIR!"=="" (
        set LOG_DIR=!NEW_LOG_DIR!
        if not exist !LOG_DIR! mkdir !LOG_DIR!
        echo ログディレクトリを !LOG_DIR! に変更しました。
    )
    timeout /t 2 >nul
    goto SETTINGS
)

if "%SETTING_OPTION%"=="3" (
    set DATA_DIR=data
    set LOG_DIR=logs
    echo 設定をリセットしました。
    timeout /t 2 >nul
    goto SETTINGS
)

if "%SETTING_OPTION%"=="4" goto MENU

echo 無効な選択です。もう一度お試しください。
timeout /t 2 >nul
goto SETTINGS

:EOF
cls
echo プロジェクト管理システムを終了します。
echo ご利用ありがとうございました。
timeout /t 2 >nul
endlocal
exit /b 0
