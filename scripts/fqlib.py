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
    if key in ("price", "preco", "preco_prev"): return fmt_coins(v) + " coins"
    if key in ("d24", "d7", "pct", "pct7d", "pct24h", "prev24"):
        return f"+{v}%" if float(v) > 0 else f"{v}%"
    if key == "prob_alta": return f"{int(float(v))}%"
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

def faq_block(pairs):
    """Markdown do bloco de FAQ visível (mesma fonte do FAQPage schema)."""
    out = ["\n## ❓ Perguntas frequentes\n"]
    for q, a in pairs:
        out.append(f"**{q}**  \n{a}\n")
    return "\n".join(out)

def write_post(out_dir, slug, title, description, tags, body, featured=False, faq=None):
    """Escreve o .md com frontmatter compatível com o schema AstroPaper (pubDatetime sem aspas).
    faq = lista de (pergunta, resposta) -> emitida no frontmatter p/ gerar FAQPage JSON-LD."""
    faq_yaml = ""
    if faq:
        faq_yaml = "faq:\n" + "".join(
            f'  - q: "{_esc(q)}"\n    a: "{_esc(a)}"\n' for q, a in faq
        )
    fm = (
        "---\n"
        'author: "FutQuant"\n'
        f"pubDatetime: {now_utc().strftime('%Y-%m-%dT%H:%M:%S.000Z')}\n"
        f'title: "{_esc(title)}"\n'
        "draft: false\n"
        f"featured: {'true' if featured else 'false'}\n"
        "tags:\n" + "".join(f"  - {t}\n" for t in tags) +
        f'description: "{_esc(description)}"\n'
        + faq_yaml +
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

# --- Segmento do blog (torna cada blog distinto sem duplicar geradores) ---
# FQ_SEG: condição SQL simples sobre o universe, ex: "league='Premier League'", "position='GK'",
#         "current_price<=25000", "nation='Brazil'". FQ_SEG_LABEL: rótulo p/ títulos.
_SEG = os.environ.get("FQ_SEG", "").strip()
SEG_LABEL = os.environ.get("FQ_SEG_LABEL", "").strip()

def seg(alias=""):
    """Cláusula AND do segmento, com alias opcional da tabela (ex: 'u')."""
    if not _SEG:
        return ""
    prefix = (alias + ".") if alias else ""
    return f" AND {prefix}{_SEG}"

def seg_label():
    return SEG_LABEL

def has_seg():
    return bool(_SEG)

def signal_label(signal, prob_alta):
    """Rótulo legível da previsão do modelo."""
    try:
        prob = int(float(prob_alta))
    except (TypeError, ValueError):
        prob = None
    if signal == "rise":
        return f"📈 Alta provável" + (f" ({prob}%)" if prob is not None else "")
    if signal == "fall":
        return f"📉 Queda provável" + (f" ({100-prob}%)" if prob is not None else "")
    return "➡️ Estável"

def trend_vs_sma(price, sma7):
    """Posição do preço atual frente à média de 7 dias (sinal de tendência)."""
    try:
        price, sma7 = float(price), float(sma7)
        if sma7 <= 0: return None
        diff = (price - sma7) / sma7 * 100
        if diff >= 8: return f"{diff:+.0f}% acima da média de 7 dias (aquecida)"
        if diff <= -8: return f"{diff:+.0f}% abaixo da média de 7 dias (descontada)"
        return f"em linha com a média de 7 dias ({diff:+.0f}%)"
    except (TypeError, ValueError, ZeroDivisionError):
        return None

def methodology():
    """Bloco de metodologia (E-E-A-T) reutilizável entre os posts."""
    return ("\n## 📐 Como o FutQuant gera estes dados\n"
            "Trabalhamos com **centenas de milhões de pontos de preço** do mercado do EA FC Ultimate Team, "
            "coletados de múltiplas fontes e atualizados várias vezes ao dia. Antes de publicar, removemos "
            "**anomalias** (cotações irreais de cartas extintas ou erros de coleta) e cruzamos preço atual, "
            "**médias móveis (24h e 7 dias)**, faixa do dia e tendência. É por isso que aqui você vê dado "
            "tratado — não número solto.\n")

def market_sentiment(up, down, avg):
    """Frase de sentimento macro do mercado."""
    total = up + down
    if total == 0: return "mercado parado"
    pct_up = up / total * 100
    if avg >= 1.5 or pct_up >= 60: return "mercado **em alta** — predominam as valorizações"
    if avg <= -1.5 or pct_up <= 40: return "mercado **em baixa** — predominam as quedas"
    return "mercado **lateral** — sem direção clara"
