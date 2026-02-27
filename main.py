"""
HCOWA 每日热点新闻生成器 v2.0
西非健康共同体协会 · 智能简报系统
"""
import sys
import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
from urllib.parse import quote

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QWidget, QMessageBox,
    QLabel, QDateEdit, QFrame, QSizePolicy, QCalendarWidget
)
from PySide6.QtGui import QIcon, QPixmap, QFont, QTextCursor
from PySide6.QtCore import Qt, QThread, Signal, QDate, QLocale

# ─── 路径解析（打包后兼容）──────────────────────────────────────────
def res(rel):
    base = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
    return os.path.join(base, rel)

# ─── 常量 ────────────────────────────────────────────────────────────
SEARCH_URL = "https://sousuo.zze.cc/search"
HEADERS    = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
requests.packages.urllib3.disable_warnings()

COMMENTS = [
    "此政策变动将直接压缩中间流通环节，建议相关企业提前储备区域合规资质。",
    "跨境协作机制的完善有助于将区域疫情响应窗口期从72小时缩短至24小时。",
    "本土化制造能力的跃升是中非医疗长期健康合作的核心战略支柱。",
    "此类峰会成果通常在6至12个月内转化为正式采购框架协议，值得持续跟踪。",
    "区域资本对公共卫生政策红利的前瞻布局动向，建议密切关注后续落地细节。",
]

# ─── 翻译（直接调 Google 官方接口，无需第三方库）──────────────────
def translate(text: str) -> str:
    if not text:
        return text
    # 判断是否需要翻译（含英文字母）
    if not any(c.isalpha() and ord(c) < 128 for c in text):
        return text
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=auto&tl=zh-CN&dt=t&q={quote(text)}"
        )
        r = requests.get(url, timeout=8, verify=False)
        data = r.json()
        return "".join(seg[0] for seg in data[0] if seg[0])
    except Exception:
        return text  # 翻译失败原文返回

