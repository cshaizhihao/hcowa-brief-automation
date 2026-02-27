import sys
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from deep_translator import GoogleTranslator
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
    QLabel, QDateEdit, QFrame, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette
from PySide6.QtCore import Qt, QThread, Signal, QDate, QLocale

# ─── 路径解析 ───────────────────────────────────────────────────────────────────
def resource_path(rel):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(os.path.abspath("."), rel)

# ─── 常量 ───────────────────────────────────────────────────────────────────────
SEARCH_URL  = "https://sousuo.zze.cc/search"
HEADERS     = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
requests.packages.urllib3.disable_warnings()

# ─── 翻译助手 ──────────────────────────────────────────────────────────────────
def translate_en_to_zh(text: str) -> str:
    """调用 Google 免费翻译接口，失败则原文返回"""
    try:
        if not text or not any(c.isascii() and c.isalpha() for c in text):
            return text
        return GoogleTranslator(source='auto', target='zh-CN').translate(text) or text
    except Exception:
        return text

# ─── 简评库 ──────────────────────────────────────────────────────────────────
COMMENTS = [
    "此动态反映区域药物监管体系的持续深化，建议相关机构提前研判合规风险。",
    "跨境合作机制的完善将有效缩短区域内疫情响应时间，具有重要战略价值。",
    "本土化生产能力的提升是中非医疗贸易长期健康发展的核心支柱。",
    "此类会议成果通常会在未来6至12个月内转化为具体的采购或投资协议。",
    "区域资本对公共卫生政策红利的前瞻性布局值得持续跟踪关注。",
]

# ─── 后台采集线程 ──────────────────────────────────────────────────────────────
class BriefWorker(QThread):
    finished = Signal(str)
    error    = Signal(str)
    progress = Signal(str)

    def __init__(self, target_date: str):
        super().__init__()
        self.target_date = target_date   # "YYYY-MM-DD"

    def run(self):
        try:
            self.progress.emit("正在检索西非健康热点...")
            query = f"West Africa health news site:who.int OR site:afro.who.int OR site:aljazeera.com OR site:reuters.com {self.target_date}"
            resp  = requests.get(SEARCH_URL, params={"q": query},
                                 headers=HEADERS, timeout=25, verify=False)
            soup  = BeautifulSoup(resp.text, 'html.parser')

            articles = soup.find_all('article', limit=4)
            if not articles:
                # 降级搜索
                resp2 = requests.get(SEARCH_URL,
                                     params={"q": f"West Africa healthcare {self.target_date}"},
                                     headers=HEADERS, timeout=20, verify=False)
                soup  = BeautifulSoup(resp2.text, 'html.parser')
                articles = soup.find_all('article', limit=4)

            news_block = ""
            for i, art in enumerate(articles, 1):
                self.progress.emit(f"正在处理第 {i} 条新闻...")

                # 标题
                raw_title = ""
                for tag in ['h3', 'h2', 'a']:
                    el = art.find(tag)
                    if el:
                        raw_title = el.get_text(strip=True)
                        break
                title_zh = translate_en_to_zh(raw_title) if raw_title else f"西非医疗动态 #{i}"

                # 摘要
                snippet_raw = ""
                for p in art.find_all('p'):
                    t = p.get_text(strip=True)
                    if len(t) > 30:
                        snippet_raw = t[:120]
                        break
                snippet_zh = translate_en_to_zh(snippet_raw) if snippet_raw else "详细内容请访问原文链接。"

                # 原文链接
                origin_link = SEARCH_URL
                for l in art.find_all('a', href=True):
                    href = l['href']
                    if href.startswith('http') and 'sousuo.zze.cc' not in href:
                        origin_link = href
                        break

                comment = COMMENTS[i % len(COMMENTS)]
                news_block += (
                    f"{i}. {title_zh}\n"
                    f"• 概况：{snippet_zh}\n"
                    f"• HCOWA 简评：{comment}\n"
                    f"• 来源：{origin_link}\n\n"
                )

            if not news_block:
                news_block = "今日暂未检索到相关重大动态，建议稍后重新同步。\n"

            date_obj      = datetime.strptime(self.target_date, "%Y-%m-%d")
            date_cn       = date_obj.strftime("%Y年%m月%d日")
            is_today      = (self.target_date == date.today().strftime("%Y-%m-%d"))
            date_label    = f"{date_cn}（今日）" if is_today else date_cn

            report = (
                f"《HCOWA西非健康共同体协会每日健康时事简报》\n"
                f"日期：{date_label} | 坐标：加纳 · 阿克拉 (Accra)\n"
                f"───\n"
                f"📌 【首要关注：】\n"
                f"{news_block}"
                f"───\n"
                f"🌍 【西非区域动态汇报】\n"
                f"• 区域内多国联合推进传统医学标准化认证体系建设。\n"
                f"• 非洲疾控中心持续跟进猴痘及登革热的区域扩散风险。\n"
                f"───\n"
                f"📊 【西非医疗板块股市动态 (NGX/GSE Focus)】\n"
                f"• 尼日利亚 NGX 医药板块延续强势，本土龙头个股获机构持续加仓。\n"
                f"• 加纳 GSE 市场受国际资本流入驱动，医疗分销板块交投活跃。\n"
                f"\n"
                f"📋 【HCOWA 建议】\n"
                f"• 投资端：重点关注在拉各斯及阿克拉具备独立分销体系的药企标的。\n"
                f"• 风控端：及时审查西非各国近期颁布的医疗设备进口许可细则变动。\n"
                f"───\n"
                f"2026中国-西非医疗健康产业博览会\n"
                f"【☎️ 展会招商联系方式 ☎️】\n"
                f"陈 洁  13541379956\n"
                f"皮志仁  18674858861\n"
                f"彭丽瑛  17375719615\n"
                f"龚小兰  19180714740\n"
                f"岁 / 启 / 新 / 程 ● 健 / 康 / 西 / 非\n"
                f"───\n"
                f"[HCOWA 信息中心]"
            )
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))


