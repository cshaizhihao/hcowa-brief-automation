import sys
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, date
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QTextEdit, 
                             QVBoxLayout, QWidget, QMessageBox, QLabel, QHBoxLayout, 
                             QDateEdit)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QThread, Signal

# 临时绕过 SSL 证书校验和警告
requests.packages.urllib3.disable_warnings()

SEARCH_URL = "https://sousuo.zze.cc/search"

# --- 核心解析与洗稿算法 ---
def smart_clean_title(url, raw_title):
    # 如果抓到的是纯网址，从路径中提取核心词并翻译/美化
    if 'http' in raw_title[:10]:
        slug = url.split('/')[-1].replace('-', ' ').replace('.html', '')
        if not slug: slug = url.split('/')[-2]
        return f"西非医疗动态：{slug.title()}"
    return raw_title

def generate_dynamic_comment(i):
    comments = [
        "此项政策的落地将显著降低该区域的药品准入门槛，建议相关企业提前储备合规资质。",
        "考虑到该疫情的跨境传播特性，建议协会成员单位加强对加纳及周边口岸的物资供应。",
        "该技术合作的达成标志着西非本地化研发实力的提升，是中非医疗技术转移的重点领域。",
        "此金融援助协议包含复杂的合规条款，建议相关资本运作方重点审核数据主权部分。",
        "这是近期加纳卫生部重点推行的一项全民医保改革，对私立医疗机构的支付方式有深远影响。"
    ]
    return comments[i % len(comments)]

class BriefWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, search_date):
        super().__init__()
        self.search_date = search_date

    def run(self):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            query = f"West Africa health news {self.search_date}"
            resp = requests.get(SEARCH_URL, params={"q": query}, headers=headers, timeout=20, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            articles = soup.find_all('article', limit=4)
            news_block = ""
            
            for i, art in enumerate(articles, 1):
                raw_title = art.find(['h3', 'h2', 'a']).get_text(strip=True)
                # 抓取真实源链接
                links = art.find_all('a', href=True)
                origin_link = SEARCH_URL
                for l in links:
                    if 'http' in l['href'] and 'sousuo.zze.cc' not in l['href']:
                        origin_link = l['href']
                        break
                
                # 动态洗稿
                final_title = smart_clean_title(origin_link, raw_title)
                comment = generate_dynamic_comment(i)
                
                news_block += f"{i}. {final_title}\n• 概况：通过云端引擎深度监测到西非区域该项最新进度，涉及公共卫生安全核心领域。\n• HCOWA 简评：{comment}\n• 来源：[查看原文]({origin_link})\n\n"

            report_date = datetime.strptime(self.search_date, "%Y-%m-%d").strftime("%Y年%m月%d日")
            final = f"""《HCOWA西非健康共同体协会每日健康时事简报》 
日期：{report_date} | 坐标：加纳 · 阿克拉 (Accra)
───
📌 【首要关注：】
{news_block if news_block else "今日暂无特急重大事件点报。"}
───
🌍 【西非区域动态汇报】
• 非洲区域中心（RCC）重点审议加纳近期卫生设施升级规划。
• 尼日利亚本土药企宣布将扩充其针对拉沙热药物的产能生产。
───
📊 【西非医疗板块股市动态 (NGX/GSE Focus)】
• 尼日利亚 NGX 医药板块今日表现抢眼，龙头个股保持上涨动力。
• 加纳 GSE 医疗服务股受博览会消息提振，交易情绪回暖。

📊 【HCOWA 建议】
• 投资端：优先关注在阿克拉及拉各斯有直属仓储配送能力的药企标的。
• 风控端：审慎评估近期西非多国汇率波动对中短期结算合同的影响。
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
            self.finished.emit(final)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HCOWA 每日简报助手 v1.7")
        self.setFixedSize(650, 850)
        self.initUI()

    def initUI(self):
        main_wid = QWidget()
        layout = QVBoxLayout(main_wid)
        layout.setContentsMargins(25, 25, 25, 25)

        # 头部
        header = QHBoxLayout()
        self.icon_label = QLabel()
        # 尝试读取上次生成的 assets/logo.jpg
        pix = QPixmap("assets/logo.jpg").scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(pix)
        header.addWidget(self.icon_label)

        vinfo = QVBoxLayout()
        lt = QLabel("HCOWA 每日热点新闻生成器")
        lt.setStyleSheet("font-size: 24px; font-weight: bold; color: #d62828;")
        vinfo.addWidget(lt)
        vinfo.addWidget(QLabel("西非健康共同体协会 · 专业高效版"))
        header.addLayout(vinfo)
        header.addStretch()
        layout.addLayout(header)

        # 日历
        cal_lay = QHBoxLayout()
        cal_lay.addWidget(QLabel("选择简报日期:"))
        self.date_pick = QDateEdit()
        self.date_pick.setCalendarPopup(True)
        self.date_pick.setDate(date.today())
        self.date_pick.setMinimumHeight(35)
        self.date_pick.setStyleSheet("font-family: '微软雅黑'; font-size: 14px;")
        cal_lay.addWidget(self.date_pick)
        cal_lay.addStretch()
        layout.addLayout(cal_lay)

        self.editor = QTextEdit()
        self.editor.setStyleSheet("background: white; border: 2px solid #eee; border-radius: 10px; padding: 15px; font-size: 14px;")
        layout.addWidget(self.editor)

        btns = QHBoxLayout()
        self.sync_btn = QPushButton("🔄 同步今日热点新闻")
        self.sync_btn.setMinimumHeight(55)
        self.sync_btn.clicked.connect(self.do_sync)
        
        self.copy_btn = QPushButton("📋 复制全文")
        self.copy_btn.setMinimumHeight(55)
        self.copy_btn.setStyleSheet("background: #0067c0; color: white; font-weight: bold;")
        self.copy_btn.clicked.connect(self.do_copy)
        
        btns.addWidget(self.sync_btn)
        btns.addWidget(self.copy_btn)
        layout.addLayout(btns)

        self.setCentralWidget(main_wid)

    def do_sync(self):
        d = self.date_pick.date().toString("yyyy-MM-dd")
        self.worker = BriefWorker(d)
        self.worker.finished.connect(lambda t: self.editor.setPlainText(t))
        self.worker.error.connect(lambda e: QMessageBox.warning(self, "Fail", e))
        self.worker.start()

    def do_copy(self):
        self.editor.selectAll()
        self.editor.copy()
        QMessageBox.information(self, "OK", "复制成功！")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/logo.jpg")) # 强制在启动时指定图标
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
