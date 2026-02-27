import sys
import requests
import base64
from bs4 import BeautifulSoup
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                             QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QThread, Signal

# --- 配置 ---
TG_BOT_TOKEN = "8205657344:AAFN6ypCKJ513nM11Xwz3nT8yw5qfbRcVYI"
TG_CHAT_ID = "-5136067937"
SEARCH_URL = "https://sousuo.zze.cc/search"

# 关闭低级别 SSL 警告
requests.packages.urllib3.disable_warnings()

class BriefWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def run(self):
        try:
            # 增加 User-Agent 模拟浏览器，并关闭 SSL 校验以解决报错
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            resp = requests.get(SEARCH_URL, params={"q": "West Africa health news 2026"}, headers=headers, timeout=20, verify=False)
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            articles = soup.find_all('article', limit=4)
            
            news_items = ""
            for i, art in enumerate(articles, 1):
                title_tag = art.find(['h3', 'h2', 'a'])
                title = title_tag.get_text(strip=True) if title_tag else "最新区域健康动态"
                link = art.find('a')['href'] if art.find('a') else SEARCH_URL
                if not link.startswith('http'): link = "https://sousuo.zze.cc" + link
                news_items += f"{i}. {title}\n• 来源：[点击查看原文]({link})\n"

            if not news_items: news_items = "1. 区域卫生协作持续推进\n• 来源：[官方监测](https://sousuo.zze.cc)\n"

            today = datetime.now().strftime("%Y年%m月%d日")
            template = f"""《HCOWA西非健康共同体协会每日健康时事简报》 
日期：{today} | 坐标：加纳 · 阿克拉 (Accra)
───
📌 【首要关注：】
{news_items}
───
🌍 【西非区域动态汇报】
（此处可根据搜索结果详细编辑...）
───
📈 【西非医疗板块股市动态】
（请根据今日 NGX/GSE 行情填入关键涨幅...）
───
📊 【协会时事热度分析（HCOWA Index）】
• 当前最高热度：数字化卫生改革。
• HCOWA 建议：重点关注药企本土化进程。
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
        self.setWindowTitle("HCOWA 简报助手 - Zaki Edit")
        self.setFixedSize(600, 750)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # 顶部 LOGO 展示区域
        logo_area = QHBoxLayout()
        try:
            self.pixmap = QPixmap("assets/logo.jpg")
            self.logo_label = QLabel()
            self.logo_label.setPixmap(self.pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_area.addWidget(self.logo_label)
        except:
            pass
        
        header_text = QLabel("🚀 简报生产工作台\n(Win11 Pro Ver)")
        header_text.setStyleSheet("font-size: 20px; font-weight: bold; color: #0067c0;")
        logo_area.addWidget(header_text)
        logo_area.addStretch()
        layout.addLayout(logo_area)

        self.editor = QTextEdit()
        self.editor.setStyleSheet("font-family: 'Microsoft YaHei'; font-size: 13px; border: 1px solid #ddd; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.editor)

        btn_box = QHBoxLayout()
        self.gen_btn = QPushButton("☁️ 同步云端数据")
        self.gen_btn.setMinimumHeight(45)
        self.gen_btn.clicked.connect(self.generate_brief)
        
        self.send_btn = QPushButton("🚀 确认正式推送")
        self.send_btn.setMinimumHeight(45)
        self.send_btn.setStyleSheet("background-color: #0067c0; color: white; border-radius: 6px; font-weight: bold;")
        self.send_btn.clicked.connect(self.send_to_tg)
        
        btn_box.addWidget(self.gen_btn)
        btn_box.addWidget(self.send_btn)
        layout.addLayout(btn_box)

        self.status = QLabel("就绪")
        self.status.setStyleSheet("color: #777; font-size: 11px;")
        layout.addWidget(self.status)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def generate_brief(self):
        self.status.setText("正在执行数据同步...")
        self.worker = BriefWorker()
        self.worker.finished.connect(self.on_fin)
        self.worker.error.connect(self.on_err)
        self.worker.start()

    def on_fin(self, c):
        self.editor.setPlainText(c)
        self.status.setText("完成。")

    def on_err(self, e):
        QMessageBox.warning(self, "同步失败", f"原因：{e}\n\n建议检查网络代理或稍后再试。")

    def send_to_tg(self):
        content = self.editor.toPlainText()
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        try:
            r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": content, "parse_mode": "Markdown"}, verify=False)
            if r.status_code == 200:
                QMessageBox.information(self, "成功", "投递成功！")
            else:
                QMessageBox.warning(self, "失败", r.text)
        except Exception as e:
            QMessageBox.critical(self, "异常", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
