import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
                             QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox, 
                             QLabel, QHBoxLayout)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt, QThread, Signal

# 配置信息（建议以后放入配置文件）
TG_BOT_TOKEN = "8205657344:AAFN6ypCKJ513nM11Xwz3nT8yw5qfbRcVYI"
TG_CHAT_ID = "-5136067937"
SEARCH_URL = "https://sousuo.zze.cc/search"

class BriefWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def run(self):
        try:
            # 1. 抓取新闻
            query = "West Africa Ghana healthcare news"
            params = {"q": query}
            resp = requests.get(SEARCH_URL, params=params, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 简单解析逻辑（根据 sousuo.zze.cc 结构可微调）
            articles = soup.find_all('article', limit=4)
            news_items = ""
            for i, art in enumerate(articles, 1):
                title = art.find('h3').get_text(strip=True) if art.find('h3') else "最新健康简讯"
                link = art.find('a')['href'] if art.find('a') else SEARCH_URL
                news_items += f"{i}. {title}\n• 来源：[查看原文]({link})\n"

            # 2. 构造模板
            today = datetime.now().strftime("%Y年%m月%d日")
            template = f"""《HCOWA西非健康共同体协会每日健康时事简报》 
日期：{today} | 坐标：加纳 · 阿克拉 (Accra)
───
📌 【首要关注：】
{news_items}
───
🌍 【西非区域动态汇报】
（此处可根据搜索结果微调）
───
📊 【协会时事热度分析（HCOWA Index）】
• 当前最高热度：区域公共卫生政策更新
• HCOWA 提醒：建议关注各国最新检疫动态。
───
2026中国-西非医疗健康产业博览会
【☎️展会招商联系方式☎️】
陈 洁 13541379956
皮志仁 18674858861
彭丽瑛 17375719615
龚小兰 19180714740
岁 / 启 / 新 / 程 ● 健 /康 / 西 / 非
───
[HCOWA 信息中心]"""
            self.finished.emit(template)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("HCOWA 简报助手 v1.0")
        self.setFixedSize(500, 650)
        
        layout = QVBoxLayout()
        
        self.label = QLabel("今日简报内容预览：")
        layout.addWidget(self.label)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("点击下方生成按钮获取内容...")
        layout.addWidget(self.editor)

        btn_layout = QHBoxLayout()
        self.gen_btn = QPushButton("🚀 生成今日简报")
        self.gen_btn.clicked.connect(self.generate_brief)
        
        self.send_btn = QPushButton("📤 确认推送至群组")
        self.send_btn.clicked.connect(self.send_to_tg)
        self.send_btn.setStyleSheet("background-color: #4361ee; color: white; font-weight: bold;")
        
        btn_layout.addWidget(self.gen_btn)
        btn_layout.addWidget(self.send_btn)
        layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def generate_brief(self):
        self.gen_btn.setText("正在同步云端数据...")
        self.gen_btn.setEnabled(False)
        self.worker = BriefWorker()
        self.worker.finished.connect(self.on_gen_finished)
        self.worker.error.connect(self.on_gen_error)
        self.worker.start()

    def on_gen_finished(self, content):
        self.editor.setPlainText(content)
        self.gen_btn.setText("🚀 重新生成")
        self.gen_btn.setEnabled(True)

    def on_gen_error(self, err):
        QMessageBox.critical(self, "错误", f"获取数据失败: {err}")
        self.gen_btn.setEnabled(True)

    def send_to_tg(self):
        content = self.editor.toPlainText()
        if not content:
            QMessageBox.warning(self, "警告", "内容为空，请先生成。")
            return
        
        try:
            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TG_CHAT_ID, "text": content, "parse_mode": "Markdown"}
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                QMessageBox.information(self, "成功", "简报已成功投递！")
            else:
                QMessageBox.warning(self, "失败", f"推送失败: {r.text}")
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 托盘图标逻辑
    tray = QSystemTrayIcon()
    tray.setIcon(QIcon.fromTheme("edit-copy")) # 建议放置一个 real logo png
    
    main_win = MainWindow()
    
    def show_win():
        main_win.show()
        main_win.raise_()

    menu = QMenu()
    action_show = QAction("打开助手")
    action_show.triggered.connect(show_win)
    action_exit = QAction("退出程序")
    action_exit.triggered.connect(app.quit)
    
    menu.addAction(action_show)
    menu.addSeparator()
    menu.addAction(action_exit)
    
    tray.setContextMenu(menu)
    tray.show()
    
    # 默认显示主窗口
    show_win()
    
    sys.exit(app.exec())
