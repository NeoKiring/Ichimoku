# 技術引継ぎ資料：プロジェクト管理システム（Ichimoku）
## PyQt6からPySide6への移行

---

## 📋 目次

1. [システム概要](#1-システム概要)
2. [システムアーキテクチャ](#2-システムアーキテクチャ)
3. [ディレクトリ構成](#3-ディレクトリ構成)
4. [実装済み機能一覧](#4-実装済み機能一覧)
5. [データモデル詳細](#5-データモデル詳細)
6. [GUI実装詳細](#6-gui実装詳細)
7. [PyQt6からPySide6への移行情報](#7-pyqt6からpyside6への移行情報)
8. [主要クラスと責務](#8-主要クラスと責務)
9. [外部依存関係](#9-外部依存関係)
10. [注意点とベストプラクティス](#10-注意点とベストプラクティス)

---

## 1. システム概要

### 1.1 プロジェクト名
**Ichimoku** - プロジェクト管理システム

### 1.2 目的
プロジェクト、フェーズ、プロセス、タスクの4階層構造による進捗管理システム。
ガントチャートによる視覚的なスケジュール管理、Excel連携、エラーログ管理、通知機能を備える。

### 1.3 開発言語・フレームワーク
- **言語**: Python 3.8以上
- **現在のGUIフレームワーク**: PyQt6（移行元）
- **移行先GUIフレームワーク**: PySide6
- **Excel処理**: openpyxl
- **データ永続化**: JSON（ファイルベース）

### 1.4 インターフェース
- **GUIモード**: PyQt6ベースのマルチタブインターフェース（移行対象）
- **CLIモード**: cmd.Cmdベースのインタラクティブシェル（移行不要）

### 1.5 コード統計
- **総Pythonファイル数**: 38ファイル
- **総コード行数**: 約13,496行
- **GUI関連コード**: 約6,642行（PyQt6依存）
- **PyQt6依存ファイル**: 14ファイル

---

## 2. システムアーキテクチャ

### 2.1 アーキテクチャパターン
**MVC（Model-View-Controller）パターン**を採用

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACES                          │
├──────────────────────┬──────────────────┬────────────────────┤
│  GUI (PyQt6)         │  CLI (cmd.Cmd)   │  Entry Point       │
│  ▼ PySide6へ移行     │  ✓ 移行不要      │  ✓ 移行不要        │
├──────────────────────┼──────────────────┼────────────────────┤
│ • MainWindow         │ • Interactive    │ • Argument Parser  │
│ • Dialogs (6種類)    │   Commands       │ • Mode Router      │
│ • Tabs (6種類)       │ • Command Loop   │                    │
│ • Custom Widgets     │ • Help System    │                    │
└──────────────────────┴──────────────────┴────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              CONTROLLER LAYER                                │
│              ▼ PyQt6 Signal/Slot の移行が必要               │
├─────────────────────────────────────────────────────────────┤
│ • GUIController (PyQt6 signals/slots bridge)                │
│ • Signal emission on data changes                           │
│ • Data transformation for UI display                        │
│   - pyqtSignal → Signal への変更が必要                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              BUSINESS LOGIC LAYER                            │
│              ✓ 移行不要（Pure Python）                       │
├─────────────────────────────────────────────────────────────┤
│ ProjectManager (Core):                                       │
│ • Project CRUD operations                                   │
│ • Phase management                                          │
│ • Process management                                        │
│ • Task management                                           │
│ • Error handling decorators                                 │
│ • Logging integration                                       │
│                                                             │
│ Supporting Services:                                        │
│ • NotificationManager - Alert generation & management       │
│ • Logger - Audit trail & error logging                      │
│ • ErrorHandler - Decorator-based error capturing            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              DATA MODEL LAYER                                │
│              ✓ 移行不要（Pure Python）                       │
├─────────────────────────────────────────────────────────────┤
│ Hierarchical Structure:                                      │
│ • Project (root) → contains multiple Phases                 │
│ • Phase → contains multiple Processes                       │
│ • Process → contains multiple Tasks                         │
│ • Task → terminal entity with status tracking               │
│ • Notification → independent entity                         │
│ • All entities inherit from BaseEntity                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              DATA ACCESS LAYER                               │
│              ✓ 移行不要（Pure Python）                       │
├─────────────────────────────────────────────────────────────┤
│ DataStore (File-based persistence):                         │
│ • JSON file storage                                         │
│ • Project serialization/deserialization                     │
│ • Excel import/export (openpyxl)                            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 適用されているデザインパターン

| パターン | 適用箇所 | 目的 |
|---------|---------|------|
| **Singleton** | ProjectManager, Logger | 単一インスタンスの保証 |
| **MVC** | 全体構造 | ビジネスロジックとUIの分離 |
| **Observer** | GUIController（PyQt6 Signals/Slots） | イベント駆動型UI更新 |
| **Decorator** | error_handler.py | エラーハンドリングの横断的関心事 |
| **Factory** | data_store.py | データストアの生成 |
| **Template Method** | BaseEntity | 共通処理の抽象化 |
| **Strategy** | Excel Importer | フォーマット別処理の切り替え |

---

## 3. ディレクトリ構成

```
/home/user/Ichimoku/
├── README.md                        # プロジェクトREADME
├── run_project_manager.bat          # Windows用起動スクリプト（181行）
├── 技術引継ぎ資料_PyQt6からPySide6への移行.md  # 本資料
├── 変更履歴.md                      # 変更履歴（別途作成）
│
└── project_manager/                 # メインアプリケーションパッケージ
    ├── __init__.py
    ├── main.py                      # エントリーポイント（83行）
    │                                # ▼ 移行: 76行目のエラーメッセージ
    │
    ├── core/                        # コアビジネスロジック（✓ 移行不要）
    │   ├── __init__.py
    │   ├── manager.py               # ProjectManager（812行）
    │   ├── logger.py                # ログシステム（360行）
    │   ├── error_handler.py         # エラーハンドラ（221行）
    │   └── notification_manager.py  # 通知システム（470行）
    │
    ├── model/                       # データモデル（✓ 移行不要）
    │   ├── __init__.py
    │   ├── base.py                  # BaseEntity抽象クラス（116行）
    │   ├── project.py               # Projectモデル（213行）
    │   ├── phase.py                 # Phaseモデル
    │   ├── process.py               # Processモデル（200行）
    │   ├── task.py                  # Taskモデル
    │   └── notification.py          # Notificationモデル
    │
    ├── interface/                   # ユーザーインターフェース
    │   ├── __init__.py
    │   ├── cli.py                   # CLIインターフェース（✓ 移行不要、1189行）
    │   │
    │   └── gui/                     # GUIコンポーネント（▼ 移行対象）
    │       ├── __init__.py
    │       ├── app.py               # アプリ起動（▼ 移行必要）
    │       ├── main_window.py        # メインウィンドウ（▼ 移行必要、1998行）
    │       ├── controller.py         # GUIコントローラ（▼ 移行必要、701行）
    │       ├── utils.py             # GUI共通ユーティリティ（▼ 移行必要、204行）
    │       │
    │       ├── dialogs/             # ダイアログ（全6ファイル、▼ 移行必要）
    │       │   ├── project_dialog.py    # プロジェクト作成/編集
    │       │   ├── phase_dialog.py      # フェーズ作成/編集
    │       │   ├── process_dialog.py    # プロセス作成/編集
    │       │   ├── task_dialog.py       # タスク作成/編集
    │       │   ├── excel_dialog.py      # Excelインポート/エクスポート
    │       │   └── bulk_excel_dialog.py # 一括Excel読込
    │       │
    │       ├── gantt_chart_widget.py   # ガントチャートウィジェット（▼ 移行必要、821行）
    │       ├── gantt_chart_tab.py      # ガントチャートタブ（▼ 移行必要、491行）
    │       ├── error_log_tab.py        # エラーログタブ（▼ 移行必要、626行）
    │       └── notification_tab.py     # 通知タブ（▼ 移行必要、632行）
    │
    ├── storage/                     # データ永続化（✓ 移行不要）
    │   ├── __init__.py
    │   └── data_store.py            # JSONファイルストア（379行）
    │
    ├── excel/                       # Excel連携（✓ 移行不要）
    │   ├── __init__.py
    │   ├── excel_importer.py        # インポーター（1035行）
    │   ├── excel_exporter.py        # エクスポーター
    │   ├── bulk_excel_importer.py   # 一括インポーター
    │   └── excel_utils.py           # ユーティリティ（1035行）
    │
    └── logs/                        # 実行時ログ（動的生成）
```

### 3.1 移行対象ファイル一覧（14ファイル）

| # | ファイルパス | 説明 | PyQt6使用箇所 |
|---|-------------|------|--------------|
| 1 | `interface/gui/app.py` | アプリ起動 | QApplication, QIcon |
| 2 | `interface/gui/main_window.py` | メインウィンドウ（最大ファイル、1998行） | 多数のウィジェット + pyqtSignal |
| 3 | `interface/gui/controller.py` | GUIコントローラ | QObject, pyqtSignal |
| 4 | `interface/gui/utils.py` | GUI共通ユーティリティ | QMessageBox, QWidget |
| 5 | `interface/gui/project_dialog.py` | ダイアログ | QDialog系 |
| 6 | `interface/gui/phase_dialog.py` | ダイアログ | QDialog系 |
| 7 | `interface/gui/process_dialog.py` | ダイアログ | QDialog系 |
| 8 | `interface/gui/task_dialog.py` | ダイアログ | QDialog系 |
| 9 | `interface/gui/excel_dialog.py` | ダイアログ | QDialog系 |
| 10 | `interface/gui/bulk_excel_dialog.py` | ダイアログ | QDialog系 |
| 11 | `interface/gui/gantt_chart_widget.py` | カスタムウィジェット（821行） | QPainter, QWheelEvent等 |
| 12 | `interface/gui/gantt_chart_tab.py` | タブ | 各種ウィジェット |
| 13 | `interface/gui/error_log_tab.py` | タブ | 各種ウィジェット |
| 14 | `interface/gui/notification_tab.py` | タブ | 各種ウィジェット |

---

## 4. 実装済み機能一覧

### 4.1 プロジェクト管理機能

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **作成** | プロジェクト名、説明を入力して新規作成 | `ProjectManager.create_project()` |
| **読込** | 既存プロジェクトの読み込み | `ProjectManager.load_project()` |
| **編集** | プロジェクト情報の更新 | `ProjectManager.update_project()` |
| **削除** | プロジェクトの削除（カスケード削除） | `ProjectManager.delete_project()` |
| **状態管理** | 未着手/進行中/完了/中止/保留 | `Project.update_status()` |
| **自動保存** | 30秒ごとの自動保存 | `MainWindow.auto_save_project()` |
| **進捗計算** | 子要素の進捗に基づく自動計算 | `Project.calculate_progress()` |
| **状態自動判定** | 進捗に基づく状態自動決定 | `Project.determine_status()` |

### 4.2 フェーズ管理機能

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **追加** | プロジェクトへのフェーズ追加 | `ProjectManager.add_phase()` |
| **編集** | フェーズ情報（名前、説明、終了日）の更新 | `ProjectManager.update_phase()` |
| **削除** | フェーズの削除（子プロセス・タスクも削除） | `ProjectManager.delete_phase()` |
| **進捗計算** | 子プロセスの進捗に基づく計算 | `Phase.calculate_progress()` |
| **日付追跡** | 開始日・終了日の追跡 | `Phase.start_date`, `Phase.end_date` |

### 4.3 プロセス管理機能

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **追加** | フェーズへのプロセス追加 | `ProjectManager.add_process()` |
| **編集** | プロセス情報の更新 | `ProjectManager.update_process()` |
| **削除** | プロセスの削除（子タスクも削除） | `ProjectManager.delete_process()` |
| **担当者割当** | チームメンバーの割り当て | `Process.assignee` |
| **工数管理** | 見積時間 vs 実績時間の追跡 | `Process.estimated_hours`, `Process.actual_hours` |
| **進捗計算** | タスクのステータスに基づく計算 | `Process.calculate_progress()` |
| **全プロセス一覧** | 全プロジェクトのプロセスを統合表示 | `MainWindow.all_processes_tab` |

### 4.4 タスク管理機能

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **追加** | プロセスへのタスク追加 | `ProjectManager.add_task()` |
| **編集** | タスク情報の更新 | `ProjectManager.update_task()` |
| **削除** | タスクの削除 | `ProjectManager.delete_task()` |
| **状態追跡** | 未着手/進行中/完了/進行不可 | `Task.status` |
| **履歴管理** | タスク変更履歴の記録 | `Task.history` |
| **コンテキストメニュー** | 右クリックによる状態変更 | `MainWindow.show_task_context_menu()` |

### 4.5 GUI機能

#### 4.5.1 メインウィンドウ（MainWindow）

| タブ | 機能 | 主要ウィジェット |
|-----|------|----------------|
| **プロジェクト一覧** | 全プロジェクトの閲覧 | QTableWidget |
| **プロジェクト詳細** | 階層的なツリービュー | QTreeWidget |
| **ガントチャート** | 視覚的なスケジュール管理 | カスタムウィジェット |
| **全プロセス一覧** | 全プロセスの統合表示 | QTableWidget |
| **エラーログ** | システムエラーの追跡 | QTableWidget |
| **通知** | アラートと警告の表示 | カスタムウィジェット |

#### 4.5.2 ダイアログ（6種類）

| ダイアログ | 目的 | 主要機能 |
|-----------|------|---------|
| **ProjectDialog** | プロジェクト作成/編集 | 名前、説明、状態の入力 |
| **PhaseDialog** | フェーズ作成/編集 | 名前、説明、終了日の入力 |
| **ProcessDialog** | プロセス作成/編集 | 名前、担当者、日付、工数の入力 |
| **TaskDialog** | タスク作成/編集 | 名前、説明、状態の入力 |
| **ExcelDialog** | Excel連携 | インポート/エクスポート |
| **BulkExcelDialog** | 一括インポート | 複数プロジェクトの一括読込 |

#### 4.5.3 カスタムウィジェット

| ウィジェット | 機能 | 技術的特徴 |
|-------------|------|-----------|
| **GanttChartWidget** | ガントチャート描画 | QPainterによるカスタム描画、マウスホイールズーム |
| **プログレスバー** | 進捗率の視覚化 | 色分け表示（0-33%: 赤、34-66%: 黄、67-100%: 緑） |
| **ステータスインジケータ** | 状態の色分け表示 | QColorによる動的色付け |

### 4.6 ガントチャート機能

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **タイムライン描画** | プロジェクトスケジュールの視覚化 | `GanttChartWidget.paintEvent()` |
| **色分け表示** | タスク状態による色分け | `GanttChartWidget.get_task_color()` |
| **マウスホイールズーム** | 拡大縮小機能 | `GanttChartWidget.wheelEvent()` |
| **日付範囲フィルタ** | 表示期間の絞り込み | `GanttChartTab.filter_by_date_range()` |
| **マイルストーン追跡** | 重要期日の表示 | ウィジェット内で実装 |

### 4.7 Excel連携機能

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **インポート** | Excelからプロジェクトデータを読込 | `ExcelImporter.import_project()` |
| **エクスポート** | プロジェクトデータをExcelへ出力 | `ExcelExporter.export_project()` |
| **フォーマット検出** | 複数形式の自動検出 | `ExcelImporter.detect_format()` |
| **一括インポート** | 複数プロジェクトの一括読込 | `BulkExcelImporter.import_projects()` |
| **日付自動解析** | 日付形式の自動変換 | `ExcelUtils.parse_date()` |
| **ステータス解析** | ステータス文字列の自動判定 | `ExcelUtils.parse_status()` |

対応フォーマット：
- **標準形式**: システム独自フォーマット
- **MS Projectフォーマット**: Microsoft Project互換
- **シンプル形式**: 簡易フォーマット

### 4.8 ログとエラーハンドリング

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **アクション監査ログ** | 作成/更新/削除操作の記録 | `Logger.log_action()` |
| **エラーログ** | システムエラーの記録 | `Logger.log_error()` |
| **デコレータベース** | エラーハンドリングの自動適用 | `@with_error_logging` |
| **エラーログビューア** | GUIでのエラー閲覧 | `ErrorLogTab` |
| **フィルタリング** | エラーレベル別フィルタ | `ErrorLogTab.filter_logs()` |
| **エンティティ変更履歴** | データ変更の履歴追跡 | `Logger.log_entity_change()` |

### 4.9 通知システム

| 機能 | 詳細 | 実装場所 |
|-----|------|---------|
| **期限接近警告** | 期限までの日数に基づく警告 | `NotificationManager.check_deadlines()` |
| **進捗閾値アラート** | 進捗率に基づくアラート | `NotificationManager.check_progress()` |
| **未読通知追跡** | 未読通知のカウント | `NotificationManager.unread_count` |
| **優先度レベル** | 通知の重要度分類 | `Notification.priority` |
| **自動消去** | 古い通知の自動削除 | `NotificationManager.auto_dismiss()` |
| **スケジュール生成** | 定期的な通知チェック | `NotificationTab.refresh_timer` |

### 4.10 CLI機能（移行不要）

| コマンド | 機能 | 実装場所 |
|---------|------|---------|
| `list` | プロジェクト一覧表示 | `ProjectManagerCLI.do_list()` |
| `create` | 新規作成 | `ProjectManagerCLI.do_create()` |
| `open` | プロジェクトを開く | `ProjectManagerCLI.do_open()` |
| `status` | ステータスレポート | `ProjectManagerCLI.do_status()` |
| `export` | データエクスポート | `ProjectManagerCLI.do_export()` |
| `help` | ヘルプシステム | cmd.Cmd組み込み |

---

## 5. データモデル詳細

### 5.1 階層構造

```
Project (プロジェクト)
  ├── Phase (フェーズ) × N
  │     ├── Process (プロセス) × N
  │     │     ├── Task (タスク) × N
  │     │     └── Task × N
  │     └── Process × N
  └── Phase × N

Notification (通知) - 独立したエンティティ
```

### 5.2 BaseEntity（基底クラス）

**ファイル**: `project_manager/model/base.py`

**プロパティ**:
- `id: str` - UUID（自動生成）
- `name: str` - 名前
- `description: str` - 説明
- `created_at: datetime` - 作成日時
- `updated_at: datetime` - 更新日時
- `parent: BaseEntity` - 親エンティティ
- `children: List[BaseEntity]` - 子エンティティリスト

**メソッド**:
- `update(name, description)` - 基本情報更新
- `add_child(child)` - 子要素追加
- `remove_child(child_id)` - 子要素削除
- `find_child(child_id)` - 子要素検索
- `to_dict()` - 辞書変換
- `from_dict(data)` - 辞書から復元（抽象メソッド）

### 5.3 Project（プロジェクト）

**ファイル**: `project_manager/model/project.py`

**追加プロパティ**:
- `status: ProjectStatus` - プロジェクト状態（Enum）
- `is_status_manual: bool` - 手動状態設定フラグ

**ProjectStatus（列挙型）**:
- `NOT_STARTED` - 未着手
- `IN_PROGRESS` - 進行中
- `COMPLETED` - 完了
- `CANCELLED` - 中止
- `ON_HOLD` - 保留

**主要メソッド**:
- `add_phase(phase)` - フェーズ追加
- `remove_phase(phase_id)` - フェーズ削除
- `update_status(status, manual)` - 状態更新
- `determine_status()` - 状態自動判定
- `calculate_progress()` - 進捗率計算（0〜100）
- `get_start_date()` - 開始日取得
- `get_end_date()` - 終了日取得

### 5.4 Phase（フェーズ）

**ファイル**: `project_manager/model/phase.py`

**追加プロパティ**:
- `end_date: Optional[datetime]` - 終了予定日

**主要メソッド**:
- `add_process(process)` - プロセス追加
- `remove_process(process_id)` - プロセス削除
- `calculate_progress()` - 進捗率計算
- `get_start_date()` - 最も早いプロセスの開始日
- `get_end_date()` - 最も遅いプロセスの終了日

### 5.5 Process（プロセス）

**ファイル**: `project_manager/model/process.py`

**追加プロパティ**:
- `assignee: str` - 担当者
- `start_date: Optional[datetime]` - 開始日
- `end_date: Optional[datetime]` - 終了日
- `estimated_hours: float` - 見積時間
- `actual_hours: float` - 実績時間
- `progress: float` - 進捗率（0〜100、手動入力）

**主要メソッド**:
- `add_task(task)` - タスク追加
- `remove_task(task_id)` - タスク削除
- `calculate_progress()` - タスク完了率に基づく計算
- `update_hours(estimated, actual)` - 工数更新

### 5.6 Task（タスク）

**ファイル**: `project_manager/model/task.py`

**追加プロパティ**:
- `status: TaskStatus` - タスク状態（Enum）
- `history: List[Dict]` - 変更履歴

**TaskStatus（列挙型）**:
- `NOT_STARTED` - 未着手
- `IN_PROGRESS` - 進行中
- `COMPLETED` - 完了
- `UNABLE_TO_PROCEED` - 進行不可

**主要メソッド**:
- `update_status(status)` - 状態更新（履歴記録）
- `get_history()` - 変更履歴取得

### 5.7 Notification（通知）

**ファイル**: `project_manager/model/notification.py`

**プロパティ**:
- `id: str` - UUID
- `title: str` - タイトル
- `message: str` - メッセージ
- `priority: str` - 優先度（high/medium/low）
- `is_read: bool` - 既読フラグ
- `created_at: datetime` - 作成日時
- `related_entity_id: Optional[str]` - 関連エンティティID

**主要メソッド**:
- `mark_as_read()` - 既読にする
- `mark_as_unread()` - 未読にする

---

## 6. GUI実装詳細

### 6.1 メインウィンドウ（MainWindow）

**ファイル**: `project_manager/interface/gui/main_window.py` (1998行)

**構成要素**:

```python
class MainWindow(QMainWindow):
    def __init__(self, controller: GUIController):
        # コントローラとの接続
        self.controller = controller

        # シグナル接続（▼ 移行時にSignalへ変更）
        self.controller.project_changed.connect(self.refresh_project_view)
        self.controller.phases_changed.connect(self.refresh_phases_view)
        self.controller.processes_changed.connect(self.refresh_processes_view)
        self.controller.tasks_changed.connect(self.refresh_tasks_view)

        # 自動保存タイマー
        self.save_timer = QTimer(self)
        self.save_timer.setInterval(30000)  # 30秒
        self.save_timer.timeout.connect(self.auto_save_project)
```

**主要メソッド**:
- `init_ui()` - UI初期化
- `init_menu()` - メニューバー初期化
- `init_toolbar()` - ツールバー初期化
- `init_statusbar()` - ステータスバー初期化
- `setup_projects_tab()` - プロジェクト一覧タブ
- `setup_project_detail_tab()` - プロジェクト詳細タブ
- `setup_all_processes_tab()` - 全プロセスタブ
- `load_projects()` - プロジェクト一覧読込
- `refresh_*_view()` - 各ビューのリフレッシュ

### 6.2 GUIコントローラ（GUIController）

**ファイル**: `project_manager/interface/gui/controller.py` (701行)

**役割**: ビジネスロジック（ProjectManager）とGUI（MainWindow）の橋渡し

**シグナル定義**（▼ 移行時に`Signal`へ変更）:

```python
from PyQt6.QtCore import QObject, pyqtSignal

class GUIController(QObject):
    # ▼ PySide6では: from PySide6.QtCore import Signal
    project_changed = pyqtSignal()      # → Signal()
    phases_changed = pyqtSignal()       # → Signal()
    processes_changed = pyqtSignal()    # → Signal()
    tasks_changed = pyqtSignal()        # → Signal()
```

**主要メソッド**:
- `create_project(name, description)` - プロジェクト作成
- `load_project(project_id)` - プロジェクト読込
- `update_project(...)` - プロジェクト更新
- `add_phase(...)` - フェーズ追加
- `update_phase(...)` - フェーズ更新
- `add_process(...)` - プロセス追加
- `add_task(...)` - タスク追加

### 6.3 ガントチャートウィジェット（GanttChartWidget）

**ファイル**: `project_manager/interface/gui/gantt_chart_widget.py` (821行)

**技術的特徴**:
- `QPainter`による完全カスタム描画
- `QWheelEvent`によるマウスホイールズーム
- `QMouseEvent`によるマウス操作
- `QPaintEvent`による再描画

**主要描画処理**:

```python
def paintEvent(self, event: QPaintEvent):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # タイムライン描画
    self.draw_timeline(painter)

    # ガントバー描画
    self.draw_gantt_bars(painter)

    # マイルストーン描画
    self.draw_milestones(painter)
```

**色分けロジック**:
- 未着手: グレー
- 進行中: 青
- 完了: 緑
- 進行不可: 赤

### 6.4 エラーログタブ（ErrorLogTab）

**ファイル**: `project_manager/interface/gui/error_log_tab.py` (626行)

**機能**:
- エラーログの一覧表示
- エラーレベル別フィルタリング
- 日付範囲フィルタリング
- エラー詳細の表示

### 6.5 通知タブ（NotificationTab）

**ファイル**: `project_manager/interface/gui/notification_tab.py` (632行)

**機能**:
- 通知の一覧表示
- 優先度別色分け
- 未読/既読の切り替え
- 通知の自動生成（タイマー）
- 期限接近警告の設定

### 6.6 ダイアログ実装パターン

**共通パターン**:

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox
from PyQt6.QtCore import Qt

class SomeDialog(QDialog):
    def __init__(self, parent=None, initial_data=None):
        super().__init__(parent)

        self.setWindowTitle("タイトル")
        self.setModal(True)

        # レイアウト構築
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # フォーム要素追加
        # ...

        # OK/Cancelボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(button_box)

    def get_data(self) -> Dict[str, Any]:
        """入力データを取得"""
        return {...}
```

---

## 7. PyQt6からPySide6への移行情報

### 7.1 移行が必要な理由

- ライセンスの違い: PyQt6はGPL、PySide6はLGPL（より柔軟）
- Qt公式サポート: PySide6はQt Companyの公式Python実装
- 互換性: APIはほぼ同一、移行は比較的容易

### 7.2 主要な変更点

#### 7.2.1 インポート文の変更

| PyQt6 | PySide6 |
|-------|---------|
| `from PyQt6.QtWidgets import ...` | `from PySide6.QtWidgets import ...` |
| `from PyQt6.QtCore import ...` | `from PySide6.QtCore import ...` |
| `from PyQt6.QtGui import ...` | `from PySide6.QtGui import ...` |

#### 7.2.2 シグナル/スロットの変更

| PyQt6 | PySide6 |
|-------|---------|
| `from PyQt6.QtCore import pyqtSignal` | `from PySide6.QtCore import Signal` |
| `from PyQt6.QtCore import pyqtSlot` | `from PySide6.QtCore import Slot` |
| `signal_name = pyqtSignal()` | `signal_name = Signal()` |
| `signal_name = pyqtSignal(int, str)` | `signal_name = Signal(int, str)` |

**移行例**:

```python
# PyQt6版
from PyQt6.QtCore import QObject, pyqtSignal

class GUIController(QObject):
    project_changed = pyqtSignal()
    data_updated = pyqtSignal(str, int)

# PySide6版
from PySide6.QtCore import QObject, Signal

class GUIController(QObject):
    project_changed = Signal()
    data_updated = Signal(str, int)
```

### 7.3 移行対象ファイルと変更内容

#### 7.3.1 最優先ファイル（Signal使用ファイル）

| ファイル | 変更箇所 | 変更内容 |
|---------|---------|---------|
| `controller.py` | 8行目 | `from PyQt6.QtCore import pyqtSignal` → `from PySide6.QtCore import Signal` |
| | 13-16行目 | `pyqtSignal()` → `Signal()` に全置換 |
| `main_window.py` | 15行目 | `from PyQt6.QtCore import pyqtSignal` → `from PySide6.QtCore import Signal` |
| `gantt_chart_widget.py` | 12行目 | `pyqtSignal` → `Signal` |
| `gantt_chart_tab.py` | 11行目 | `pyqtSignal` → `Signal` |
| `error_log_tab.py` | 14行目 | `pyqtSignal` → `Signal` |
| `notification_tab.py` | 12行目 | `pyqtSignal` → `Signal` |

#### 7.3.2 インポート変更のみのファイル

| ファイル | 変更内容 |
|---------|---------|
| `app.py` | `PyQt6` → `PySide6` に全置換 |
| `utils.py` | `PyQt6` → `PySide6` に全置換 |
| `project_dialog.py` | `PyQt6` → `PySide6` に全置換 |
| `phase_dialog.py` | `PyQt6` → `PySide6` に全置換 |
| `process_dialog.py` | `PyQt6` → `PySide6` に全置換 |
| `task_dialog.py` | `PyQt6` → `PySide6` に全置換 |
| `excel_dialog.py` | `PyQt6` → `PySide6` に全置換 |
| `bulk_excel_dialog.py` | `PyQt6` → `PySide6` に全置換 |

#### 7.3.3 その他の変更

| ファイル | 行番号 | 変更内容 |
|---------|-------|---------|
| `main.py` | 76 | エラーメッセージ内の"PyQt6"を"PySide6"に変更 |
| `run_project_manager.bat` | 73 | `python -c "import PyQt6"` → `import PySide6` |

### 7.4 一括置換スクリプト（推奨手順）

**ステップ1**: 全ファイルでインポート文を置換

```bash
# Linuxコマンド例
find project_manager/interface/gui -name "*.py" -exec sed -i 's/from PyQt6/from PySide6/g' {} +
```

**ステップ2**: pyqtSignal/pyqtSlotを置換

```bash
find project_manager/interface/gui -name "*.py" -exec sed -i 's/pyqtSignal/Signal/g' {} +
find project_manager/interface/gui -name "*.py" -exec sed -i 's/pyqtSlot/Slot/g' {} +
```

**ステップ3**: main.pyのエラーメッセージを修正

```python
# 修正前（76行目）
print("PyQt6をインストールしてください: pip install PyQt6")

# 修正後
print("PySide6をインストールしてください: pip install PySide6")
```

**ステップ4**: run_project_manager.batを修正

```batch
REM 修正前（73行目）
python -c "import PyQt6" >nul 2>&1

REM 修正後
python -c "import PySide6" >nul 2>&1
```

### 7.5 互換性の注意点

#### 7.5.1 完全互換な要素（変更不要）

- ウィジェットクラス（QWidget, QPushButton, QLabel等）
- レイアウト（QVBoxLayout, QHBoxLayout等）
- イベントハンドラ（mousePressEvent等）
- 列挙型（Qt.AlignmentFlag等）
- 描画関連（QPainter, QColor等）

#### 7.5.2 非互換の可能性がある要素

| 項目 | PyQt6 | PySide6 | 対処法 |
|-----|-------|---------|-------|
| **シグナルの接続** | 通常互換 | 通常互換 | テストで確認 |
| **スロットの自動接続** | 動作異なる場合あり | 動作異なる場合あり | 明示的接続を推奨 |
| **列挙型のアクセス** | 時々異なる | 時々異なる | ドキュメント確認 |

### 7.6 移行後のテスト項目

#### 7.6.1 機能テスト

- [ ] アプリケーション起動
- [ ] プロジェクト作成/編集/削除
- [ ] フェーズ/プロセス/タスク操作
- [ ] ガントチャート表示
- [ ] Excel インポート/エクスポート
- [ ] エラーログ表示
- [ ] 通知機能
- [ ] 自動保存

#### 7.6.2 UIテスト

- [ ] ダイアログの表示と動作
- [ ] コンテキストメニュー
- [ ] ツールバー/メニューバー
- [ ] タブ切り替え
- [ ] プログレスバー表示
- [ ] カラースキームの適用

#### 7.6.3 イベントテスト

- [ ] シグナル/スロットの接続
- [ ] マウスイベント（クリック、ホイール）
- [ ] キーボードイベント
- [ ] タイマーイベント（自動保存）
- [ ] リサイズイベント

---

## 8. 主要クラスと責務

### 8.1 コアクラス

| クラス | ファイル | 行数 | 責務 |
|-------|---------|------|------|
| **ProjectManager** | `core/manager.py` | 812 | プロジェクト管理のコアロジック |
| **Logger** | `core/logger.py` | 360 | ログ記録とアクション監査 |
| **ErrorHandler** | `core/error_handler.py` | 221 | デコレータベースのエラー処理 |
| **NotificationManager** | `core/notification_manager.py` | 470 | 通知生成と管理 |

### 8.2 GUIクラス（移行対象）

| クラス | ファイル | 行数 | 責務 |
|-------|---------|------|------|
| **MainWindow** | `interface/gui/main_window.py` | 1998 | メインウィンドウとタブ管理 |
| **GUIController** | `interface/gui/controller.py` | 701 | GUI-ビジネスロジックブリッジ |
| **GanttChartWidget** | `interface/gui/gantt_chart_widget.py` | 821 | ガントチャートの描画 |
| **ErrorLogTab** | `interface/gui/error_log_tab.py` | 626 | エラーログビューア |
| **NotificationTab** | `interface/gui/notification_tab.py` | 632 | 通知管理UI |
| **GanttChartTab** | `interface/gui/gantt_chart_tab.py` | 491 | ガントチャートタブ |

### 8.3 データストレージクラス

| クラス | ファイル | 行数 | 責務 |
|-------|---------|------|------|
| **DataStore** | `storage/data_store.py` | 379 | JSONベースのデータ永続化 |

### 8.4 Excelクラス

| クラス | ファイル | 行数 | 責務 |
|-------|---------|------|------|
| **ExcelImporter** | `excel/excel_importer.py` | 1035 | Excel読み込み |
| **ExcelExporter** | `excel/excel_exporter.py` | - | Excel書き出し |
| **ExcelUtils** | `excel/excel_utils.py` | 1035 | Excel関連ユーティリティ |

### 8.5 クラス間の依存関係

```
MainWindow
  ├── depends on → GUIController
  │                  └── depends on → ProjectManager
  │                                      ├── depends on → DataStore
  │                                      ├── depends on → Logger
  │                                      ├── depends on → NotificationManager
  │                                      └── uses → ErrorHandler (decorator)
  ├── contains → ProjectDialog
  ├── contains → PhaseDialog
  ├── contains → ProcessDialog
  ├── contains → TaskDialog
  ├── contains → ExcelDialog
  ├── contains → BulkExcelDialog
  ├── contains → GanttChartTab
  │                └── contains → GanttChartWidget
  ├── contains → ErrorLogTab
  └── contains → NotificationTab
```

---

## 9. 外部依存関係

### 9.1 Python標準ライブラリ

| モジュール | 用途 |
|-----------|------|
| `sys` | システム操作 |
| `os` | OS操作 |
| `pathlib` | パス操作 |
| `uuid` | UUID生成 |
| `datetime` | 日時処理 |
| `enum` | 列挙型 |
| `typing` | 型ヒント |
| `cmd` | CLIシェル |
| `json` | JSON処理 |
| `argparse` | コマンドライン引数 |

### 9.2 外部パッケージ

| パッケージ | バージョン | 用途 | 移行での影響 |
|-----------|----------|------|-------------|
| **PyQt6** | 6.x | GUIフレームワーク | ❌ アンインストール |
| **PySide6** | 6.x | GUIフレームワーク | ✅ 新規インストール |
| **openpyxl** | 3.x | Excel操作 | ✅ 影響なし |

### 9.3 インストールコマンド

**移行前の削除**:
```bash
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
```

**移行後のインストール**:
```bash
pip install PySide6 openpyxl
```

**requirements.txt（移行後）**:
```
PySide6>=6.0.0
openpyxl>=3.0.0
```

---

## 10. 注意点とベストプラクティス

### 10.1 移行作業の注意点

#### 10.1.1 開発環境の準備

1. **バックアップの作成**
   - 移行前に必ずGitコミットまたはバックアップを取る
   - ブランチを作成して移行作業を行う

2. **仮想環境の使用**
   - PyQt6とPySide6が混在しないよう、新しい仮想環境を作成
   ```bash
   python -m venv venv_pyside6
   source venv_pyside6/bin/activate  # Windows: venv_pyside6\Scripts\activate
   pip install PySide6 openpyxl
   ```

3. **段階的な移行**
   - 一度に全ファイルを変更せず、モジュール単位でテスト
   - controller.py → dialogs → main_window.py の順に推奨

#### 10.1.2 移行中のトラブルシューティング

| 問題 | 原因 | 解決策 |
|-----|------|-------|
| **インポートエラー** | パッケージ名の変更漏れ | `PyQt6`を`PySide6`に全置換 |
| **シグナルエラー** | pyqtSignalの変更漏れ | `pyqtSignal`を`Signal`に全置換 |
| **実行時エラー** | 混在インストール | 仮想環境を作り直す |
| **表示崩れ** | 列挙型アクセスの違い | PySide6ドキュメントで確認 |

#### 10.1.3 テストの実施

1. **単体テスト**
   - 各ダイアログが正常に開くか
   - データの入力・取得が正常に動作するか

2. **統合テスト**
   - MainWindowが正常に起動するか
   - タブ切り替えが正常に動作するか
   - シグナル/スロットが正常に接続されているか

3. **エンドツーエンドテスト**
   - プロジェクト作成から削除まで一連の操作
   - Excelインポート/エクスポート
   - ガントチャート表示

### 10.2 コーディング規約

#### 10.2.1 命名規則

- **クラス名**: PascalCase（例: `ProjectManager`, `MainWindow`）
- **関数名**: snake_case（例: `create_project`, `load_data`）
- **定数**: UPPER_SNAKE_CASE（例: `MAX_RETRY`, `DEFAULT_TIMEOUT`）
- **プライベートメソッド**: `_`プレフィックス（例: `_internal_method`）

#### 10.2.2 ドキュメンテーション

- すべてのクラスとメソッドにdocstringを記述
- 日本語で記述（現在のコードと統一）
- パラメータと戻り値を明記

```python
def update_project(self, name: Optional[str] = None,
                  description: Optional[str] = None) -> bool:
    """
    プロジェクト情報を更新

    Args:
        name: 新しいプロジェクト名（省略時は変更なし）
        description: 新しい説明（省略時は変更なし）

    Returns:
        更新が成功した場合True、失敗した場合False
    """
```

#### 10.2.3 型ヒント

- すべての関数パラメータと戻り値に型ヒントを記述
- `Optional`, `List`, `Dict`等を積極的に使用

```python
from typing import Optional, List, Dict, Any

def get_phases(self) -> List[Phase]:
    return self.children

def to_dict(self) -> Dict[str, Any]:
    return {...}
```

### 10.3 パフォーマンスの考慮事項

#### 10.3.1 大規模データの扱い

- プロジェクト数が100を超える場合、ページネーションを検討
- ガントチャートの描画は表示範囲に限定
- Excel読込は非同期処理を検討

#### 10.3.2 メモリ管理

- 不要なウィジェットは適切に破棄（`deleteLater()`）
- 大きなデータをキャッシュしない
- イベントハンドラの適切な切断

### 10.4 セキュリティの注意点

#### 10.4.1 ファイル操作

- ユーザー入力パスの検証
- ディレクトリトラバーサル攻撃の防止
- Excel読込時のファイル検証

#### 10.4.2 データ永続化

- JSONファイルのパーミッション設定
- 機密情報の平文保存を避ける
- バックアップファイルの管理

### 10.5 今後の拡張性

#### 10.5.1 推奨される改善

1. **データベース化**
   - 現在: JSONファイル
   - 推奨: SQLite または PostgreSQL
   - メリット: パフォーマンス向上、クエリの柔軟性

2. **非同期処理の導入**
   - 現在: 同期処理
   - 推奨: QThread または asyncio
   - メリット: UIのフリーズ防止

3. **設定ファイルの外部化**
   - 現在: ハードコード
   - 推奨: config.ini または YAML
   - メリット: カスタマイズ性向上

4. **ユニットテストの追加**
   - 現在: テストなし
   - 推奨: pytest + Qt Test
   - メリット: リファクタリングの安全性

#### 10.5.2 将来の機能追加候補

- ユーザー認証・権限管理
- マルチプロジェクトの並行管理
- ネットワーク経由のデータ共有
- レポート生成機能
- ダッシュボード機能

### 10.6 ドキュメント管理

#### 10.6.1 更新すべきドキュメント

- [ ] README.mdの更新（インストール手順）
- [ ] 変更履歴.mdの記録
- [ ] APIドキュメントの生成（Sphinx推奨）
- [ ] ユーザーマニュアルの作成

#### 10.6.2 コードコメント

- 複雑なロジックには必ずコメント
- TODOコメントの活用
- WARNINGコメントでリスクを明示

---

## 📌 移行チェックリスト

### 準備フェーズ

- [ ] Gitバックアップの作成
- [ ] 新しい仮想環境の構築
- [ ] PySide6のインストール
- [ ] 依存パッケージのインストール確認

### 移行フェーズ

- [ ] `controller.py`の移行とテスト
- [ ] 全ダイアログファイルの移行
- [ ] `main_window.py`の移行
- [ ] カスタムウィジェットの移行
- [ ] タブコンポーネントの移行
- [ ] `utils.py`の移行
- [ ] `app.py`の移行

### テストフェーズ

- [ ] アプリケーション起動テスト
- [ ] 全機能の動作確認
- [ ] エラーログの確認
- [ ] パフォーマンステスト

### 完了フェーズ

- [ ] README.mdの更新
- [ ] 変更履歴.mdの更新
- [ ] PyQt6のアンインストール
- [ ] 最終コミット

---

## 📞 サポート・問い合わせ

移行作業中に不明点が発生した場合:

1. **公式ドキュメント**
   - PySide6: https://doc.qt.io/qtforpython/
   - PyQt6 to PySide6: https://wiki.qt.io/Qt_for_Python_Migration_Guide

2. **コミュニティ**
   - Stack Overflow (タグ: pyside6)
   - Qt Forum

3. **本プロジェクトについて**
   - Githubリポジトリのissue

---

## 📝 付録

### 付録A: PyQt6とPySide6の完全対応表

| 機能 | PyQt6 | PySide6 |
|-----|-------|---------|
| シグナル | pyqtSignal | Signal |
| スロット | pyqtSlot | Slot |
| プロパティ | pyqtProperty | Property |
| バウンドシグナル | - | SignalInstance |

### 付録B: よく使うウィジェットの対応

| ウィジェット | 対応状況 | 備考 |
|------------|---------|------|
| QMainWindow | ✅ 完全互換 | |
| QWidget | ✅ 完全互換 | |
| QPushButton | ✅ 完全互換 | |
| QLabel | ✅ 完全互換 | |
| QTableWidget | ✅ 完全互換 | |
| QTreeWidget | ✅ 完全互換 | |
| QDialog | ✅ 完全互換 | |
| QPainter | ✅ 完全互換 | カスタム描画 |

### 付録C: ファイル一覧（移行状況管理用）

| # | ファイル | 行数 | 移行状態 | 担当者 | 完了日 |
|---|---------|------|---------|-------|-------|
| 1 | controller.py | 701 | ⬜️ 未着手 | | |
| 2 | main_window.py | 1998 | ⬜️ 未着手 | | |
| 3 | project_dialog.py | - | ⬜️ 未着手 | | |
| 4 | phase_dialog.py | - | ⬜️ 未着手 | | |
| 5 | process_dialog.py | - | ⬜️ 未着手 | | |
| 6 | task_dialog.py | - | ⬜️ 未着手 | | |
| 7 | excel_dialog.py | - | ⬜️ 未着手 | | |
| 8 | bulk_excel_dialog.py | - | ⬜️ 未着手 | | |
| 9 | gantt_chart_widget.py | 821 | ⬜️ 未着手 | | |
| 10 | gantt_chart_tab.py | 491 | ⬜️ 未着手 | | |
| 11 | error_log_tab.py | 626 | ⬜️ 未着手 | | |
| 12 | notification_tab.py | 632 | ⬜️ 未着手 | | |
| 13 | utils.py | 204 | ⬜️ 未着手 | | |
| 14 | app.py | - | ⬜️ 未着手 | | |

---

**作成日**: 2026-01-14
**作成者**: システム移行チーム
**バージョン**: 1.0
**対象システム**: Ichimoku プロジェクト管理システム
**移行元**: PyQt6
**移行先**: PySide6

---

**この資料は、PyQt6からPySide6への移行作業を行う開発者が、システムの全体像を理解し、効率的に移行作業を進めるための包括的なガイドです。不明点がある場合は、随時更新・追記してください。**