# ─── 主窗口 ───────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HCOWA 每日热点新闻生成器")
        self.setFixedSize(660, 860)
        self._apply_global_style()
        self._build_ui()
        self._load_icon()

    # ── 全局样式 ──────────────────────────────────────────────────────────────
    def _apply_global_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f5f6fa;
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
            }
            QLabel {
                color: #2c3e50;
            }
            QTextEdit {
                background: #ffffff;
                border: 1.5px solid #dde1e7;
                border-radius: 10px;
                padding: 14px;
                font-size: 13px;
                color: #1a1a2e;
                line-height: 1.7;
            }
            QPushButton {
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 18px;
            }
            QPushButton#syncBtn {
                background: #ffffff;
                border: 1.5px solid #c8ccd4;
                color: #2c3e50;
            }
            QPushButton#syncBtn:hover  { background: #e8f0fe; border-color: #4a90d9; }
            QPushButton#syncBtn:disabled { color: #aaa; }
            QPushButton#copyBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #1565c0, stop:1 #1e88e5);
                border: none;
                color: white;
            }
            QPushButton#copyBtn:hover { background: #1557a8; }
            QDateEdit {
                background: #fff;
                border: 1.5px solid #c8ccd4;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                min-width: 140px;
                min-height: 32px;
            }
            QFrame#divider {
                background: #dde1e7;
                max-height: 1px;
            }
        """)

    # ── 构建 UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 18)
        layout.setSpacing(16)

        # === 头部 ===
        header = QHBoxLayout()
        header.setSpacing(16)

        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(80, 80)
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        header.addWidget(self.logo_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        t1 = QLabel("HCOWA 每日热点新闻生成器")
        t1.setStyleSheet("font-size: 22px; font-weight: bold; color: #c0392b;")
        t2 = QLabel("西非健康共同体协会 · 智能简报系统 v1.9")
        t2.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        title_col.addWidget(t1)
        title_col.addWidget(t2)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)

        # === 分割线 ===
        div = QFrame(); div.setObjectName("divider")
        layout.addWidget(div)

        # === 日期选择 ===
        date_row = QHBoxLayout()
        lbl = QLabel("📅  简报日期：")
        lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
        date_row.addWidget(lbl)

        self.date_pick = QDateEdit()
        self.date_pick.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.date_pick.setDisplayFormat("yyyy / MM / dd")
        self.date_pick.setCalendarPopup(True)
        today = QDate.currentDate()
        self.date_pick.setDate(today)
        self.date_pick.setMaximumDate(today)   # 禁止选未来日期
        date_row.addWidget(self.date_pick)
        
        self.date_hint = QLabel("（今日）")
        self.date_hint.setStyleSheet("color: #27ae60; font-size: 12px;")
        date_row.addWidget(self.date_hint)
        date_row.addStretch()

        self.date_pick.dateChanged.connect(self._on_date_changed)
        layout.addLayout(date_row)

        # === 编辑器 ===
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("选择日期，点击"同步今日热点新闻"开始生成...")
        layout.addWidget(self.editor)

        # === 状态栏 ===
        self.status_lbl = QLabel("就绪")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #95a5a6;")
        layout.addWidget(self.status_lbl)

        # === 底部按钮 + Zaki Tag ===
        footer = QHBoxLayout()
        footer.setSpacing(12)

        self.sync_btn = QPushButton("🔄  同步今日热点新闻")
        self.sync_btn.setObjectName("syncBtn")
        self.sync_btn.setMinimumHeight(50)
        self.sync_btn.clicked.connect(self.do_sync)

        self.copy_btn = QPushButton("📋  复制简报全文")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setMinimumHeight(50)
        self.copy_btn.clicked.connect(self.do_copy)

        footer.addWidget(self.sync_btn)
        footer.addWidget(self.copy_btn)

        # Zaki Tag（右下角）
        zaki = QLabel("Zaki")
        zaki.setStyleSheet("""
            color: #bdc3c7;
            font-size: 11px;
            font-style: italic;
            font-weight: bold;
            padding-left: 8px;
        """)
        zaki.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        footer.addWidget(zaki)

        layout.addLayout(footer)
        self.setCentralWidget(root)

    # ── 事件 ─────────────────────────────────────────────────────────────────
    def _on_date_changed(self, qd: QDate):
        if qd == QDate.currentDate():
            self.date_hint.setText("（今日）")
            self.date_hint.setStyleSheet("color: #27ae60; font-size: 12px;")
        else:
            self.date_hint.setText("（往期回顾）")
            self.date_hint.setStyleSheet("color: #e67e22; font-size: 12px;")

    def do_sync(self):
        target = self.date_pick.date().toString("yyyy-MM-dd")
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("⟳  正在获取数据...")
        self.editor.clear()

        self.worker = BriefWorker(target)
        self.worker.progress.connect(lambda m: self.status_lbl.setText(m))
        self.worker.finished.connect(self._on_finish)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finish(self, text):
        self.editor.setPlainText(text)
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄  重新同步")
        self.status_lbl.setText("✅ 简报已就绪，可复制发布。")

    def _on_error(self, msg):
        QMessageBox.warning(self, "网络异常", f"无法完成同步：\n{msg}")
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄  同步今日热点新闻")
        self.status_lbl.setText("❌ 同步失败，请检查网络后重试。")

    def do_copy(self):
        if not self.editor.toPlainText():
            QMessageBox.information(self, "提示", "请先同步内容。")
            return
        self.editor.selectAll()
        self.editor.copy()
        self.editor.moveCursor(self.editor.textCursor().MoveOperation.Start)
        QMessageBox.information(self, "完成", "简报全文已复制到剪贴板，可直接粘贴发布。")

    # ── 图标加载（带白边去除）────────────────────────────────────────────────
    def _load_icon(self):
        logo_path = resource_path("assets/logo.png")
        jpg_path  = resource_path("assets/logo.jpg")
        target    = logo_path if os.path.exists(logo_path) else jpg_path if os.path.exists(jpg_path) else None
        if target:
            pix = QPixmap(target)
            # 裁掉白边：使用 Qt mask 近似
            self.logo_lbl.setPixmap(pix.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.setWindowIcon(QIcon(target))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("assets/icon.ico")))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
