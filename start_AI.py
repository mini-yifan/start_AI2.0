import sys
import os
import re
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
                             QStyleFactory, QLineEdit, QGridLayout, QFrame, QStatusBar, QTextEdit, QFileDialog, QComboBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, QProcess, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QDesktopServices
import subprocess

# 使用环境变量抑制PyQt5的警告
os.environ['QT_LOGGING_RULES'] = '*.warning=false;*.critical=false'

class LauncherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mcp_process = None
        self.api_modified = False  # 标记API是否被修改
        self.init_ui()
        # 检查mcp_agent.exe是否正在运行
        QTimer.singleShot(100, self.check_mcp_process)
    
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle("AI Jarvis 启动器")
        self.setGeometry(100, 100, 800, 600)
        
        # 设置窗口样式
        app.setStyle(QStyleFactory.create('Fusion'))
        
        # 设置窗口背景颜色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # 创建顶部布局
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignRight)
        
        # 创建保存按钮
        self.save_button = QPushButton("保存信息")
        self.save_button.setMinimumSize(120, 40)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.save_button.clicked.connect(self.save_api_keys)
        top_layout.addWidget(self.save_button)
        
        # 添加水平间距
        top_layout.addSpacing(10)
        
        # 创建启动按钮
        self.launch_button = QPushButton("启动/重新启动")
        self.launch_button.setMinimumSize(120, 40)
        self.launch_button.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.launch_button.clicked.connect(self.toggle_mcp_process)
        top_layout.addWidget(self.launch_button)
        main_layout.addLayout(top_layout)
        
        # 创建状态栏用于显示未保存提示
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 创建选项卡控件，设置为顶部水平布局
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)  # 将选项卡放在顶部
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #1976D2;
                border-radius: 8px;
                background-color: #f0f7ff;
                margin-top: 2px;
            }
            QTabBar {
                background-color: transparent;
                alignment: left;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                color: #0D47A1;
                border: 2px solid #BBDEFB;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 12px 24px;
                margin-right: 5px;
                font-size: 15px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                min-width: 150px; /* 增加最小宽度以确保文字完全显示 */
            }
            QTabBar::tab:selected {
                background-color: #1976D2;
                color: white;
                border-color: #1976D2;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E3F2FD;
                border-color: #90CAF9;
            }
        """)
        
        # 创建第一个选项卡内容 - API管理
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setContentsMargins(30, 20, 30, 20)
        
        label1 = QLabel("API密钥管理")
        label1.setStyleSheet("font-size: 18px; font-weight: bold; color: #0D47A1;")
        label1.setAlignment(Qt.AlignCenter)
        
        # 创建API输入区域
        api_frame = QFrame()
        api_frame.setFrameShape(QFrame.StyledPanel)
        api_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f9ff;
                border-radius: 8px;
                border: 1px solid #bbdefb;
            }
        """)
        
        api_layout = QGridLayout(api_frame)
        api_layout.setContentsMargins(20, 20, 20, 20)
        api_layout.setSpacing(15)
        
        # 阿里云API标签和输入框（带眼睛图标）
        alibaba_label_layout = QHBoxLayout()
        alibaba_label = QLabel("阿里云API:")
        alibaba_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #0D47A1;")
        
        # 创建超链接标签
        alibaba_link = QLabel('<a href="https://bailian.console.aliyun.com/?tab=model#/api-key">获取API密钥</a>')
        alibaba_link.setOpenExternalLinks(True)
        alibaba_link.setStyleSheet("color: #1976D2; text-decoration: none;")
        alibaba_link.linkActivated.connect(self.open_url)
        
        alibaba_label_layout.addWidget(alibaba_label)
        alibaba_label_layout.addWidget(alibaba_link)
        
        # 创建水平布局包含输入框和眼睛图标
        alibaba_input_layout = QHBoxLayout()
        self.alibaba_api_input = QLineEdit()
        self.alibaba_api_input.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.alibaba_api_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 4px 0 0 4px;
                padding: 8px 12px;
                font-size: 10px; /* 减小字体大小使密码点变小 */
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1976D2;
                background-color: #f0f7ff;
            }
        """)
        self.alibaba_api_input.textChanged.connect(self.set_api_modified)
        
        # 创建眼睛图标按钮
        self.alibaba_eye_button = QPushButton()
        self.alibaba_eye_button.setFixedSize(40, 40)
        self.alibaba_eye_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #bbdefb;
                border-left: none;
                border-radius: 0 4px 4px 0;
                background-color: #f5f9ff;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        # 使用文字作为眼睛图标（在没有实际图标的情况下）
        self.alibaba_eye_button.setText("👁")
        self.alibaba_eye_button.setToolTip("显示密码")
        self.alibaba_eye_button.clicked.connect(lambda: self.toggle_password_visibility(self.alibaba_api_input, self.alibaba_eye_button))
        
        # 添加到水平布局
        alibaba_input_layout.addWidget(self.alibaba_api_input)
        alibaba_input_layout.addWidget(self.alibaba_eye_button)
        alibaba_input_layout.setContentsMargins(0, 0, 0, 0)
        alibaba_input_layout.setSpacing(0)
        
        # 秘塔AI搜索API标签和输入框（带眼睛图标）
        metaso_label_layout = QHBoxLayout()
        metaso_label = QLabel("秘塔AI搜索API:")
        metaso_label.setStyleSheet("font-size: 14px; font-weight: 500; color: #0D47A1;")
        
        # 创建超链接标签
        metaso_link = QLabel('<a href="https://metaso.cn/search-api/api-keys">获取API密钥</a>')
        metaso_link.setOpenExternalLinks(True)
        metaso_link.setStyleSheet("color: #1976D2; text-decoration: none;")
        metaso_link.linkActivated.connect(self.open_url)
        
        metaso_label_layout.addWidget(metaso_label)
        metaso_label_layout.addWidget(metaso_link)
        
        # 创建水平布局包含输入框和眼睛图标
        metaso_input_layout = QHBoxLayout()
        self.metaso_api_input = QLineEdit()
        self.metaso_api_input.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.metaso_api_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 4px 0 0 4px;
                padding: 8px 12px;
                font-size: 10px; /* 减小字体大小使密码点变小 */
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1976D2;
                background-color: #f0f7ff;
            }
        """)
        self.metaso_api_input.textChanged.connect(self.set_api_modified)
        
        # 创建眼睛图标按钮
        self.metaso_eye_button = QPushButton()
        self.metaso_eye_button.setFixedSize(40, 40)
        self.metaso_eye_button.setStyleSheet("""
            QPushButton {
                border: 2px solid #bbdefb;
                border-left: none;
                border-radius: 0 4px 4px 0;
                background-color: #f5f9ff;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
            }
        """)
        # 使用文字作为眼睛图标（在没有实际图标的情况下）
        self.metaso_eye_button.setText("👁")
        self.metaso_eye_button.setToolTip("显示密码")
        self.metaso_eye_button.clicked.connect(lambda: self.toggle_password_visibility(self.metaso_api_input, self.metaso_eye_button))
        
        # 添加到水平布局
        metaso_input_layout.addWidget(self.metaso_api_input)
        metaso_input_layout.addWidget(self.metaso_eye_button)
        metaso_input_layout.setContentsMargins(0, 0, 0, 0)
        metaso_input_layout.setSpacing(0)
        
        # 添加到布局
        api_layout.addLayout(alibaba_label_layout, 0, 0)
        api_layout.addLayout(alibaba_input_layout, 0, 1)
        api_layout.addLayout(metaso_label_layout, 1, 0)
        api_layout.addLayout(metaso_input_layout, 1, 1)
        
        # 设置列的拉伸因子，使输入框占据更多空间
        api_layout.setColumnStretch(1, 1)
        
        # 加载.env中的API值
        self.load_api_keys()
        
        tab1_layout.addWidget(label1)
        tab1_layout.addSpacing(20)
        tab1_layout.addWidget(api_frame)
        tab1_layout.addStretch()
        
        # 状态标签
        status_label = QLabel("状态: 等待启动")
        status_label.setStyleSheet("font-size: 14px; color: #FF9800; margin-top: 20px;")
        status_label.setAlignment(Qt.AlignCenter)
        self.status_label = status_label
        tab1_layout.addWidget(status_label)
        
        # 创建第二个选项卡 - 设置选项卡
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        
        # 顶部：AI性格设置
        ai_character_label = QLabel("设置你的专属AI的性格")
        ai_character_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #0D47A1; margin-bottom: 5px;")
        
        self.ai_character_input = QTextEdit()
        self.ai_character_input.setMinimumHeight(150)
        self.ai_character_input.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bbdefb;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #1976D2;
                background-color: #f0f7ff;
            }
        """)
        self.ai_character_input.textChanged.connect(self.set_settings_modified)
        
        # 创建底部的水平布局（T字形的底部）
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # 左侧：悬浮球头像设置
        avatar_frame = QGroupBox()
        avatar_frame.setStyleSheet("""
            QGroupBox {
                border: 2px solid #bbdefb;
                border-radius: 5px;
                padding: 15px;
                background-color: #fafafa;
            }
        """)
        avatar_layout = QVBoxLayout(avatar_frame)
        
        # 文件选择按钮
        self.avatar_path = ""
        self.select_avatar_btn = QPushButton("自定义悬浮球头像")
        self.select_avatar_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.select_avatar_btn.clicked.connect(self.select_avatar_file)
        
        # 图片预览标签
        self.avatar_preview = QLabel()
        self.avatar_preview.setAlignment(Qt.AlignCenter)
        self.avatar_preview.setFixedSize(100, 100)
        self.avatar_preview.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: white;
                border-radius: 5px;
            }
        """)
        
        # 恢复默认按钮
        self.reset_avatar_btn = QPushButton("恢复默认")
        self.reset_avatar_btn.setStyleSheet("""
            QPushButton {
                background-color: #BBDEFB;
                color: #1565C0;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #90CAF9;
            }
        """)
        self.reset_avatar_btn.clicked.connect(self.reset_to_default_avatar)
        
        avatar_layout.addWidget(self.select_avatar_btn)
        avatar_layout.addSpacing(15)
        avatar_layout.addWidget(self.avatar_preview)
        avatar_layout.addSpacing(10)
        avatar_layout.addWidget(self.reset_avatar_btn)
        avatar_layout.addStretch()
        
        # 右侧：声音设置
        sound_frame = QGroupBox()
        sound_frame.setStyleSheet("""
            QGroupBox {
                border: 2px solid #bbdefb;
                border-radius: 5px;
                padding: 15px;
                background-color: #fafafa;
            }
        """)
        sound_layout = QVBoxLayout(sound_frame)
        
        # 声音类型选择
        sound_type_label = QLabel("声音类型：")
        sound_type_label.setStyleSheet("color: #1565C0; margin-bottom: 5px;")
        
        self.sound_type_combo = QComboBox()
        self.sound_type_combo.addItems(["男声", "女声"])
        self.sound_type_combo.setStyleSheet('''
            QComboBox {
                border: 2px solid #1976D2;
                border-radius: 8px;
                padding: 8px 12px;
                background-color: white;
                min-width: 160px;
                font-size: 14px;
                color: #1565C0;
                font-weight: bold;
            }
            QComboBox:hover {
                border-color: #1565C0;
                background-color: #f0f7ff;
            }
            QComboBox:focus {
                border-color: #0D47A1;
                background-color: #f0f7ff;
                outline: none;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #bbdefb;
                border-radius: 10px;
                padding: 5px;
                background-color: white;
                selection-background-color: #90caf9;
                selection-color: #1565C0;
                font-size: 14px;
            }
        ''')
        self.sound_type_combo.currentIndexChanged.connect(self.set_settings_modified)
        
        # 开启语音对话选项
        self.enable_voice_checkbox = QCheckBox("开启语音对话")
        self.enable_voice_checkbox.setStyleSheet("""
            QCheckBox {
                color: #1565C0;
                font-size: 14px;
                margin-top: 15px;
            }
        """)
        self.enable_voice_checkbox.stateChanged.connect(self.set_settings_modified)
        
        sound_layout.addWidget(sound_type_label)
        sound_layout.addWidget(self.sound_type_combo)
        sound_layout.addWidget(self.enable_voice_checkbox)
        sound_layout.addStretch()
        
        # 将左右部分添加到底部布局
        bottom_layout.addWidget(avatar_frame)
        bottom_layout.addWidget(sound_frame)
        
        # 添加到主设置布局
        tab2_layout.addWidget(ai_character_label)
        tab2_layout.addWidget(self.ai_character_input)
        tab2_layout.addLayout(bottom_layout)
        tab2_layout.setContentsMargins(20, 20, 20, 20)
        tab2_layout.setSpacing(15)
        
        # 添加选项卡到选项卡控件
        self.tab_widget.addTab(tab1, "API密钥管理")
        self.tab_widget.addTab(tab2, "设置")
        
        # 添加选项卡控件到主布局
        main_layout.addWidget(self.tab_widget)
        
        # 初始化设置状态标志
        self.settings_modified = False
        
        # 加载设置
        self.load_settings()
    
    def set_api_modified(self):
        """设置API已修改标志并显示提示"""
        # 每次修改都设置标志并显示提示，不再检查是否已经设置
        self.api_modified = True
        # 使状态栏提示更醒目
        self.statusBar.setStyleSheet("color: #D32F2F; font-weight: bold; background-color: #FFF3E0;")
        self.statusBar.showMessage("修改后点击”保存信息”才能在软件中执行", 0)  # 0表示一直显示
    
    def set_settings_modified(self):
        """设置设置已修改标志并显示提示"""
        # 每次修改都设置标志并显示提示
        self.settings_modified = True
        # 使状态栏提示更醒目
        self.statusBar.setStyleSheet("color: #D32F2F; font-weight: bold; background-color: #FFF3E0;")
        self.statusBar.showMessage("修改后点击”保存信息”才能在软件中执行", 0)  # 0表示一直显示
    
    def load_settings(self):
        """加载所有设置"""
        # 加载AI性格设置
        ai_setting_path = os.path.join(os.getcwd(), "ai_setting.txt")
        if os.path.exists(ai_setting_path):
            try:
                with open(ai_setting_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.ai_character_input.setText(content)
            except Exception as e:
                print(f"加载AI性格设置失败: {e}")
        
        # 加载声音类型设置
        tts_sound_path = os.path.join(os.getcwd(), "tts_sound.txt")
        if os.path.exists(tts_sound_path):
            try:
                with open(tts_sound_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content == "male":
                        self.sound_type_combo.setCurrentIndex(0)  # 男声
                    elif content == "female":
                        self.sound_type_combo.setCurrentIndex(1)  # 女声
            except Exception as e:
                print(f"加载声音设置失败: {e}")
        
        # 加载语音对话开关设置
        sound_on_path = os.path.join(os.getcwd(), "sound_on.txt")
        if os.path.exists(sound_on_path):
            try:
                with open(sound_on_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self.enable_voice_checkbox.setChecked(content.lower() == "true")
            except Exception as e:
                print(f"加载语音对话设置失败: {e}")
        
        # 显示默认头像
        self.update_avatar_preview()
    
    def open_url(self, url):
        """打开指定的URL"""
        QDesktopServices.openUrl(url)
        
    def load_api_keys(self):
        """从.env文件加载API密钥"""
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 读取阿里云API
                alibaba_match = re.search(r'ALIBABA_CLOUD_ACCESS_KEY_ID\s*=\s*["\'](.*?)["\']', content)
                if alibaba_match:
                    self.alibaba_api_input.setText(alibaba_match.group(1))
                
                # 读取秘塔AI搜索API
                metaso_match = re.search(r'METASO_API_KEY\s*=\s*["\'](.*?)["\']', content)
                if metaso_match:
                    self.metaso_api_input.setText(metaso_match.group(1))
    
    def select_avatar_file(self):
        """选择头像文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PNG图片", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            self.avatar_path = file_path
            # 立即更新预览
            self.update_avatar_preview(file_path)
            # 设置修改标志
            self.set_settings_modified()
    
    def update_avatar_preview(self, file_path=None):
        """更新头像预览"""
        from PyQt5.QtGui import QPixmap
        
        # 如果没有提供文件路径，使用默认路径
        if not file_path:
            file_path = os.path.join(os.getcwd(), "downloads", "圆AI.png")
        
        if os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            # 缩放图片以适应预览框
            scaled_pixmap = pixmap.scaled(
                self.avatar_preview.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.avatar_preview.setPixmap(scaled_pixmap)
        else:
            # 如果默认图片不存在，显示提示文本
            self.avatar_preview.setText("默认图片不存在")
    
    def reset_to_default_avatar(self):
        """恢复默认头像"""
        # 设置为默认头像路径
        default_avatar_path = os.path.join(os.getcwd(), "downloads", "圆AI - 副本.png")
        
        if os.path.exists(default_avatar_path):
            # 设置头像路径
            self.avatar_path = default_avatar_path
            # 更新预览
            self.update_avatar_preview(default_avatar_path)
            # 设置修改标志
            self.set_settings_modified()
        else:
            # 如果默认副本图片不存在，显示提示
            self.avatar_preview.setText("默认副本图片不存在")
    
    def save_api_keys(self):
        """保存API密钥和所有设置"""
        try:
            # 保存API密钥到.env文件
            env_path = os.path.join(os.getcwd(), ".env")
            
            if os.path.exists(env_path):
                # 读取现有内容
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 更新阿里云API
                alibaba_key = self.alibaba_api_input.text().strip()
                if alibaba_key:
                    if re.search(r'ALIBABA_CLOUD_ACCESS_KEY_ID\s*=', content):
                        content = re.sub(r'ALIBABA_CLOUD_ACCESS_KEY_ID\s*=\s*["\'](.*?)["\']', 
                                        f'ALIBABA_CLOUD_ACCESS_KEY_ID = "{alibaba_key}"', content)
                    else:
                        # 如果不存在，则添加新行
                        content += f'\nALIBABA_CLOUD_ACCESS_KEY_ID = "{alibaba_key}"'
                
                # 更新秘塔AI搜索API
                metaso_key = self.metaso_api_input.text().strip()
                if metaso_key:
                    if re.search(r'METASO_API_KEY\s*=', content):
                        content = re.sub(r'METASO_API_KEY\s*=\s*["\'](.*?)["\']', 
                                        f'METASO_API_KEY = "{metaso_key}"', content)
                    else:
                        # 如果不存在，则添加新行
                        content += f'\nMETASO_API_KEY = "{metaso_key}"'
                
                # 写入文件
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # 创建新的.env文件
                content = ""
                
                # 添加阿里云API
                alibaba_key = self.alibaba_api_input.text().strip()
                if alibaba_key:
                    content += f'ALIBABA_CLOUD_ACCESS_KEY_ID = "{alibaba_key}"\n'
                
                # 添加秘塔AI搜索API
                metaso_key = self.metaso_api_input.text().strip()
                if metaso_key:
                    content += f'METASO_API_KEY = "{metaso_key}"\n'
                
                # 写入文件
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # 保存AI性格设置
            # 保存AI性格
            ai_setting_path = os.path.join(os.getcwd(), "ai_setting.txt")
            with open(ai_setting_path, 'w', encoding='utf-8') as f:
                f.write(self.ai_character_input.toPlainText())
            
            # 保存声音类型
            tts_sound_path = os.path.join(os.getcwd(), "tts_sound.txt")
            sound_type = "male" if self.sound_type_combo.currentIndex() == 0 else "female"
            with open(tts_sound_path, 'w', encoding='utf-8') as f:
                f.write(sound_type)
            
            # 保存语音对话开关
            sound_on_path = os.path.join(os.getcwd(), "sound_on.txt")
            with open(sound_on_path, 'w', encoding='utf-8') as f:
                f.write("True" if self.enable_voice_checkbox.isChecked() else "False")
            
            # 保存头像
            if self.avatar_path:
                import shutil
                downloads_dir = os.path.join(os.getcwd(), "downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                target_path = os.path.join(downloads_dir, "圆AI.png")
                # 复制文件并覆盖
                shutil.copy2(self.avatar_path, target_path)
                # 更新预览为目标文件
                self.update_avatar_preview(target_path)
                # 重置选择的路径
                self.avatar_path = ""
            
            # 更新状态
            self.api_modified = False
            self.settings_modified = False
            # 恢复状态栏默认样式
            self.statusBar.setStyleSheet("")
            self.statusBar.clearMessage()
            QMessageBox.information(self, "成功", "所有设置已保存")
        except Exception as e:
            # 即使出错也更新状态，避免用户无法继续操作
            self.api_modified = False
            self.settings_modified = False
            self.statusBar.setStyleSheet("")
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
                
    def toggle_password_visibility(self, line_edit, eye_button):
        """切换密码显示/隐藏状态"""
        if line_edit.echoMode() == QLineEdit.Password:
            # 显示密码
            line_edit.setEchoMode(QLineEdit.Normal)
            eye_button.setText("👁️")
            eye_button.setToolTip("隐藏密码")
        else:
            # 隐藏密码
            line_edit.setEchoMode(QLineEdit.Password)
            eye_button.setText("👁")
            eye_button.setToolTip("显示密码")
            eye_button.setToolTip("显示密码")
    
    def toggle_mcp_process(self):
        """切换mcp_agent.exe进程的状态（启动/重新启动）"""
        # 如果API被修改但未保存，提示用户
        if self.api_modified:
            reply = QMessageBox.question(self, "未保存的更改", 
                                         "您有未保存的API更改，是否继续启动服务？",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        # 强制关闭系统中所有运行的mcp_agent.exe进程
        self.status_label.setText("状态: 正在关闭现有进程...")
        self.status_label.setStyleSheet("font-size: 14px; color: #FF9800; margin-top: 20px;")
        
        # 使用taskkill命令强制关闭所有mcp_agent.exe进程
        try:
            # /F 强制终止进程，/IM 指定进程映像名称
            subprocess.run(
                ['taskkill', '/F', '/IM', 'mcp_agent.exe'],
                shell=True,
                capture_output=True,
                text=True
            )
            # 等待进程完全终止
            time.sleep(1)
        except Exception as e:
            # 忽略taskkill命令的错误，继续执行
            pass
        
        # 关闭当前对象管理的进程
        if hasattr(self, 'mcp_process') and self.mcp_process:
            try:
                # 尝试终止进程
                self.mcp_process.terminate()
                # 等待进程终止
                self.mcp_process.wait(timeout=2)
            except:
                # 如果终止失败，强制杀死进程
                try:
                    self.mcp_process.kill()
                except:
                    pass
        
        self.status_label.setText("状态: 启动中...")
        
        # 启动新进程
        try:
            # 获取应用程序所在目录，而不是当前工作目录
            if hasattr(sys, 'frozen'):
                # 对于打包后的可执行文件
                app_dir = os.path.dirname(sys.executable)
            else:
                # 对于普通Python脚本
                app_dir = os.getcwd()
            mcp_path = os.path.join(app_dir, "mcp_agent.exe")
            if not os.path.exists(mcp_path):
                self.status_label.setText("状态: 文件不存在")
                self.status_label.setStyleSheet("font-size: 14px; color: #D32F2F; margin-top: 20px;")
                QMessageBox.warning(self, "警告", "mcp_agent.exe 文件不存在")
                return
            
            # 使用subprocess.Popen强制启动进程，添加shell=True参数
            # 设置creationflags确保进程能独立运行
            self.mcp_process = subprocess.Popen(
                [mcp_path],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE  # 创建新控制台窗口，确保进程能够启动
            )
            
            # 立即设置为运行状态，因为subprocess.Popen是异步的
            self.status_label.setText("状态: 运行中")
            self.status_label.setStyleSheet("font-size: 14px; color: #1976D2; margin-top: 20px;")
            self.launch_button.setText("重新启动")
            
            # 启动定时器检查进程状态
            QTimer.singleShot(2000, self.check_mcp_process)
            
        except Exception as e:
            self.status_label.setText("状态: 启动错误")
            self.status_label.setStyleSheet("font-size: 14px; color: #D32F2F; margin-top: 20px;")
            QMessageBox.critical(self, "错误", f"启动进程时出错: {str(e)}")

    
    def check_mcp_process(self):
        """检查mcp_agent.exe是否已经在运行"""
        try:
            # 使用tasklist命令检查进程
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq mcp_agent.exe'], 
                capture_output=True, text=True, shell=True
            )
            
            if "mcp_agent.exe" in result.stdout:
                self.status_label.setText("状态: 运行中")
                self.status_label.setStyleSheet("font-size: 14px; color: #1976D2; margin-top: 20px;")
                self.launch_button.setText("重新启动")
            else:
                self.status_label.setText("状态: 未运行")
                self.status_label.setStyleSheet("font-size: 14px; color: #666; margin-top: 20px;")
        except Exception as e:
            print(f"检查进程状态时出错: {str(e)}")
    
    def closeEvent(self, event):
        """窗口关闭时的处理"""
        # 关闭mcp_process（如果存在）
        if hasattr(self, 'mcp_process') and self.mcp_process:
            try:
                # 尝试终止subprocess进程
                self.mcp_process.terminate()
                # 等待进程终止
                try:
                    self.mcp_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # 如果超时，强制杀死进程
                    self.mcp_process.kill()
            except Exception:
                # 忽略关闭时的错误
                pass
        event.accept()

if __name__ == "__main__":
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    window = LauncherApp()
    window.show()
    sys.exit(app.exec_())