# ─── 后台采集线程 ─────────────────────────────────────────────────────
class BriefWorker(QThread):
    finished = Signal(str)
    error    = Signal(str)
    progress = Signal(str)

    def __init__(self, target_date: str):
        super().__init__()
        self.target_date = target_date

    def run(self):
        try:
            # 主搜索
            self.progress.emit("🔍 正在检索西非医疗热点新闻...")
            q = f"West Africa health medical news {self.target_date}"
            resp = requests.get(
                SEARCH_URL, params={"q": q},
                headers=HEADERS, timeout=25, verify=False
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            articles = soup.find_all("article", limit=4)

            # 降级搜索
            if not articles:
                self.progress.emit("⚠️ 主源无结果，切换备用检索...")
                resp2 = requests.get(
                    SEARCH_URL,
                    params={"q": f"Ghana Nigeria healthcare {self.target_date}"},
                    headers=HEADERS, timeout=20, verify=False
                )
                soup = BeautifulSoup(resp2.text, "html.parser")
                articles = soup.find_all("article", limit=4)

            news_block = ""
            for i, art in enumerate(articles, 1):
                self.progress.emit(f"🌐 正在处理第 {i} 条，翻译中...")

                # 标题
                raw_title = ""
                for tag in ("h3", "h2", "a"):
                    el = art.find(tag)
                    if el:
                        raw_title = el.get_text(strip=True)
                        if len(raw_title) > 10:
                            break
                title_cn = translate(raw_title) if raw_title else f"西非医疗动态 #{i}"

                # 摘要
                snippet_raw = ""
                for p in art.find_all("p"):
                    t = p.get_text(strip=True)
                    if len(t) > 30:
                        snippet_raw = t[:150]
                        break
                snippet_cn = translate(snippet_raw) if snippet_raw else "详情请访问原文链接。"

                # 原文链接
                link = SEARCH_URL
                for a in art.find_all("a", href=True):
                    h = a["href"]
                    if h.startswith("http") and "sousuo.zze.cc" not in h:
                        link = h
                        break

                comment = COMMENTS[i % len(COMMENTS)]
                news_block += (
                    f"{i}. {title_cn}\n"
                    f"• 概况：{snippet_cn}\n"
                    f"• HCOWA 简评：{comment}\n"
                    f"• 来源：{link}\n\n"
                )

            if not news_block:
                news_block = "今日暂未检索到相关重大动态，建议稍后重新同步。\n"

            d = datetime.strptime(self.target_date, "%Y-%m-%d")
            is_today = (self.target_date == date.today().strftime("%Y-%m-%d"))
            date_label = d.strftime("%Y年%m月%d日") + ("（今日）" if is_today else "")

            report = (
                "《HCOWA西非健康共同体协会每日健康时事简报》\n"
                f"日期：{date_label} | 坐标：加纳 · 阿克拉 (Accra)\n"
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
                "• 加纳 GSE 市场受国际资本流入驱动，医疗分销板块交投活跃。\n"
                "\n"
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
            self.finished.emit(report)
        except Exception as e:
            self.error.emit(str(e))


# ─── 主窗口 ───────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    QSS = """
    QMainWindow, QWidget#root {
        background: #f0f2f5;
        font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    }
    QLabel { color: #1a1a2e; }

    /* 顶部卡片 */
    QWidget#card {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e6ea;
    }

    /* 文本编辑器 */
    QTextEdit {
        background: #ffffff;
        border: 1.5px solid #dde3ec;
        border-radius: 10px;
        padding: 14px;
        font-size: 13px;
        color: #222;
        line-height: 1.8;
    }

    /* 日期选择 */
    QDateEdit {
        background: #fff;
        border: 1.5px solid #c9d3df;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 13px;
        min-width: 150px;
        min-height: 34px;
        font-family: "Segoe UI", "Microsoft YaHei UI";
    }
    QDateEdit::drop-down { width: 24px; }

    /* 按钮 */
    QPushButton {
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        padding: 10px 20px;
    }
    QPushButton#syncBtn {
        background: #f4f6f8;
        border: 1.5px solid #c9d3df;
        color: #2c3e50;
    }
    QPushButton#syncBtn:hover   { background: #e8f0fe; border-color: #4285f4; }
    QPushButton#syncBtn:disabled { color: #aaa; background: #f0f0f0; }
    QPushButton#copyBtn {
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #1a73e8, stop:1 #0d47a1);
        border: none;
        color: white;
    }
    QPushButton#copyBtn:hover { background: #1557b0; }
    QPushButton#copyBtn:disabled { background: #90b0e0; }

    /* 分割线 */
    QFrame#hr { background: #e2e6ea; max-height: 1px; }

    /* 状态标签 */
    QLabel#status { color: #7f8c8d; font-size: 11px; }
    QLabel#zaki   { color: #bdc3c7; font-size: 11px; font-style: italic; }
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HCOWA 每日热点新闻生成器")
        self.setFixedSize(680, 880)
        self.setStyleSheet(self.QSS)
        self._build()
        self._load_icon()

    def _build(self):
        root = QWidget(); root.setObjectName("root")
        lay  = QVBoxLayout(root)
        lay.setContentsMargins(24, 20, 24, 16)
        lay.setSpacing(14)

        # ── 头部 ──
        hdr = QHBoxLayout(); hdr.setSpacing(14)
        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(72, 72)
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        hdr.addWidget(self.logo_lbl)

        info = QVBoxLayout(); info.setSpacing(3)
        t1 = QLabel("HCOWA 每日热点新闻生成器")
        t1.setStyleSheet("font-size: 21px; font-weight: bold; color: #c0392b;")
        t2 = QLabel("西非健康共同体协会 · 智能简报系统 v2.0")
        t2.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        info.addWidget(t1); info.addWidget(t2)
        hdr.addLayout(info); hdr.addStretch()
        lay.addLayout(hdr)

        # ── 分割线 ──
        hr = QFrame(); hr.setObjectName("hr"); lay.addWidget(hr)

        # ── 日期选择 ──
        drow = QHBoxLayout()
        dl = QLabel("📅  简报日期：")
        dl.setStyleSheet("font-size: 13px; font-weight: bold;")
        drow.addWidget(dl)

        self.dp = QDateEdit()
        # 关键修复：强制英文 locale，彻底解决中文日历乱码
        self.dp.setLocale(QLocale(QLocale.Language.C))
        self.dp.setDisplayFormat("yyyy-MM-dd")
        self.dp.setCalendarPopup(True)
        today = QDate.currentDate()
        self.dp.setDate(today)
        self.dp.setMaximumDate(today)  # 禁止选未来日期

        # 日历弹窗同样强制英文
        cal = self.dp.calendarWidget()
        if cal:
            cal.setLocale(QLocale(QLocale.Language.C))
        self.dp.dateChanged.connect(self._date_hint)
        drow.addWidget(self.dp)

        self.hint = QLabel("（今日）")
        self.hint.setStyleSheet("color: #27ae60; font-size: 12px;")
        drow.addWidget(self.hint)
        drow.addStretch()
        lay.addLayout(drow)

        # ── 编辑区 ──
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "请选择日期后，点击「同步今日热点新闻」开始生成简报..."
        )
        lay.addWidget(self.editor)

        # ── 底部：状态 + 按钮 + Zaki ──
        self.status = QLabel("就绪")
        self.status.setObjectName("status")
        lay.addWidget(self.status)

        foot = QHBoxLayout(); foot.setSpacing(12)
        self.sync_btn = QPushButton("🔄  同步今日热点新闻")
        self.sync_btn.setObjectName("syncBtn")
        self.sync_btn.setMinimumHeight(52)
        self.sync_btn.clicked.connect(self._sync)

        self.copy_btn = QPushButton("📋  复制简报全文")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setMinimumHeight(52)
        self.copy_btn.clicked.connect(self._copy)

        zaki = QLabel("Zaki")
        zaki.setObjectName("zaki")
        zaki.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        foot.addWidget(self.sync_btn)
        foot.addWidget(self.copy_btn)
        foot.addWidget(zaki)
        lay.addLayout(foot)

        self.setCentralWidget(root)

    # ── 图标加载 ──────────────────────────────────────────────────────
    def _load_icon(self):
        for p in (res("assets/logo.png"), res("assets/logo.jpg")):
            if os.path.exists(p):
                pix = QPixmap(p).scaled(
                    72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.logo_lbl.setPixmap(pix)
                self.setWindowIcon(QIcon(res("assets/icon.ico") if
                                         os.path.exists(res("assets/icon.ico")) else p))
                break

    # ── 日期提示 ──────────────────────────────────────────────────────
    def _date_hint(self, qd):
        if qd == QDate.currentDate():
            self.hint.setText("（今日）")
            self.hint.setStyleSheet("color: #27ae60; font-size: 12px;")
        else:
            self.hint.setText("（往期回顾）")
            self.hint.setStyleSheet("color: #e67e22; font-size: 12px;")

    # ── 同步 ──────────────────────────────────────────────────────────
    def _sync(self):
        target = self.dp.date().toString("yyyy-MM-dd")
        self.sync_btn.setEnabled(False)
        self.sync_btn.setText("⟳  正在同步...")
        self.editor.clear()
        self.status.setText("▶ 启动中...")

        self.worker = BriefWorker(target)
        self.worker.progress.connect(lambda m: self.status.setText(m))
        self.worker.finished.connect(self._on_ok)
        self.worker.error.connect(self._on_err)
        self.worker.start()

    def _on_ok(self, text):
        self.editor.setPlainText(text)
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄  重新同步")
        self.status.setText("✅ 简报已就绪，可复制发布。")

    def _on_err(self, msg):
        QMessageBox.warning(self, "同步失败", f"网络异常：\n{msg}\n\n请检查网络后重试。")
        self.sync_btn.setEnabled(True)
        self.sync_btn.setText("🔄  同步今日热点新闻")
        self.status.setText("❌ 同步失败。")

    # ── 复制 ──────────────────────────────────────────────────────────
    def _copy(self):
        txt = self.editor.toPlainText()
        if not txt:
            QMessageBox.information(self, "提示", "请先点击「同步」生成简报内容。")
            return
        self.editor.selectAll()
        self.editor.copy()
        self.editor.moveCursor(QTextCursor.MoveOperation.Start)
        QMessageBox.information(self, "完成", "✅ 简报全文已复制到剪贴板，可直接粘贴发布！")


# ─── 入口 ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ico = res("assets/icon.ico")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
