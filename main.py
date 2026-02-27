import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QSystemTrayIcon, QMenu, 
                             QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox, 
                             QLabel, QHBoxLayout, QFrame)
from PySide6.QtGui import QIcon, QAction, QFont, QColor
from PySide6.QtCore import Qt, QThread, Signal

# --- 配置（固定部分） ---
TG_BOT_TOKEN = "8205657344:AAFN6ypCKJ513nM11Xwz3nT8yw5qfbRcVYI"
TG_CHAT_ID = "-5136067937"
SEARCH_URL = "https://sousuo.zze.cc/search"

# --- Win11 风格样式表 ---
QSS_STYLE = """
QMainWindow {
    background-color: #f3f3f3;
}
QLabel {
    font-family: "Microsoft YaHei UI";
    font-size: 14px;
    color: #333;
}
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #dcdcdc;
    border-radius: 8px;
    padding: 10px;
    font-family: "Consolas", "Microsoft YaHei";
    font-size: 13px;
    color: #2b2b2b;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 6px;
    padding: 8px 16px;
    font-family: "Microsoft YaHei UI";
    font-weight: bold;
}
QPushButton#PrimaryBtn {
    background-color: #0067c0;
    color: white;
    border: none;
}
QPushButton#PrimaryBtn:hover {
    background-color: #0056a0;
}
QPushButton#SecondaryBtn:hover {
    background-color: #f9f9f9;
}
"""

class BriefWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def run(self):
        try:
            # 抓取逻辑
            resp = requests.get(SEARCH_URL, params={"q": "West Africa healthcare news"}, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.find_all('article', limit=4)
            
            news_items = ""
            for i, art in enumerate(articles, 1):
                title = art.find('h3').get_text(strip=True) if art.find('h3') else "区域健康动态"
                link = art.find('a')['href'] if art.find('a') else SEARCH_URL
                news_items += f"{i}. {title}\n• 来源：[查看原文]({link})\n"

            today = datetime.now().strftime("%Y年%m月%d日")
            template = f"""《HCOWA西非健康共同体协会每日健康时事简报》 
日期：{today} | 坐标：加纳 · 阿克拉 (Accra)
───
📌 【首要关注：】
{news_items}
───
🌍 【西非区域动态汇报】
• 区域内多国正加强跨境卫生协作。
───
📊 【协会时事热度分析（HCOWA Index）】
• 当前最高热度：数字化卫生改革。
• HCOWA 提醒：建议关注近期区域展会。
───
2026中国-西非医疗健康产业博览会
【☎️展会招商联系方式☎️】
陈 洁 13541379956
皮志仁 18674858861
彭丽瑛 17375719615
龚小兰 19180714740
岁 / 启 / 新 / 程 ● 健 / 康 / 西 / 非
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
        self.setWindowTitle("HCOWA 简报助手 - Zaki Edit")
        self.setFixedSize(550, 700)
        self.setWindowIcon(QIcon("assets/logo.jpg"))
        self.setStyleSheet(QSS_STYLE)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 头部标题
        header = QLabel("🚀 简报生产工作台")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #0067c0;")
        main_layout.addWidget(header)

        # 编辑器部分
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("第一步：点击下方生成按钮同步最新云端数据...")
        main_layout.addWidget(self.editor)

        # 按钮区
        btn_container = QHBoxLayout()
        
        self.gen_btn = QPushButton("☁️ 同步云端数据")
        self.gen_btn.setObjectName("SecondaryBtn")
        self.gen_btn.clicked.connect(self.generate_brief)
        
        self.send_btn = QPushButton("🚀 确认正式推送")
        self.send_btn.setObjectName("PrimaryBtn")
        self.send_btn.clicked.connect(self.send_to_tg)
        
        btn_container.addWidget(self.gen_btn)
        btn_container.addWidget(self.send_btn)
        main_layout.addLayout(btn_container)

        # 状态栏模拟
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-size: 11px; color: #888;")
        main_layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def generate_brief(self):
        self.status_label.setText("正在通过云端引擎检索数据...")
        self.gen_btn.setEnabled(False)
        self.worker = BriefWorker()
        self.worker.finished.connect(self.on_gen_finished)
        self.worker.error.connect(self.on_gen_error)
        self.worker.start()

    def on_gen_finished(self, content):
        self.editor.setPlainText(content)
        self.gen_btn.setEnabled(True)
        self.status_label.setText("数据同步完成。")

    def on_gen_error(self, err):
        QMessageBox.critical(self, "连接错误", f"云端抓取失败: {err}")
        self.gen_btn.setEnabled(True)
        self.status_label.setText("由于网络原因同步中止。")

    def send_to_tg(self):
        content = self.editor.toPlainText()
        if not content:
            return
        
        self.status_label.setText("正在向 Telegram 服务器投递数据...")
        try:
            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
            payload = {"chat_id": TG_CHAT_ID, "text": content, "parse_mode": "Markdown"}
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                QMessageBox.information(self, "推送成功", "今日简报已成功送达群组。")
                self.status_label.setText("投递成功。")
            else:
                QMessageBox.warning(self, "推送失败", f"错误码: {r.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "通讯异常", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
