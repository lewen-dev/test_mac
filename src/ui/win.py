from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, QTextEdit, QFileDialog, QGroupBox

from info import __version__, __app_name__
from config.user import UserConfig
from process import ProcessThread
from log import Logger

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(__app_name__)
        self.setMinimumSize(700, 700)
        
        self.process_thread = None
        self.latest_end_time = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部选项区域
        self.options_group = QGroupBox("任务选项")
        options_layout = QVBoxLayout()
        options_layout.setSpacing(5)

        # 目录选择部分
        folder_layout = QHBoxLayout()
        
        self.folder_label = QLabel("目标目录:")
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)  # 只读显示路径
        self.select_btn = QPushButton("选择目录")
        self.select_btn.clicked.connect(self._select_directory)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_path, stretch=1)  # 路径输入框拉伸
        folder_layout.addWidget(self.select_btn)

        options_layout.addLayout(folder_layout)

        # 产品下拉框
        product_layout = QHBoxLayout()
        product_label = QLabel("产品类型:")
        self.product_combo = QComboBox() # ([ "Tread XP", "Chimera" ])
        product_layout.addWidget(product_label)
        product_layout.addWidget(self.product_combo)
        product_layout.addStretch()

        options_layout.addLayout(product_layout)

        # Hash类型勾选框
        hash_layout = QHBoxLayout()
        hash_label = QLabel("启用校验:")
        self.checkbox_md5 = QCheckBox("MD5")
        self.checkbox_blake3 = QCheckBox("BLAKE3")
        self.checkbox_xxh3 = QCheckBox("XXH3")
        hash_layout.addWidget(hash_label)
        hash_layout.addWidget(self.checkbox_md5)
        hash_layout.addWidget(self.checkbox_blake3)
        hash_layout.addWidget(self.checkbox_xxh3)
        hash_layout.addStretch()  # 右对齐伸展
        options_layout.addLayout(hash_layout)
        
        self.options_group.setLayout(options_layout)
        layout.addWidget(self.options_group)
        
        # 日志栏
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout()

        # 日志级别和保存按钮部分
        log_head_layout = QHBoxLayout()

        log_level_label = QLabel("日志级别:")
        log_head_layout.addWidget(log_level_label)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["error", "warning", "info", "debug"])
        self.log_level_combo.currentTextChanged.connect(self._log_level_changed)
        log_head_layout.addWidget(self.log_level_combo)

        log_head_layout.addStretch()  # 间隔
        
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self._clear_log_btn_clicked)
        log_head_layout.addWidget(self.clear_log_btn)

        self.save_log_btn = QPushButton("导出完整日志")
        self.save_log_btn.clicked.connect(self._save_log_btn_clicked)
        log_head_layout.addWidget(self.save_log_btn)

        log_layout.addLayout(log_head_layout)

        # 日志框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        Logger.bind(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group, stretch=1)
        
        # 底部按钮和复选框
        bottom_layout = QHBoxLayout()

        # 版本
        version_label = QLabel(f"当前版本：{__version__}")
        bottom_layout.addWidget(version_label)

        bottom_layout.addStretch()
        
        # 错误中断勾选框
        self.checkbox_break = QCheckBox("错误时中断")
        self.checkbox_break.setChecked(True)
        bottom_layout.addWidget(self.checkbox_break)
        
        # 开始按钮
        self.start_btn = QPushButton("开始")
        self.start_btn.setEnabled(False)
        self.start_btn.setFixedSize(80, 40)
        self.start_btn.setStyleSheet(self._get_start_button_style(False))
        self.start_btn.clicked.connect(self._start_process)
        bottom_layout.addWidget(self.start_btn)
        
        layout.addLayout(bottom_layout)

        # 恢复状态
        self.user_config = UserConfig()
        self.user_config.load_config()

        self.product_combo.addItems(self.user_config.targets)
        self.product_combo.setCurrentText(self.user_config.target)
        self.product_combo.currentTextChanged.connect(self._select_target)

        self.log_level_combo.setCurrentText(self.user_config.log_level)
        Logger.set_print_level(self.user_config.log_level)

        if self.user_config.selected_dir:
            self.folder_path.setText(self.user_config.selected_dir)
            self._update_start_button(True)

        self.checkbox_md5.setChecked(self.user_config.md5_state)
        self.checkbox_blake3.setChecked(self.user_config.blake3_state)
        self.checkbox_xxh3.setChecked(self.user_config.xxh3_state)

    @staticmethod
    def _get_start_button_style(enabled: bool) -> str:
        """获取开始按钮样式"""
        if enabled:
            return """
                QPushButton {
                    background-color: #00AA00;
                    color: white;
                    border: none;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #00DD00;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #CCCCCC;
                    color: gray;
                    border: none;
                    border-radius: 5px;
                }
            """
    
    def _select_directory(self):
        """选择目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择目录")
        if directory:
            self.folder_path.setText(directory)
            self.user_config.select_dir(directory)
            self._update_start_button(True)
    
    def _select_target(self, selected_target: str):
        """选择产品类型"""
        self.user_config.target = selected_target
    
    def _log_level_changed(self, selected_level: str):
        """选择日志级别"""
        self.user_config.set_log_level(selected_level)
        Logger.set_print_level(self.user_config.log_level)
    
    def _clear_log_btn_clicked(self):
        """清空日志按钮点击处理"""
        Logger.delete_log()
        self.log_text.clear()

    def _save_log_btn_clicked(self):
        """保存日志按钮点击处理"""
        Logger.save_log_to_file(self, self.latest_end_time)
    
    def _start_process(self):
        """开始处理"""
        self._disable_controls()
        self.log_text.clear()
        
        self.process_thread = ProcessThread(
            self.user_config.selected_dir,
            self.user_config.target,
            self.checkbox_break.isChecked(),
            enable_md5=self.checkbox_md5.isChecked(),
            enable_blake3=self.checkbox_blake3.isChecked(),
            enable_xxh3=self.checkbox_xxh3.isChecked()
        )
        self.process_thread.finished_signal.connect(self._on_process_finished)
        self.process_thread.start()
    
    def _update_start_button(self, enabled: bool):
        """更新开始按钮状态"""
        self.start_btn.setEnabled(enabled)
        self.start_btn.setStyleSheet(self._get_start_button_style(enabled))
    
    def _disable_controls(self):
        """禁用所有控制按钮"""
        self.options_group.setEnabled(False)
        self.checkbox_break.setEnabled(False)
        self._update_start_button(False)
    
    def _on_process_finished(self):
        """处理完成"""
        self.options_group.setEnabled(True)
        self.checkbox_break.setEnabled(True)
        self._update_start_button(True)
        # 保存最后的完成时间
        if self.process_thread:
            self.latest_end_time = self.process_thread.end_time
    
    def closeEvent(self, event):
        """窗口关闭时保存配置"""
        self.user_config.set_md5_state(self.checkbox_md5.isChecked())
        self.user_config.set_blake3_state(self.checkbox_blake3.isChecked())
        self.user_config.set_xxh3_state(self.checkbox_xxh3.isChecked())
        self.user_config.save_config()
        event.accept()
