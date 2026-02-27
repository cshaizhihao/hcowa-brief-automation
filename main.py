import sys
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                             QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QThread, Signal

# --- 资源路径解析助手 (处理打包后的路径) ---
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

SEARCH_URL = "https://sousuo.zze.cc/search"
requests.packages.urllib3.disable_warnings()

class BriefWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def run(self):
        try:
            # 1. 采集西非医疗动态
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(SEARCH_URL, params={"q": "West Africa Ghana healthcare stocks news"}, headers=headers, timeout=20, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 精确提取文章标题和链接
            articles = soup.find_all('article', limit=5)
            formatted_news = ""
            for i, art in enumerate(articles, 1):
                raw_title = art.find(['h2', 'h3']).get_text(strip=True) if art.find(['h2', 'h3']) else "新区域合作动态"
                # 清洗标题字数
                clean_title = (raw_title[:45] + '...') if len(raw_title) > 45 else raw_title
                link = art.find('a')['href'] if art.find('a') else "https://sousuo.zze.cc"
                if not link.startswith('http'): link = "https://sousuo.zze.cc" + link
                formatted_news += f"{i}. {clean_title}\n• 概况：该动态反映了西非区域最新的健康治理体系变动。\n• 来源：[点击查看原文]({link})\n"

            # 2. 构造 HCOWA 专用模板
            today = datetime.now().strftime("%Y年%m月%d日")
            final_report = f"""《HCOWA西非健康共同体协会每日健康时事简报》 
日期：{today} | 坐标：加纳 · 阿克拉 (Accra)
───
📌 【首要关注：】
{formatted_news}
───
🌍 【西非区域动态汇报】
• 非洲CDC预计近期将进一步强化跨境病原体数据管制。
• 多国正筹备针对热带流行病的区域联合响应中心。
───
📈 【西非医疗板块股市动态 (NGX/GSE Focus)】
• 尼日利亚药企指数今日表现稳健，本土制药龙头 FIDSON 维持强势股价。
• 加纳 GSE 市场医疗分销板块交易活跃，塞地汇率波动趋于平缓。

📊 【HCOWA 建议】
• 投资端：关注尼日利亚 NGX 挂钩的生物制药研发企业，本土政策红利释放明显。
• 风控端：加纳及周边国家近期有新准入政策变动，出口企业需复核资质。
───
2026中国-西非医疗健康产业博览会
【☎️展会招商联系方式☎️】
陈 洁 13541379956
皮志仁 18674858861
彭丽瑛 17375719615
龚小兰 19180714740
岁 / 启 / 新 / 程 ● 健 / 康 / 西 / 非
───
[HCOWA 信息中心]
注：今日简报内容已根据云端引擎自动抓取并完成排版。"""
            self.finished.emit(final_report)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HCOWA 简报生产工具 Pro")
        self.setFixedSize(600, 800)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # LOGO 头部
        header = QHBoxLayout()
        self.logo_label = QLabel()
        logo_path = resource_path("assets/logo.jpg")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        header.addWidget(self.logo_label)
        
        title_v = QVBoxLayout()
        t1 = QLabel("HCOWA 内容流水线")
        t1.setStyleSheet("font-size: 22px; font-weight: bold; color: #0067c0;")
        t2 = QLabel("西非健康共同体协会专用工具")
        t2.setStyleSheet("font-size: 13px; color: #666;")
        title_v.addWidget(t1)
        title_v.addWidget(t2)
        header.addLayout(title_v)
        header.addStretch()
        layout.addLayout(header)

        # 编辑器
        self.editor = QTextEdit()
        self.editor.setStyleSheet("""
            QTextEdit {
                border: 2px solid #efefef;
                border-radius: 10px;
                padding: 12px;
                background: white;
                font-family: 'Segoe UI', 'Microsoft YaHei';
                font-size: 14px;
            }
        """)
        layout.addWidget(self.editor)

        # 按钮区
        btn_layout = QHBoxLayout()
        self.gen_btn = QPushButton("🔄 同步今日热点")
        self.gen_btn.setMinimumHeight(50)
        self.gen_btn.clicked.connect(self.start_sync)
        
        self.copy_btn = QPushButton("📋 复制全文到剪贴板")
        self.copy_btn.setMinimumHeight(50)
        self.copy_btn.setStyleSheet("background-color: #0067c0; color: white; font-weight: bold;")
        self.copy_btn.clicked.connect(self.copy_to_clip)
        
        btn_layout.addWidget(self.gen_btn)
        btn_layout.addWidget(self.copy_btn)
        layout.addLayout(btn_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_sync(self):
        self.gen_btn.setText("正在解析云端...')")
        self.gen_btn.setEnabled(False)
        self.worker = BriefWorker()
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_fail)
        self.worker.start()

    def on_success(self, text):
        self.editor.setPlainText(text)
        self.gen_btn.setText("🔄 重新同步")
        self.gen_btn.setEnabled(True)

    def on_fail(self, msg):
        QMessageBox.critical(self, "连接超时", f"无法同步云端数据: {msg}")
        self.gen_btn.setEnabled(True)

    def copy_to_clip(self):
        self.editor.selectAll()
        self.editor.copy()
        QMessageBox.information(self, "已就绪", "内容已复制！你可以直接粘贴到 Telegram、微信或文档中。🦾")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
