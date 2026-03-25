import os
import logging
from collections import deque
from datetime import datetime
from PySide6.QtWidgets import QWidget, QTextEdit, QFileDialog, QMessageBox
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QFont, QTextCursor, QTextCharFormat

class _Logger(QObject):
    """日志处理"""

    # 定义一个比 CRITICAL 更高的级别
    ENDPOINT = 60
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "ENDPOINT": ENDPOINT
    }
    
    log_signal = Signal(str, int)  # message, level
    file_handler = None

    def __init__(self,):
        super().__init__()
        self.log_signal.connect(self._log)

        # 配置日志器
        logging.addLevelName(self.ENDPOINT, "ENDPOINT")
        self.logger = logging.getLogger('disk_logger')
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # 避免输出到控制台

        # 日志文件路径
        self.log_file = "current.log"

        # 最大显示行数
        self.max_display_lines = 5000

    def bind(self, log_text: QTextEdit):
        """初始化日志管理器
        
        Args:
            log_text: QTextEdit日志显示控件
        """
        self.log_text = log_text

    def reset_log_file(self):
        # 删除日志文件
        self.delete_log()

        # 添加文件 Handler（输出日志到文件）
        self.file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter('[ %(asctime)s ] [ %(levelname)s ] %(message)s')
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def refresh_display(self):
        """从文件读取最近的日志，过滤级别，只显示最多5000条"""
        self.log_text.clear()
        lines = deque(maxlen=self.max_display_lines)
        total_lines = 0

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    total_lines += 1
                    if self.line_matches_level(line.strip()):
                        lines.append(line.strip())

            # 如果总行数 > max_display_lines，在顶部添加提示
            if total_lines > self.max_display_lines:
                fmt = QTextCharFormat()
                self.log_text.setCurrentCharFormat(fmt)
                self.log_text.append(">>>>>>>>>>>>>>>>>>>>>>更早日志请点击保存日志按钮后查看。\n")

            # 显示过滤后的最近行
            for line in lines:
                level = self.extract_level_from_line(line)
                self._append_colored_log(line, level)

            # 滚动到底部
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
        except Exception as e:
            print(f"读取日志失败: {str(e)}")

    def extract_level_from_line(self, line: str):
        """从格式化后的日志行中提取级别数值"""
        for name, level_val in self.level_map.items():
            if f" ] [ {name} ]" in line:
                return level_val
        return None

    def set_print_level(self, print_level_str: str):
        """设置日志打印级别"""
        print_level_str = print_level_str.upper()
        
        level = self.level_map.get(print_level_str)
        if level:
            self.current_level = level
            self.refresh_display()
    
    def line_matches_level(self, line: str) -> bool:
        """判断一行日志是否符合当前级别"""
        for level_str, level_val in self.level_map.items():
            if f" ] [ {level_str} ]" in line:  # 根据格式匹配级别
                return level_val >= self.current_level
        return False  # 无法匹配时不显示

    def debug(self, message: str):
        self.log_signal.emit(message, logging.DEBUG)

    def info(self, message: str):
        self.log_signal.emit(message, logging.INFO)
        
    def warn(self, message: str):
        self.log_signal.emit(message, logging.WARNING)

    def error(self, message: str):
        self.log_signal.emit(message, logging.ERROR)

    def endpoint(self, message: str):
        self.log_signal.emit(message, self.ENDPOINT)
    
    def _log(self, message: str, level: int):
        self.logger.log(level, message)
        self._add_log(message, level)
    
    def delete_log(self):
        """删除日志文件"""
        if self.file_handler:
            self.file_handler.flush()
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)
            self.file_handler = None

        if os.path.exists(self.log_file):
            os.remove(self.log_file)
    
    def save_log_to_file(self, parent: QWidget, log_time: datetime = None):
        """保存日志到文件"""
        
        # 检查源文件是否存在
        from pathlib import Path
        src_path = Path(self.log_file)
        if not src_path.exists():
            QMessageBox.information(None, "提示", "尚未产生日志。")
            return
        
        # 生成默认文件名：log_{日期和时间}.txt
        if log_time:
            timestamp = log_time.strftime('%Y%m%d_%H%M%S')
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"log_{timestamp}.txt"
        
        # 弹出文件保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "保存日志",
            default_filename,
            "文本文件 (*.txt)"
        )
        
        if file_path:
            try:
                # 复制完整文件（shutil.copyfile 比手动读写更快）
                from shutil import copyfile
                dest_path = Path(file_path)
                copyfile(src_path, dest_path)
                
                # 显示成功消息
                print(f"日志已保存到：{file_path}")
            except Exception as e:
                print(f"保存日志失败：{str(e)}")

    def _append_colored_log(self, text: str, level: int = logging.INFO):
        """向 QTextEdit 追加带颜色的文本"""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)

        # 设置文本格式
        fmt = QTextCharFormat()

        if level == logging.ERROR:
            fmt.setForeground(QColor("red"))
            fmt.setFontWeight(QFont.Bold)
        elif level == logging.WARNING:
            fmt.setForeground(QColor("orange"))
        elif level == self.ENDPOINT:
            fmt.setForeground(QColor("green"))
        elif level == logging.DEBUG:
            fmt.setForeground(QColor("pink"))

        self.log_text.setCurrentCharFormat(fmt)
        self.log_text.insertPlainText(text + "\n")

    def _add_log(self, message: str, level: int = logging.INFO):
        """添加日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        if level < self.current_level:
            return
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        
        # 设置文本格式
        fmt = QTextCharFormat()

        if level == logging.ERROR:
            level_str = "ERROR"
            fmt.setForeground(QColor("red"))
        elif level == logging.WARNING:
            level_str = "WARNING"
            fmt.setForeground(QColor("orange"))
        elif level == self.ENDPOINT:
            level_str = "ENDPOINT"
            fmt.setForeground(QColor("green"))
        elif level == logging.DEBUG:
            level_str = "DEBUG"
            fmt.setForeground(QColor("pink"))
        else:
            level_str = "INFO"
            # 普通日志使用默认格式（继承编辑器主题颜色）
            fmt = QTextCharFormat()
        
        # timestamp = datetime.now().isoformat()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

        self.log_text.setCurrentCharFormat(fmt)
        self.log_text.insertPlainText(f"[ {timestamp} ][ {level_str} ] {message}\n")

Logger = _Logger()