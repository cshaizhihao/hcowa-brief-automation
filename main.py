"""
HCOWA Daily News Generator v2.2
西非健康共同体协会 · 智能简报系统
Bilingual (ZH/EN) + WeChat Article Expansion
"""
import sys, os, webbrowser, requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from urllib.parse import quote

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
    QLabel, QDateEdit, QFrame, QDialog, QListWidget,
    QListWidgetItem, QDialogButtonBox, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QTextCursor
from PySide6.QtCore import Qt, QThread, Signal, QDate, QLocale

# ── Resource path ───────────────────────────────────────────────────────────
def res(rel):
    base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
    return os.path.join(base, rel)

# ── Constants ───────────────────────────────────────────────────────────────
SEARCH_URL = "https://sousuo.zze.cc/search"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
requests.packages.urllib3.disable_warnings()

# ── i18n strings ────────────────────────────────────────────────────────────
LANGS = {
    "zh": {
        "window_title"    : "HCOWA 每日热点新闻生成器",
        "title"           : "HCOWA 每日热点新闻生成器",
        "subtitle"        : "西非健康共同体协会 · 智能简报系统 v2.2",
        "date_label"      : "📅  简报日期：",
        "today_hint"      : "（今日）",
        "history_hint"    : "（往期回顾）",
        "sync_btn"        : "🔄  同步今日热点新闻",
        "syncing_btn"     : "⟳  正在同步...",
        "copy_btn"        : "📋  复制简报全文",
        "expand_btn"      : "📝  扩写为公众号",
        "lang_btn"        : "🌐  EN",
        "placeholder"     : "请选择日期后，点击「同步今日热点新闻」开始生成简报...",
        "ready_status"    : "✅ 简报已就绪，可复制发布。",
        "fail_status"     : "❌ 同步失败，请检查网络后重试。",
        "copy_ok_title"   : "复制成功",
        "copy_ok_msg"     : "✅ 简报全文已复制！粘贴后即可发布。",
        "no_content_msg"  : "请先点击「同步」生成简报内容。",
        "no_news_msg"     : "请先同步新闻内容，然后选择新闻进行扩写。",
        "sync_fail_title" : "同步失败",
        "select_title"    : "选择新闻扩写为公众号文章",
        "select_label"    : "选择一条新闻，将自动打开豆包并复制提示词：",
        "ok_btn"          : "确定",
        "cancel_btn"      : "取消",
        "expand_ok_title" : "已就绪 ✅",
        "expand_ok_msg"   : "提示词已复制到剪贴板！\n\n豆包已在浏览器中打开，请在对话框中粘贴（Ctrl+V）并发送。",
        "searching"       : "🔍 正在检索西非医疗热点新闻...",
        "backup"          : "⚠️ 主源无结果，切换备用检索...",
        "processing"      : "🌐 正在处理第 {} 条，翻译中...",
        "no_news_text"    : "今日暂未检索到相关重大动态，建议稍后重新同步。\n",
    },
    "en": {
        "window_title"    : "HCOWA Daily News Generator",
        "title"           : "HCOWA Daily News Generator",
        "subtitle"        : "West Africa Health Community Association · Smart Brief v2.2",
        "date_label"      : "📅  Brief Date:",
        "today_hint"      : "(Today)",
        "history_hint"    : "(Archive)",
        "sync_btn"        : "🔄  Sync Today's News",
        "syncing_btn"     : "⟳  Syncing...",
        "copy_btn"        : "📋  Copy Full Brief",
        "expand_btn"      : "📝  Expand to Article",
        "lang_btn"        : "🌐  中文",
        "placeholder"     : "Select a date, then click 'Sync Today's News' to generate...",
        "ready_status"    : "✅ Brief ready. Copy and publish.",
        "fail_status"     : "❌ Sync failed. Check network and retry.",
        "copy_ok_title"   : "Copied",
        "copy_ok_msg"     : "✅ Brief copied to clipboard!",
        "no_content_msg"  : "Please sync news first.",
        "no_news_msg"     : "Please sync news first, then select an item to expand.",
        "sync_fail_title" : "Sync Failed",
        "select_title"    : "Select News → Expand to Article",
        "select_label"    : "Select a news item (Doubao will open and prompt copied to clipboard):",
        "ok_btn"          : "OK",
        "cancel_btn"      : "Cancel",
        "expand_ok_title" : "Ready ✅",
        "expand_ok_msg"   : "Prompt copied!\n\nDobao has opened in your browser — paste (Ctrl+V) and send.",
        "searching"       : "🔍 Searching West Africa health news...",
        "backup"          : "⚠️ No results, switching backup source...",
        "processing"      : "🌐 Processing item {}...",
        "no_news_text"    : "No major updates found today. Please retry later.\n",
    }
}

