import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                             QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout, 
                             QDateEdit)
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtCore import Qt, QThread, Signal

# --- 路径处理 ---
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

SEARCH_URL = "https://sousuo.zze.cc/search"
requests.packages.urllib3.disable_warnings()

class BriefWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, search_date):
        super().__init__()
        self.search_date = search_date

    def run(self):
        try:
            # 强化爬虫：抓取摘要和真实链接
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            query = f"West Africa health news {self.search_date}"
            resp = requests.get(SEARCH_URL, params={"q": query}, headers=headers, timeout=25, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            articles = soup.find_all('article', limit=4)
            news_items = ""
            
            for i, art in enumerate(articles, 1):
                # 1. 抓标题
                title_tag = art.find(['h3', 'h2', 'a'])
                title = title_tag.get_text(strip=True) if title_tag else "最新健康简讯"
                if len(title) > 50: title = title[:47] + "..."

                # 2. 抓链接（去重逻辑）
                origin_link = SEARCH_URL
                for l in art.find_all('a', href=True):
                    href = l['href']
                    if href.startswith('http') and 'sousuo.zze.cc' not in href:
                        origin_link = href
                        break

                # 3. 抓摘要（概况）
                content_tag = art.find('p', class_='content') or art.find('p')
                snippet = content_tag.get_text(strip=True) if content_tag else "区域公共卫生管理动态细则更新中..."
                if len(snippet) > 80: snippet = snippet[:77] + "..."

                # 4. 构造条目 (移除 Markdown，直接显示链接)
                news_items += f"{i}. {title}\n• 概况：{snippet}\n• 来源：{origin_link}\n\n"

            # 5. 组装总表
            date_obj = datetime.strptime(self.search_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%Y年%m月%d日")
            
            report = f"""《HCOWA西非健康共同体协会每日健康时事简报》 
日期：{formatted_date} | 坐标：加纳 · 阿克拉 (Accra)
───
📌 【首要关注：】
{news_items if news_items else "今日暂无特急重大事件记录。"}
───
🌍 【西非区域动态汇报】
• 区域内正在审议新的人才引进及医疗设施升级补贴方案。
───
📈 【西非医疗板块股市动态 (NGX/GSE Focus)】
• 尼日利亚医药巨头核心财务指标向好。
• 加纳资本市场对大型博览会预期强烈。

📊 【HCOWA 建议】
• 政策层面：建议关注西非多国近期颁布的传统药物监管条例。
• 投资层面：西非本地分销渠道具有极高的准入价值。
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
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HCOWA 每日热点新闻生成器")
        self.setFixedSize(600, 850)
        self.initUI()

    def initUI(self):
        main_wid = QWidget()
        layout = QVBoxLayout(main_wid)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # 头部 Logo 和标题
        header = QHBoxLayout()
        self.logo = QLabel()
        l_path = resource_path("assets/logo.jpg")
        if os.path.exists(l_path):
            self.logo.setPixmap(QPixmap(l_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header.addWidget(self.logo)
        
        info = QVBoxLayout()
        t = QLabel("HCOWA 每日热点新闻生成器")
        t.setStyleSheet("font-size: 20px; font-weight: bold; color: #d62828;")
        info.addWidget(t)
        info.addWidget(QLabel("西非健康共同体协会 · 内容自动化工作站"))
        header.addLayout(info)
        header.addStretch()
        layout.addLayout(header)

        # 日期选择 (修复乱码)
        cal_lay = QHBoxLayout()
        l_date = QLabel("选择简报日期:")
        l_date.setFont(QFont("微软雅黑", 10))
        cal_lay.addWidget(l_date)
        
        self.date_pick = QDateEdit()
        # 强制设置字体和格式
        self.date_pick.setFont(QFont("Segoe UI", 11))
        self.date_pick.setDisplayFormat("yyyy/MM/dd")
        self.date_pick.setCalendarPopup(True)
        self.date_pick.setDate(date.today())
        self.date_pick.setMinimumHeight(35)
        self.date_pick.setMinimumWidth(150)
        cal_lay.addWidget(self.date_pick)
        cal_lay.addStretch()
        layout.addLayout(cal_lay)

        # 编辑器
        self.editor = QTextEdit()
        self.editor.setStyleSheet("border-radius: 8px; border: 1px solid #ccc; background: #fff; padding: 10px; font-size: 14px;")
        layout.addWidget(self.editor)

        # 动作按钮
        btn_box = QHBoxLayout()
        self.sync_btn = QPushButton("🔄 同步今日热点新闻")
        self.sync_btn.setMinimumHeight(55)
        self.sync_btn.clicked.connect(self.do_sync)
        
        self.copy_btn = QPushButton("📋 复制简报全文")
        self.copy_btn.setMinimumHeight(55)
        self.copy_btn.setStyleSheet("background: #0067c0; color: white; font-weight: bold;")
        self.copy_btn.clicked.connect(self.do_copy)
        
        btn_box.addWidget(self.sync_btn)
        btn_box.addWidget(self.copy_btn)
        layout.addLayout(btn_box)

        self.setCentralWidget(main_wid)

    def do_sync(self):
        d = self.date_pick.date().toString("yyyy-MM-dd")
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("正在执行云端同步...")
        self.worker = BriefWorker(d)
        self.worker.finished.connect(lambda t: self.on_fin(t))
        self.worker.error.connect(lambda e: self.on_err(e))
        self.worker.start()

    def on_fin(self, text):
        self.editor.setPlainText(text)
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄 重新同步")

    def on_err(self, msg):
        QMessageBox.warning(self, "同步中断", msg)
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄 重新同步")

    def do_copy(self):
        self.editor.selectAll()
        self.editor.copy()
        QMessageBox.information(self, "完成", "内容已复制，可直接粘贴。🦾")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/logo.jpg")))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
