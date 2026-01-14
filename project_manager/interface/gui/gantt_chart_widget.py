"""
ガントチャートウィジェット
プロジェクト管理システムのガントチャート表示機能を提供するウィジェット
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QFrame, QGridLayout, QToolBar, QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QRect, QDate, QRectF, QSize, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QWheelEvent, QMouseEvent, QPaintEvent

from ...models import ProjectStatus, TaskStatus


class GanttChartWidget(QWidget):
    """
    プロジェクトのガントチャートを表示するウィジェット
    """
    
    item_clicked = pyqtSignal(str, str)  # 項目がクリックされたときのシグナル (タイプ, ID)
    
    def __init__(self, parent=None):
        """
        ガントチャートウィジェットの初期化
        
        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        
        # ガントチャートのデータ
        self.project_data = None
        self.chart_data = []  # 表示するデータリスト
        
        # 表示設定
        self.start_date = datetime.now()
        self.end_date = datetime.now() + timedelta(days=90)  # デフォルトは90日間
        self.days_span = (self.end_date - self.start_date).days + 1
        self.row_height = 30
        self.time_scale = 20  # 1日あたりのピクセル数
        self.header_height = 50
        self.grid_color = QColor(180, 180, 180)
        self.weekend_color = QColor("#BFBFBF")  # 休日関連の色
        self.text_color = QColor("#2D2D2D")  # より暗く
        self.header_bg_color = QColor("#00A9E0")  # 日付欄の塗りつぶし
        self.header_text_color = QColor("#F4F4F4")  # 日付の数字の色
        self.month_bg_color = QColor("#C6F1FF")  # 年月表示欄の色
        self.month_text_color = QColor("#2D2D2D")  # 年月表示の文字色
        self.today_color = QColor(255, 0, 0, 150)
        
        # 色設定
        self.phase_color = QColor(60, 109, 197)  # より見やすい青
        self.process_color = QColor(20, 139, 73)  # より見やすい緑
        self.task_color = QColor(215, 125, 0)  # より見やすいオレンジ
        
        # タスク状態の色
        self.status_colors = {
            "未着手": QColor(130, 130, 130),
            "進行中": QColor(45, 85, 205),
            "完了": QColor(30, 185, 30),
            "中止": QColor(200, 0, 40),
            "保留": QColor(235, 195, 0),
            "対応不能": QColor(200, 0, 40)
        }
        
        # 折りたたみ状態の追加
        self.collapsed_items = set()
        
        # スクロール位置とズーム
        self.scroll_x = 0
        self.scroll_y = 0
        self.is_dragging = False
        self.last_mouse_pos = None
        
        # マウスイベント追跡のためのデータ
        self.hovered_item = None  # ホバー中のアイテム
        self.selected_item = None  # 選択中のアイテム
        
        self.setMouseTracking(True)  # マウス移動イベントを追跡
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # キーボードイベントを受け取るためのフォーカスポリシー
        
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        # レイアウトとウィジェットの配置は不要
        # paintEventで描画するため、最小サイズのみ設定
        self.setMinimumSize(800, 400)
    
    def set_project_data(self, project_data: Dict[str, Any]):
        """
        プロジェクトデータを設定し、ガントチャートを更新
        
        Args:
            project_data: プロジェクトデータ
        """
        self.project_data = project_data
        self.prepare_chart_data()
        self.update_date_range()
        self.update()
    
    def prepare_chart_data(self):
        """プロジェクトデータからガントチャート表示用のデータを準備"""
        self.chart_data = []
        
        if not self.project_data:
            return
        
        # プロジェクト自体を追加
        self.chart_data.append({
            "id": self.project_data["id"],
            "name": self.project_data["name"],
            "type": "project",
            "level": 0,
            "start_date": self.project_data.get("start_date"),
            "end_date": self.project_data.get("end_date"),
            "progress": self.project_data.get("progress", 0),
            "status": self.project_data.get("status", "")
        })
        
        # フェーズを追加
        for phase in self.project_data.get("phases", []):
            self.chart_data.append({
                "id": phase["id"],
                "name": phase["name"],
                "type": "phase",
                "level": 1,
                "start_date": phase.get("start_date"),
                "end_date": phase.get("end_date"),
                "progress": phase.get("progress", 0),
                "parent_id": self.project_data["id"]
            })
            
            # プロセスを追加
            for process in phase.get("processes", []):
                self.chart_data.append({
                    "id": process["id"],
                    "name": process["name"],
                    "type": "process",
                    "level": 2,
                    "start_date": process.get("start_date"),
                    "end_date": process.get("end_date"),
                    "progress": process.get("progress", 0),
                    "assignee": process.get("assignee", ""),
                    "parent_id": phase["id"]
                })
                
                # タスクを追加
                for task in process.get("tasks", []):
                    self.chart_data.append({
                        "id": task["id"],
                        "name": task["name"],
                        "type": "task",
                        "level": 3,
                        "status": task.get("status", "未着手"),
                        "created_at": task.get("created_at"),
                        "updated_at": task.get("updated_at"),
                        "parent_id": process["id"]
                    })
    
    def prepare_visible_data(self):
        """
        折りたたみ状態を考慮して表示するデータを準備
        """
        if not self.chart_data:
            return []
        
        visible_data = []
        i = 0
        
        while i < len(self.chart_data):
            item = self.chart_data[i]
            visible_data.append(item)
            i += 1
            
            # アイテムが折りたたまれている場合は子アイテムをスキップ
            if item["id"] in self.collapsed_items and item["type"] in ["project", "phase", "process"]:
                parent_id = item["id"]
                parent_level = item["level"]
                
                # 親レベルより低いレベルの項目をスキップ
                while i < len(self.chart_data) and self.chart_data[i]["level"] > parent_level:
                    i += 1
        
        return visible_data

    def update_date_range(self):
        """チャートの日付範囲を更新"""
        if not self.chart_data:
            return
        
        # 開始日と終了日を初期化
        min_date = None
        max_date = None
        
        # すべてのアイテムの日付を確認して範囲を決定
        for item in self.chart_data:
            start_date = item.get("start_date")
            end_date = item.get("end_date")
            
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date)
                
                if min_date is None or start_date < min_date:
                    min_date = start_date
            
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date)
                
                if max_date is None or end_date > max_date:
                    max_date = end_date
        
        # 日付が設定されていない場合のデフォルト値
        if min_date is None:
            min_date = datetime.now()
        if max_date is None:
            max_date = min_date + timedelta(days=90)  # デフォルトは90日間
        
        # データの開始日と終了日の前後に余白を追加
        margin_days = 7
        self.start_date = min_date - timedelta(days=margin_days)
        self.end_date = max_date + timedelta(days=margin_days)
        self.days_span = (self.end_date - self.start_date).days + 1
    
    def paintEvent(self, event: QPaintEvent):
        """
        ガントチャートを描画
        
        Args:
            event: 描画イベント
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景を描画
        painter.fillRect(event.rect(), Qt.GlobalColor.white)
        
        if not self.chart_data:
            # データがない場合はメッセージを表示
            painter.drawText(event.rect(), Qt.AlignmentFlag.AlignCenter, "プロジェクトデータがありません")
            return
        
        # 折りたたみ状態を考慮して表示するデータを取得
        visible_data = self.prepare_visible_data()
        
        # ビューの有効領域
        chart_width = self.days_span * self.time_scale
        chart_height = len(visible_data) * self.row_height
        
        # スクロール位置を適用
        painter.translate(-self.scroll_x, -self.scroll_y)
        
        # ヘッダー（日付）を描画
        self.draw_timeline_header(painter)
        
        # 項目名列を描画
        name_column_width = 200
        self.draw_name_column(painter, name_column_width)
        
        # グリッドと時間軸を描画
        painter.translate(name_column_width, self.header_height)
        self.draw_time_grid(painter, chart_width, chart_height)
        
        # ガントバーを描画（表示されるアイテムのみ）
        self.draw_gantt_bars(painter, chart_width, chart_height, visible_data)

    def draw_timeline_header(self, painter: QPainter):
        """
        タイムラインのヘッダー（日付）を描画
        
        Args:
            painter: QPainterオブジェクト
        """
        name_column_width = 200
        
        # ヘッダー背景
        header_rect = QRect(0, 0, self.width() + self.scroll_x, self.header_height)
        painter.fillRect(header_rect, self.header_bg_color)  # 日付欄の塗りつぶし
        
        # 項目名ヘッダー
        name_header_rect = QRect(0, 0, name_column_width, self.header_height)
        painter.fillRect(name_header_rect, QColor(220, 220, 220))
        painter.drawRect(name_header_rect)
        painter.drawText(name_header_rect, Qt.AlignmentFlag.AlignCenter, "項目名")
        
        # 日付ヘッダー
        painter.save()
        painter.translate(name_column_width, 0)
        
        # 日付の範囲を描画
        current_date = self.start_date
        day_count = 0
        last_month = -1  # 前の月を追跡するための変数
        
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        while current_date <= self.end_date:
            x = day_count * self.time_scale
            date_rect = QRect(x, 0, self.time_scale, self.header_height // 2)
            
            # 週末かどうかで背景色を変える
            if current_date.weekday() >= 5:  # 5=土曜日, 6=日曜日
                painter.fillRect(date_rect, self.weekend_color)
            
            # 日付を表示（各月の初日は「月/日」、それ以外は「日」のみ）
            painter.setPen(self.header_text_color)  # 日付の数字の色
            
            if current_date.day == 1 or current_date.month != last_month:
                # 月の初日または表示上の月の最初の日は「月/日」形式
                date_str = current_date.strftime("%m/%d")
            else:
                # その他の日は日付のみ
                date_str = current_date.strftime("%d")
            
            painter.drawText(date_rect, Qt.AlignmentFlag.AlignCenter, date_str)
            
            # 垂直線を描画
            if day_count > 0:
                painter.setPen(self.grid_color)
                painter.drawLine(x, 0, x, self.height())
            
            # 前月を更新
            last_month = current_date.month
            
            current_date += timedelta(days=1)
            day_count += 1
        
        # 月名を描画
        current_date = self.start_date
        last_month = current_date.month
        month_start_x = 0
        day_count = 0
        
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        while current_date <= self.end_date:
            x = day_count * self.time_scale
            
            if current_date.month != last_month or current_date == self.start_date:
                if current_date != self.start_date:
                    # 前の月の表示を完了
                    month_width = x - month_start_x
                    month_rect = QRect(month_start_x, self.header_height // 2, month_width, self.header_height // 2)
                    painter.fillRect(month_rect, self.month_bg_color)  # 年月表示欄の色
                    month_str = datetime(current_date.year, last_month, 1).strftime("%Y年%m月")
                    painter.setPen(self.month_text_color)  # 年月表示の文字色
                    painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, month_str)
                
                # 新しい月の開始
                month_start_x = x
                last_month = current_date.month
            
            current_date += timedelta(days=1)
            day_count += 1
        
        # 最後の月を描画
        month_width = day_count * self.time_scale - month_start_x
        month_rect = QRect(month_start_x, self.header_height // 2, month_width, self.header_height // 2)
        painter.fillRect(month_rect, self.month_bg_color)  # 年月表示欄の色
        month_str = datetime(current_date.year, last_month, 1).strftime("%Y年%m月")
        painter.setPen(self.month_text_color)  # 年月表示の文字色
        painter.drawText(month_rect, Qt.AlignmentFlag.AlignCenter, month_str)
        
        painter.restore()

    
    def draw_name_column(self, painter: QPainter, width: int):
        """
        項目名の列を描画
        
        Args:
            painter: QPainterオブジェクト
            width: 列の幅
        """
        painter.save()
        painter.translate(0, self.header_height)
        
        # 折りたたみ状態を考慮して表示するデータを取得
        visible_data = self.prepare_visible_data()
        
        # アイコン位置をリセット
        self.expandable_item_areas = {}
        
        for i, item in enumerate(visible_data):
            y = i * self.row_height
            indent = item["level"] * 20  # レベルに応じたインデント
            
            # 行の背景（交互に色を変える）
            if i % 2 == 1:
                row_rect = QRect(0, y, width, self.row_height)
                painter.fillRect(row_rect, QColor(248, 248, 248))
            
            # 選択されたアイテムの強調表示
            if self.selected_item and self.selected_item == item["id"]:
                highlight_rect = QRect(0, y, width, self.row_height)
                painter.fillRect(highlight_rect, QColor(220, 240, 255))
            
            # 折りたたみアイコン（プロジェクト、フェーズ、プロセスのみ）
            if item["type"] in ["project", "phase", "process"]:
                icon_size = 12
                icon_x = indent
                icon_y = y + (self.row_height - icon_size) // 2
                icon_rect = QRect(icon_x, icon_y, icon_size, icon_size)
                
                painter.setPen(QPen(self.text_color))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(icon_rect)
                
                # アイコン内の+または-の描画
                is_collapsed = item["id"] in self.collapsed_items
                
                # 横線
                h_line_y = icon_y + icon_size // 2
                painter.drawLine(icon_x + 2, h_line_y, icon_x + icon_size - 2, h_line_y)
                
                # 縦線（折りたたまれている場合のみ）
                if is_collapsed:
                    v_line_x = icon_x + icon_size // 2
                    painter.drawLine(v_line_x, icon_y + 2, v_line_x, icon_y + icon_size - 2)
                
                # アイコンがクリック可能であることを示すために、ID-アイコン位置マッピングを更新
                # 重要: この座標はheader_heightからの相対位置として保存
                self.expandable_item_areas[item["id"]] = icon_rect
                                
            # 項目名のアイコンとテキスト位置を調整
            if item["type"] in ["project", "phase", "process"]:
                marker_x = indent + 16  # 折りたたみアイコンの後
            else:
                marker_x = indent
            
            # アイコンまたはマーカー（タイプによって異なる）
            marker_size = 10
            marker_rect = QRect(marker_x + 2, y + (self.row_height - marker_size) // 2, marker_size, marker_size)
            
            if item["type"] == "project":
                painter.setBrush(QBrush(self.phase_color.darker(150)))
            elif item["type"] == "phase":
                painter.setBrush(QBrush(self.phase_color))
            elif item["type"] == "process":
                painter.setBrush(QBrush(self.process_color))
            elif item["type"] == "task":
                status = item.get("status", "未着手")
                painter.setBrush(QBrush(self.status_colors.get(status, QColor(180, 180, 180))))
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(marker_rect)
            painter.setPen(QPen(self.text_color))
            
            # 名前とレベルに基づいて描画
            font = painter.font()
            if item["level"] == 0:  # プロジェクト
                font.setBold(True)
                font.setPointSize(10)
            elif item["level"] == 1:  # フェーズ
                font.setBold(True)
                font.setPointSize(9)
            else:
                font.setBold(False)
                font.setPointSize(9)
            
            text_indent = marker_x + marker_size + 4
            name_rect = QRect(text_indent, y, width - text_indent, self.row_height)
            
            painter.setFont(font)
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter, item["name"])
            
            # 区切り線
            painter.setPen(self.grid_color)
            painter.drawLine(0, y + self.row_height, width, y + self.row_height)
        
        # 縦線
        painter.setPen(self.grid_color)
        painter.drawLine(width, 0, width, len(visible_data) * self.row_height)
        
        painter.restore()    


    def draw_time_grid(self, painter: QPainter, width: int, height: int):
        """
        時間グリッドを描画
        
        Args:
            painter: QPainterオブジェクト
            width: グリッドの幅
            height: グリッドの高さ
        """
        painter.save()
        
        # 横線（行の区切り）
        painter.setPen(self.grid_color)
        for i in range(len(self.chart_data) + 1):
            y = i * self.row_height
            painter.drawLine(0, y, width, y)
        
        # 縦線（日付の区切り）
        current_date = self.start_date
        day_count = 0
        
        while current_date <= self.end_date:
            x = day_count * self.time_scale
            
            # 週末の背景色
            if current_date.weekday() >= 5:  # 5=土曜日, 6=日曜日
                weekend_rect = QRect(x, 0, self.time_scale, height)
                painter.fillRect(weekend_rect, self.weekend_color)
            
            # 日付の区切り線
            painter.setPen(self.grid_color)
            painter.drawLine(x, 0, x, height)
            
            # 今日の日付を強調表示
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if current_date.date() == today.date():
                today_rect = QRect(x, 0, self.time_scale, height)
                painter.fillRect(today_rect, self.today_color)
                
                # 太い線で今日を強調
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.drawLine(x, 0, x, height)
            
            current_date += timedelta(days=1)
            day_count += 1
        
        painter.restore()
    
    def draw_gantt_bars(self, painter: QPainter, width: int, height: int, visible_data=None):
        """
        ガントチャートのバーを描画

        Args:
            painter: QPainterオブジェクト
            width: 描画領域の幅
            height: 描画領域の高さ
            visible_data: 表示するデータ（指定されない場合はchart_dataを使用）
        """

        painter.save()
        # 表示するデータが指定されていない場合は全データを使用
        if visible_data is None:
            visible_data = self.chart_data
        
        for i, item in enumerate(visible_data):
            y = i * self.row_height
            
            # 開始日と終了日を取得
            start_date = item.get("start_date")
            end_date = item.get("end_date")
            
            # 日付文字列をdatetimeに変換
            if start_date and isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if end_date and isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            
            # 開始日または終了日がない場合はバーを描画しない
            if not start_date or not end_date:
                continue
            
            # 開始位置と長さを計算
            days_from_start = (start_date - self.start_date).days
            duration_days = (end_date - start_date).days + 1
            
            if days_from_start < 0:
                # 開始日がチャートの開始日より前の場合
                duration_days += days_from_start  # 表示期間を短くする
                days_from_start = 0
            
            if duration_days <= 0:
                continue  # 表示期間がない場合はスキップ
            
            x = days_from_start * self.time_scale
            bar_width = duration_days * self.time_scale
            
            # バーの色を決定
            if item["type"] == "project":
                color = self.phase_color.darker(150)
            elif item["type"] == "phase":
                color = self.phase_color
            elif item["type"] == "process":
                color = self.process_color
            elif item["type"] == "task":
                status = item.get("status", "未着手")
                color = self.status_colors.get(status, QColor(180, 180, 180))
            
            # バーの高さ
            bar_height = self.row_height - 10
            bar_y = y + 5
            
            # 選択されたアイテムの強調表示
            if self.selected_item and self.selected_item == item["id"]:
                highlight_rect = QRect(x - 2, bar_y - 2, bar_width + 4, bar_height + 4)
                painter.setPen(QPen(QColor(0, 100, 195), 2))  # より暗く
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(highlight_rect)
            
            # バーを描画
            painter.setPen(QPen(color.darker(120)))
            painter.setBrush(QBrush(color))
            painter.drawRect(x, bar_y, bar_width, bar_height)
            
            # 進捗状況を表示（プロジェクト、フェーズ、プロセスの場合）
            if item["type"] in ["project", "phase", "process"]:
                progress = item.get("progress", 0)
                if progress > 0:
                    progress_width = int(bar_width * progress / 100)
                    progress_rect = QRect(x, bar_y, progress_width, bar_height)
                    progress_color = color.darker(130)
                    painter.fillRect(progress_rect, progress_color)
            
            # テキスト表示（バーの中に収まる場合のみ）
            if bar_width > 40:
                text_rect = QRect(x + 5, bar_y, bar_width - 10, bar_height)
                text = item["name"]
                
                # プロセスの場合は担当者も表示
                if item["type"] == "process" and item.get("assignee"):
                    text += f" ({item['assignee']})"
                
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)
        
        painter.restore()
    
    def wheelEvent(self, event: QWheelEvent):
        """
        ホイールイベント（スクロールとズーム）
        
        Args:
            event: ホイールイベント
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+ホイールでズームイン/アウト
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # 通常のスクロール
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+ホイールで水平スクロール
                delta = event.angleDelta().y()
                self.scroll_x += -delta // 2
                self.scroll_x = max(0, self.scroll_x)
            else:
                # 垂直スクロール
                delta = event.angleDelta().y()
                self.scroll_y += -delta // 2
                self.scroll_y = max(0, self.scroll_y)
                
                # スクロール範囲の制限
                max_scroll_y = len(self.chart_data) * self.row_height - self.height() + self.header_height
                self.scroll_y = min(max(0, self.scroll_y), max(0, max_scroll_y))
        
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        """
        マウスプレスイベント
        
        Args:
            event: マウスイベント
        """
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            pos_x = pos.x() + self.scroll_x
            pos_y = pos.y() + self.scroll_y
            
            # 項目名列内のクリックか判断
            name_column_width = 200
            if pos_x < name_column_width and pos_y > self.header_height:
                # 折りたたみアイコンエリアのチェック
                for item_id, rect in self.expandable_item_areas.items():
                    # icon_rectはheader_heightからのオフセットで保存されているので、
                    # クリック位置を同じ座標系に変換
                    y_in_items_area = pos_y - self.header_height
                    
                    # オリジナルの矩形と比較（スクロールは既にrectに含まれている）
                    if rect.contains(int(pos_x), int(y_in_items_area)):
                        # 折りたたみアイコンがクリックされた
                        self.toggle_item_collapse(item_id)
                        return
                
                # 項目全体のクリック処理
                item_index = self.get_item_at_position(pos_x, pos_y)
                if item_index >= 0:
                    visible_data = self.prepare_visible_data()
                    if item_index < len(visible_data):
                        item = visible_data[item_index]
                        self.selected_item = item["id"]
                        # クリックイベントを発行
                        self.item_clicked.emit(item["type"], item["id"])
                        self.update()
            
            # ドラッグ開始
            self.is_dragging = True
            self.last_mouse_pos = event.position()
        
        super().mousePressEvent(event)

    def toggle_item_collapse(self, item_id: str):
        """
        アイテムの折りたたみ状態を切り替え
        
        Args:
            item_id: 切り替えるアイテムのID
        """
        if item_id in self.collapsed_items:
            self.collapsed_items.remove(item_id)
        else:
            self.collapsed_items.add(item_id)
        
        self.update()


    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        マウスリリースイベント
        
        Args:
            event: マウスイベント
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        
        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """
        マウス移動イベント
        
        Args:
            event: マウスイベント
        """
        pos = event.position()
        
        if self.is_dragging and self.last_mouse_pos:
            # ドラッグでスクロール
            delta_x = int(pos.x() - self.last_mouse_pos.x())
            delta_y = int(pos.y() - self.last_mouse_pos.y())
            
            self.scroll_x -= delta_x
            self.scroll_y -= delta_y
            
            # スクロール範囲の制限
            self.scroll_x = max(0, self.scroll_x)
            
            max_scroll_y = len(self.chart_data) * self.row_height - self.height() + self.header_height
            self.scroll_y = min(max(0, self.scroll_y), max(0, max_scroll_y))
            
            self.last_mouse_pos = pos
            self.update()
        else:
            # ホバー効果
            item_index = self.get_item_at_position(pos.x(), pos.y())
            
            if item_index >= 0 and item_index < len(self.chart_data):
                if self.hovered_item != self.chart_data[item_index]["id"]:
                    self.hovered_item = self.chart_data[item_index]["id"]
                    self.update()
            elif self.hovered_item is not None:
                self.hovered_item = None
                self.update()
        
        super().mouseMoveEvent(event)

    def get_item_at_position(self, x: float, y: float) -> int:
        """
        指定座標にあるアイテムのインデックスを取得
        
        Args:
            x: X座標 (スクロール済み)
            y: Y座標 (スクロール済み)
            
        Returns:
            アイテムのインデックス。見つからない場合は-1
        """
        # ヘッダーより下の場合のみ
        if y < self.header_height:
            return -1
        
        # Y座標からアイテムのインデックスを計算
        # ヘッダーの高さを考慮した実際の項目エリア内での位置に変換
        item_index = int((y - self.header_height) / self.row_height)
        
        visible_data = self.prepare_visible_data()
        if 0 <= item_index < len(visible_data):
            return item_index
        
        return -1

    def zoom_in(self):
        """ズームイン（タイムスケールを拡大）"""
        self.time_scale = min(100, self.time_scale + 5)
        self.update()
    
    def zoom_out(self):
        """ズームアウト（タイムスケールを縮小）"""
        self.time_scale = max(5, self.time_scale - 5)
        self.update()
    
    def fit_content(self):
        """すべての内容が表示されるようにズームを調整"""
        if not self.chart_data:
            return
            
        # チャートの全体の幅を計算
        width = self.width() - 200  # 名前列の幅を引く
        
        # 必要なタイムスケールを計算
        self.time_scale = max(5, width // self.days_span)
        self.update()