# ── Comments pool ────────────────────────────────────────────────────────────
COMMENTS = {
    "zh": [
        "此政策变动将直接压缩中间流通环节，建议相关企业提前储备区域合规资质。",
        "跨境协作机制的完善有助于将区域疫情响应窗口期从72小时缩短至24小时。",
        "本土化制造能力的跃升是中非医疗长期健康合作的核心战略支柱。",
        "此类峰会成果通常在6至12个月内转化为正式采购框架协议，值得持续跟踪。",
        "区域资本对公共卫生政策红利的前瞻布局动向，建议密切关注后续落地细节。",
    ],
    "en": [
        "This policy shift may compress distribution channels; prepare regional compliance credentials.",
        "Improved cross-border mechanisms could reduce epidemic response windows from 72 to 24 hours.",
        "Local manufacturing growth is a core strategic pillar for long-term China–Africa medical trade.",
        "Summit outcomes typically convert to procurement agreements within 6–12 months. Track closely.",
        "Forward capital positioning on health policy dividends warrants continuous monitoring.",
    ]
}

# ── Multi-source Translate (CN & Global friendly) ───────────────────────────
def translate(text: str) -> str:
    """
    翻译优先级：
    1. MyMemory API（免费，中国境内可用，无需 Key）
    2. Google Translate API（中国境外兜底）
    任一成功即返回，全部失败则原文返回。
    """
    if not text or not any(c.isalpha() and ord(c) < 128 for c in text):
        return text  # 纯中文或空，无需翻译

    # MyMemory 单次最多 500 字符，超长分段翻译后拼接
    def _mymemory(t):
        chunks, result = [], []
        for i in range(0, len(t), 480):
            chunks.append(t[i:i+480])
        for chunk in chunks:
            r = requests.get(
                f"https://api.mymemory.translated.net/get?q={quote(chunk)}&langpair=en|zh-CN",
                timeout=10, verify=False
            )
            data = r.json()
            if data.get("responseStatus") == 200:
                part = data["responseData"]["translatedText"]
                if part and "MYMEMORY WARNING" not in part:
                    result.append(part)
                    continue
            return None  # 任一分段失败则整体失败
        return "".join(result)

    # ── 方案 1：MyMemory（免费，中国境内可用）────────────────────────
    try:
        out = _mymemory(text)
        if out and out != text:
            return out
    except Exception:
        pass

    # ── 方案 2：Google Translate（境外兜底）──────────────────────────
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=auto&tl=zh-CN&dt=t&q={quote(text)}",
            timeout=10, verify=False
        )
        return "".join(seg[0] for seg in r.json()[0] if seg[0])
    except Exception:
        pass

    return text  # 全部失败，原文返回

