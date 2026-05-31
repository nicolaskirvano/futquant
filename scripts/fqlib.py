"""FutQuant — helpers compartilhados entre os geradores de conteúdo."""
import json, subprocess, datetime, os

CH_CONTAINER = "clickhouse-uwb8-clickhouse-1"
U = "nfmarket.nf_market_filter_universe"
PLAT_LABEL = {"ps": "Console (PS)", "pc": "PC"}

def ch_query(sql, ssh_host="local"):
    """Query no ClickHouse via stdin (sem escaping). ssh_host='local' => docker exec direto."""
    if ssh_host == "local":
        cmd = ["docker", "exec", "-i", CH_CONTAINER, "clickhouse-client", "--format", "JSONEachRow"]
    else:
        remote = f"docker exec -i {CH_CONTAINER} clickhouse-client --format JSONEachRow"
        cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", ssh_host, remote]
    out = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"ClickHouse falhou: {out.stderr[:300]}")
    return [json.loads(l) for l in out.stdout.splitlines() if l.strip()]

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)

def br(dt=None):
    return (dt or now_utc()) - datetime.timedelta(hours=3)

def today_br_str():
    return br().strftime("%d/%m/%Y")

def date_slug():
    return br().strftime("%Y-%m-%d")

def fmt_coins(n):
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M".replace(".00M", "M")
    if n >= 1_000: return f"{n/1_000:.0f}k"
    return str(n)

def _cell(r, key):
    v = r.get(key, "")
    if key in ("price", "preco"): return fmt_coins(v) + " coins"
    if key in ("d24", "d7", "pct", "pct7d", "pct24h"):
        return f"+{v}%" if float(v) > 0 else f"{v}%"
    if key == "league" and not v: return "—"
    return str(v)

def md_table(rows, cols):
    """cols = [(key, header), ...]"""
    head = "| " + " | ".join(h for _, h in cols) + " |\n"
    sep = "| " + " | ".join("---" for _ in cols) + " |\n"
    body = "".join("| " + " | ".join(_cell(r, k) for k, _ in cols) + " |\n" for r in rows)
    return head + sep + body

def _esc(s):
    return str(s).replace('"', '\\"')

def write_post(out_dir, slug, title, description, tags, body, featured=False):
    """Escreve o .md com frontmatter compatível com o schema AstroPaper (pubDatetime sem aspas)."""
    fm = (
        "---\n"
        'author: "FutQuant"\n'
        f"pubDatetime: {now_utc().strftime('%Y-%m-%dT%H:%M:%S.000Z')}\n"
        f'title: "{_esc(title)}"\n'
        "draft: false\n"
        f"featured: {'true' if featured else 'false'}\n"
        "tags:\n" + "".join(f"  - {t}\n" for t in tags) +
        f'description: "{_esc(description)}"\n'
        "---\n\n"
    )
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, slug + ".md")
    with open(path, "w") as f:
        f.write(fm + body)
    return path

def disclaimer(plat_label):
    return (f"\n---\n\n*Preços de {plat_label}, referência de {today_br_str()}. "
            f"Variações de mercado mudam a qualquer momento — invista com responsabilidade.*\n")

# filtros de qualidade reutilizáveis (sem anomalias)
QUALITY = "is_anomaly=0"