# ── Background worker ────────────────────────────────────────────────────────
class BriefWorker(QThread):
    finished   = Signal(str)
    news_ready = Signal(list)
    error      = Signal(str)
    progress   = Signal(str)

    def __init__(self, target_date: str, lang: str = "zh"):
        super().__init__()
        self.target_date = target_date
        self.lang = lang

    def run(self):
        L = LANGS[self.lang]
        try:
            self.progress.emit(L["searching"])
            resp = requests.get(
                SEARCH_URL,
                params={"q": f"West Africa health medical news {self.target_date}"},
                headers=HEADERS, timeout=25, verify=False
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.find_all("article", limit=4)

            if not articles:
                self.progress.emit(L["backup"])
                resp2 = requests.get(
                    SEARCH_URL,
                    params={"q": f"Ghana Nigeria healthcare {self.target_date}"},
                    headers=HEADERS, timeout=20, verify=False
                )
                soup = BeautifulSoup(resp2.text, "html.parser")
                articles = soup.find_all("article", limit=4)

            news_items = []
            news_block = ""
            comments   = COMMENTS[self.lang]

            for i, art in enumerate(articles, 1):
                self.progress.emit(L["processing"].format(i))

                # Title — 完整提取，不截断
                raw_title = ""
                for tag in ("h3", "h2", "a"):
                    el = art.find(tag)
                    if el:
                        t = el.get_text(strip=True)
                        # 过滤掉纯 URL 或过短的文本
                        if t and not t.startswith("http") and len(t) > 5:
                            raw_title = t
                            break
                title_out = (translate(raw_title) if (self.lang == "zh" and raw_title) else raw_title) \
                            or (f"西非医疗动态 #{i}" if self.lang == "zh" else f"W. Africa Health Update #{i}")

                # Snippet — 完整提取，不截断（最多取 3 个 p 段合并）
                snippet_parts = []
                for p in art.find_all("p"):
                    t = p.get_text(strip=True)
                    if len(t) > 15:
                        snippet_parts.append(t)
                    if len(snippet_parts) >= 2:
                        break
                snippet_raw = " ".join(snippet_parts)
                snippet_out = (translate(snippet_raw) if (self.lang == "zh" and snippet_raw) else snippet_raw) \
                              or ("详情请访问原文链接。" if self.lang == "zh" else "See source for details.")

                # URL
                link = SEARCH_URL
                for a in art.find_all("a", href=True):
                    h = a["href"]
                    if h.startswith("http") and "sousuo.zze.cc" not in h:
                        link = h
                        break

                news_items.append({"title": title_out, "url": link, "snippet": snippet_out})
                comment = comments[i % len(comments)]

                if self.lang == "zh":
                    news_block += (
                        f"{i}. {title_out}\n"
                        f"• 概况：{snippet_out}\n"
                        f"• HCOWA 简评：{comment}\n"
                        f"• 来源：{link}\n\n"
                    )
                else:
                    news_block += (
                        f"{i}. {title_out}\n"
                        f"• Summary: {snippet_out}\n"
                        f"• HCOWA Note: {comment}\n"
                        f"• Source: {link}\n\n"
                    )

            self.news_ready.emit(news_items)
            if not news_block:
                news_block = L["no_news_text"]

            d        = datetime.strptime(self.target_date, "%Y-%m-%d")
            is_today = (self.target_date == date.today().strftime("%Y-%m-%d"))

            if self.lang == "zh":
                date_str = d.strftime("%Y年%m月%d日") + ("（今日）" if is_today else "")
                report = (
                    "《HCOWA西非健康共同体协会每日健康时事简报》\n"
                    f"日期：{date_str} | 坐标：加纳 · 阿克拉 (Accra)\n"
                    "───\n"
                    "📌 【首要关注：】\n"
                    f"{news_block}"
                    "───\n"
                    "🌍 【西非区域动态汇报】\n"
                    "• 区域内多国联合推进传统医学标准化认证体系建设。\n"
                    "• 非洲疾控中心持续跟进猴痘及登革热的区域扩散风险。\n"
                    "───\n"
                    "📊 【西非医疗板块股市动态 (NGX/GSE)】\n"
                    "• 尼日利亚 NGX 医药板块延续强势，龙头个股获机构加仓。\n"
                    "• 加纳 GSE 市场受国际资本流入驱动，医疗分销板块交投活跃。\n\n"
                    "📋 【HCOWA 建议】\n"
                    "• 投资端：重点关注在拉各斯及阿克拉具备独立分销体系的药企。\n"
                    "• 风控端：及时审查西非各国近期颁布的医疗设备进口许可细则变动。\n"
                    "───\n"
                    "2026中国-西非医疗健康产业博览会\n"
                    "【☎️ 展会招商联系方式 ☎️】\n"
                    "陈 洁  13541379956\n"
                    "皮志仁  18674858861\n"
                    "彭丽瑛  17375719615\n"
                    "龚小兰  19180714740\n"
                    "岁 / 启 / 新 / 程 ● 健 / 康 / 西 / 非\n"
                    "───\n"
                    "[HCOWA 信息中心]"
                )
            else:
                date_str = d.strftime("%B %d, %Y") + (" (Today)" if is_today else "")
                report = (
                    "HCOWA West Africa Health Community Daily Brief\n"
                    f"Date: {date_str} | Location: Accra, Ghana\n"
                    "───\n"
                    "📌 [Key Focus]\n"
                    f"{news_block}"
                    "───\n"
                    "🌍 [Regional Updates]\n"
                    "• Multi-country collaboration on traditional medicine standardization continues.\n"
                    "• Africa CDC monitors monkeypox and dengue fever spread across the region.\n"
                    "───\n"
                    "📊 [Healthcare Stock Watch (NGX/GSE)]\n"
                    "• Nigeria NGX pharma index maintains upward trend; institutions accumulating.\n"
                    "• Ghana GSE medical distribution sector active amid international capital inflows.\n\n"
                    "📋 [HCOWA Recommendations]\n"
                    "• Investment: Focus on pharma firms with Lagos/Accra independent distribution.\n"
                    "• Risk: Monitor recent medical device import licensing changes across West Africa.\n"
                    "───\n"
                    "2026 China–West Africa Medical & Health Industry Expo\n"
                    "[☎️ Expo Business Contacts ☎️]\n"
                    "Chen Jie      +86 13541379956\n"
                    "Pi Zhiren     +86 18674858861\n"
                    "Peng Liying   +86 17375719615\n"
                    "Gong Xiaolan  +86 19180714740\n"
                    "New Era ● Healthy West Africa\n"
                    "───\n"
                    "[HCOWA Information Center]"
                )

            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))


# ── News selection dialog ────────────────────────────────────────────────────
class NewsSelectDialog(QDialog):
    def __init__(self, news_items: list, lang: str, parent=None):
        super().__init__(parent)
        L = LANGS[lang]
        self.setWindowTitle(L["select_title"])
        self.setFixedSize(560, 340)
        self.selected_url   = None
        self.selected_title = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        lbl = QLabel(L["select_label"])
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px;")
        lay.addWidget(lbl)

        self.lst = QListWidget()
        self.lst.setAlternatingRowColors(True)
        self.lst.setStyleSheet("font-size: 13px; border-radius: 6px; border: 1px solid #dde3ec;")
        for item in news_items:
            li = QListWidgetItem(f"  {item['title']}")
            li.setData(Qt.UserRole, item["url"])
            li.setToolTip(item["url"])
            self.lst.addItem(li)
        if self.lst.count():
            self.lst.setCurrentRow(0)
        self.lst.doubleClicked.connect(self._accept)
        lay.addWidget(self.lst)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(L["ok_btn"])
        btns.button(QDialogButtonBox.Cancel).setText(L["cancel_btn"])
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _accept(self):
        cur = self.lst.currentItem()
        if cur:
            self.selected_url   = cur.data(Qt.UserRole)
            self.selected_title = cur.text().strip()
            self.accept()


# ── Main window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    QSS = """
    QMainWindow, QWidget { background: #f0f2f5;
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif; }
    QLabel { color: #1a1a2e; }
    QTextEdit {
        background: #fff; border: 1.5px solid #dde3ec;
        border-radius: 10px; padding: 14px;
        font-size: 13px; color: #222; line-height: 1.8; }
    QDateEdit {
        background: #fff; border: 1.5px solid #c9d3df;
        border-radius: 6px; padding: 5px 10px;
        font-size: 13px; min-width: 150px; min-height: 34px;
        font-family: "Segoe UI", "Microsoft YaHei UI"; }
    QDateEdit::drop-down { width: 24px; }
    QPushButton { border-radius: 8px; font-size: 13px;
        font-weight: bold; padding: 10px 16px; }
    QPushButton#syncBtn {
        background: #f4f6f8; border: 1.5px solid #c9d3df; color: #2c3e50; }
    QPushButton#syncBtn:hover   { background: #e8f0fe; border-color: #4285f4; }
    QPushButton#syncBtn:disabled { color: #aaa; background: #f0f0f0; }
    QPushButton#copyBtn {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #1a73e8, stop:1 #0d47a1);
        border: none; color: white; }
    QPushButton#copyBtn:hover { background: #1557b0; }
    QPushButton#expandBtn {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
            stop:0 #2e7d32, stop:1 #1b5e20);
        border: none; color: white; }
    QPushButton#expandBtn:hover { background: #245c27; }
    QPushButton#expandBtn:disabled { background: #90b090; }
    QPushButton#langBtn {
        background: #fff3e0; border: 1.5px solid #ffb74d;
        color: #e65100; font-size: 12px; padding: 6px 12px; }
    QPushButton#langBtn:hover { background: #ffe0b2; }
    QFrame#hr { background: #e2e6ea; max-height: 1px; }
    QLabel#status { color: #7f8c8d; font-size: 11px; }
    QLabel#zaki   { color: #bdc3c7; font-size: 11px; font-style: italic; }
    """

    def __init__(self):
        super().__init__()
        self.lang       = "zh"
        self.news_items = []
        self.setFixedSize(720, 880)
        self.setStyleSheet(self.QSS)
        self._build()
        self._load_icon()
        self._apply_lang()

    # ── Build UI ─────────────────────────────────────────────────────────────
    def _build(self):
        root = QWidget()
        lay  = QVBoxLayout(root)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.setSpacing(14)

        # Header
        hdr = QHBoxLayout(); hdr.setSpacing(14)
        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(72, 72)
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        hdr.addWidget(self.logo_lbl)

        info = QVBoxLayout(); info.setSpacing(3)
        self.title_lbl    = QLabel()
        self.title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #c0392b;")
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        info.addWidget(self.title_lbl)
        info.addWidget(self.subtitle_lbl)
        hdr.addLayout(info)
        hdr.addStretch()

        # Language toggle in header
        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("langBtn")
        self.lang_btn.setFixedHeight(36)
        self.lang_btn.clicked.connect(self._toggle_lang)
        hdr.addWidget(self.lang_btn)
        lay.addLayout(hdr)

        # Divider
        hr = QFrame(); hr.setObjectName("hr"); lay.addWidget(hr)

        # Date row
        drow = QHBoxLayout()
        self.date_lbl = QLabel()
        self.date_lbl.setStyleSheet("font-size: 13px; font-weight: bold;")
        drow.addWidget(self.date_lbl)

        self.dp = QDateEdit()
        self.dp.setLocale(QLocale(QLocale.Language.C))
        self.dp.setDisplayFormat("yyyy-MM-dd")
        self.dp.setCalendarPopup(True)
        today = QDate.currentDate()
        self.dp.setDate(today)
        self.dp.setMaximumDate(today)
        cal = self.dp.calendarWidget()
        if cal:
            cal.setLocale(QLocale(QLocale.Language.C))
        self.dp.dateChanged.connect(self._date_hint)
        drow.addWidget(self.dp)

        self.hint_lbl = QLabel()
        self.hint_lbl.setStyleSheet("color: #27ae60; font-size: 12px;")
        drow.addWidget(self.hint_lbl)
        drow.addStretch()
        lay.addLayout(drow)

        # Editor
        self.editor = QTextEdit()
        lay.addWidget(self.editor)

        # Status
        self.status = QLabel()
        self.status.setObjectName("status")
        lay.addWidget(self.status)

        # Bottom buttons
        foot = QHBoxLayout(); foot.setSpacing(10)

        self.sync_btn   = QPushButton(); self.sync_btn.setObjectName("syncBtn")
        self.copy_btn   = QPushButton(); self.copy_btn.setObjectName("copyBtn")
        self.expand_btn = QPushButton(); self.expand_btn.setObjectName("expandBtn")

        for b in (self.sync_btn, self.copy_btn, self.expand_btn):
            b.setMinimumHeight(52)

        self.sync_btn.clicked.connect(self._sync)
        self.copy_btn.clicked.connect(self._copy)
        self.expand_btn.clicked.connect(self._expand)

        zaki = QLabel("Zaki"); zaki.setObjectName("zaki")
        zaki.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        foot.addWidget(self.sync_btn)
        foot.addWidget(self.copy_btn)
        foot.addWidget(self.expand_btn)
        foot.addWidget(zaki)
        lay.addLayout(foot)

        self.setCentralWidget(root)

    # ── Icon ─────────────────────────────────────────────────────────────────
    def _load_icon(self):
        for p in (res("assets/logo.png"), res("assets/logo.jpg")):
            if os.path.exists(p):
                self.logo_lbl.setPixmap(
                    QPixmap(p).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                ico = res("assets/icon.ico")
                self.setWindowIcon(QIcon(ico if os.path.exists(ico) else p))
                break

    # ── Language ──────────────────────────────────────────────────────────────
    def _toggle_lang(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        self._apply_lang()

    def _apply_lang(self):
        L = LANGS[self.lang]
        self.setWindowTitle(L["window_title"])
        self.title_lbl.setText(L["title"])
        self.subtitle_lbl.setText(L["subtitle"])
        self.date_lbl.setText(L["date_label"])
        self.sync_btn.setText(L["sync_btn"])
        self.copy_btn.setText(L["copy_btn"])
        self.expand_btn.setText(L["expand_btn"])
        self.lang_btn.setText(L["lang_btn"])
        self.editor.setPlaceholderText(L["placeholder"])
        self.status.setText(LANGS[self.lang]["ready_status"] if self.editor.toPlainText()
                            else ("就绪" if self.lang == "zh" else "Ready"))
        self._date_hint(self.dp.date())

    # ── Date hint ─────────────────────────────────────────────────────────────
    def _date_hint(self, qd: QDate):
        L = LANGS[self.lang]
        is_today = (qd == QDate.currentDate())
        self.hint_lbl.setText(L["today_hint"] if is_today else L["history_hint"])
        self.hint_lbl.setStyleSheet(
            f"color: {'#27ae60' if is_today else '#e67e22'}; font-size: 12px;"
        )

    # ── Sync ──────────────────────────────────────────────────────────────────
    def _sync(self):
        target = self.dp.date().toString("yyyy-MM-dd")
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText(LANGS[self.lang]["syncing_btn"])
        self.editor.clear()
        self.news_items = []
        self.expand_btn.setEnabled(False)

        self.worker = BriefWorker(target, self.lang)
        self.worker.progress.connect(lambda m: self.status.setText(m))
        self.worker.news_ready.connect(lambda items: setattr(self, "news_items", items) or
                                                      self.expand_btn.setEnabled(bool(items)))
        self.worker.finished.connect(self._on_ok)
        self.worker.error.connect(self._on_err)
        self.worker.start()

    def _on_ok(self, text):
        self.editor.setPlainText(text)
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText(LANGS[self.lang]["sync_btn"])
        self.status.setText(LANGS[self.lang]["ready_status"])

    def _on_err(self, msg):
        L = LANGS[self.lang]
        QMessageBox.warning(self, L["sync_fail_title"], f"{msg}\n\n{'请检查网络后重试。' if self.lang=='zh' else 'Check network and retry.'}")
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText(L["sync_btn"])
        self.status.setText(L["fail_status"])

    # ── Copy ──────────────────────────────────────────────────────────────────
    def _copy(self):
        L = LANGS[self.lang]
        if not self.editor.toPlainText():
            QMessageBox.information(self, "💡", L["no_content_msg"]); return
        self.editor.selectAll(); self.editor.copy()
        self.editor.moveCursor(QTextCursor.MoveOperation.Start)
        QMessageBox.information(self, L["copy_ok_title"], L["copy_ok_msg"])

    # ── Expand to article ─────────────────────────────────────────────────────
    def _expand(self):
        L = LANGS[self.lang]
        if not self.news_items:
            QMessageBox.information(self, "💡", L["no_news_msg"]); return

        dlg = NewsSelectDialog(self.news_items, self.lang, self)
        if dlg.exec() != QDialog.Accepted or not dlg.selected_url:
            return

        url    = dlg.selected_url
        # Doubao prompt — always Chinese (it's a Chinese AI tool)
        prompt = f"根据这个网页 {url}，扩写成微信公众号文章（附上新闻中的来源网页）"

        QApplication.clipboard().setText(prompt)
        webbrowser.open("https://www.doubao.com/chat/")

        QMessageBox.information(self, L["expand_ok_title"], L["expand_ok_msg"])


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ico = res("assets/icon.ico")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
