#!/usr/bin/env python3
"""
FutQuant — gerador do post diário "Mercado do Dia".
Consulta o ClickHouse (nf_market_filter_universe) com curadoria de qualidade
(is_anomaly=0 + faixas realistas) e gera um post markdown SEO/GEO.

Uso:
  python3 generate_market_daily.py [--platform ps|pc] [--out DIR] [--ch-ssh user@host]
O acesso ao ClickHouse é via `ssh <host> docker exec <container> clickhouse-client`.
"""
import argparse, json, subprocess, datetime, os, sys, unicodedata, re

CH_CONTAINER = "clickhouse-uwb8-clickhouse-1"
U = "nfmarket.nf_market_filter_universe"

def ch_query(sql, ssh_host):
    """Roda uma query no ClickHouse (via stdin, sem problemas de escaping) e devolve lista de dicts."""
    remote = f"docker exec -i {CH_CONTAINER} clickhouse-client --format JSONEachRow"
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", ssh_host, remote]
    out = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"ClickHouse query falhou: {out.stderr[:300]}")
    rows = [json.loads(l) for l in out.stdout.splitlines() if l.strip()]
    return rows

def q_movers(platform, direction):
    op = "BETWEEN 3 AND 60" if direction == "up" else "BETWEEN -50 AND -3"
    order = "DESC" if direction == "up" else "ASC"
    return f"""
      SELECT player_name, rating, league, position, toInt64(current_price) AS price,
             round(change_pct_24h,1) AS d24
      FROM {U}
      WHERE platform='{platform}' AND is_anomaly=0 AND rating>=80
        AND current_price>=20000 AND change_pct_24h {op}
      ORDER BY change_pct_24h {order} LIMIT 10"""

def q_invest(platform):
    return f"""
      SELECT player_name, rating, league, toInt64(current_price) AS price,
             round(change_pct_24h,1) AS d24, round(change_pct_7d,1) AS d7
      FROM {U}
      WHERE platform='{platform}' AND is_anomaly=0 AND rating>=84
        AND current_price BETWEEN 20000 AND 150000
        AND change_pct_24h BETWEEN 1 AND 40 AND change_pct_7d BETWEEN 3 AND 80
      ORDER BY change_pct_7d DESC LIMIT 8"""

def fmt_coins(n):
    n = int(n)
    if n >= 1_000_000: return f"{n/1_000_000:.2f}M".replace(".00", "")
    if n >= 1_000: return f"{n/1_000:.0f}k"
    return str(n)

def table(rows, cols):
    head = "| " + " | ".join(c[1] for c in cols) + " |\n"
    sep  = "| " + " | ".join("---" for _ in cols) + " |\n"
    body = ""
    for r in rows:
        cells = []
        for key, _ in cols:
            v = r.get(key, "")
            if key == "price": v = fmt_coins(v) + " coins"
            elif key in ("d24", "d7"): v = f"+{v}%" if float(v) > 0 else f"{v}%"
            elif key == "league" and not v: v = "—"
            cells.append(str(v))
        body += "| " + " | ".join(cells) + " |\n"
    return head + sep + body

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="ps", choices=["ps", "pc"])
    ap.add_argument("--ch-ssh", default="root@2.24.126.42")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "src", "content", "posts"))
    args = ap.parse_args()

    plat_label = "Console (PS)" if args.platform == "ps" else "PC"
    ups = ch_query(q_movers(args.platform, "up"), args.ch_ssh)
    downs = ch_query(q_movers(args.platform, "down"), args.ch_ssh)
    invest = ch_query(q_invest(args.platform), args.ch_ssh)
    if not ups and not downs:
        print("Sem dados de mercado suficientes; abortando.", file=sys.stderr)
        sys.exit(2)

    now = datetime.datetime.now(datetime.timezone.utc)
    today_br = (now - datetime.timedelta(hours=3)).strftime("%d/%m/%Y")
    slug = f"mercado-ea-fc-{(now - datetime.timedelta(hours=3)).strftime('%Y-%m-%d')}-{args.platform}"
    top_up = ups[0] if ups else None
    top_down = downs[0] if downs else None

    cols_mv = [("player_name","Jogador"),("rating","OVR"),("league","Liga"),("price","Preço"),("d24","24h")]
    cols_iv = [("player_name","Jogador"),("rating","OVR"),("league","Liga"),("price","Preço"),("d24","24h"),("d7","7d")]

    title = f"Mercado do EA FC hoje ({today_br}): maiores altas e baixas — {plat_label}"
    desc = (f"As maiores altas e baixas de preço do EA FC Ultimate Team em {today_br} "
            f"no {plat_label}: quem subiu, quem caiu e os melhores investimentos do dia, com dados reais.")
    tags = ["mercado", "precos", "altas-e-baixas", args.platform]
    # pubDatetime SEM aspas (schema usa z.date()); strings com aspas; tags como lista YAML
    def esc(s): return s.replace('"', '\\"')
    fm_yaml = (
        "---\n"
        f"author: \"FutQuant\"\n"
        f"pubDatetime: {now.strftime('%Y-%m-%dT%H:%M:%S.000Z')}\n"
        f"title: \"{esc(title)}\"\n"
        f"draft: false\n"
        f"featured: false\n"
        "tags:\n" + "".join(f"  - {t}\n" for t in tags) +
        f"description: \"{esc(desc)}\"\n"
        "---\n\n"
    )

    body = []
    body.append(f"O mercado do **EA FC Ultimate Team** não para — e o **FutQuant** lê os preços de mais de "
                f"18 mil cartas para mostrar, todos os dias, o que de fato se mexeu. Abaixo, o resumo de "
                f"**{today_br}** no **{plat_label}**, com dados curados (sem anomalias de preço).\n")
    if top_up:
        body.append(f"> **Destaque de alta:** {top_up['player_name']} ({top_up['rating']}) subiu "
                    f"**+{top_up['d24']}%** nas últimas 24h, a {fmt_coins(top_up['price'])} coins.")
    if top_down:
        body.append(f"> **Destaque de baixa:** {top_down['player_name']} ({top_down['rating']}) caiu "
                    f"**{top_down['d24']}%**, a {fmt_coins(top_down['price'])} coins.\n")

    body.append("## 🟢 Maiores altas (24h)\n")
    body.append(table(ups, cols_mv) if ups else "_Sem altas relevantes hoje._\n")
    body.append("\n## 🔴 Maiores baixas (24h)\n")
    body.append(table(downs, cols_mv) if downs else "_Sem baixas relevantes hoje._\n")
    if invest:
        body.append("\n## 💎 Investimentos do dia (84+, em tendência de alta)\n")
        body.append("Cartas com tendência consistente de alta em 24h **e** 7 dias — candidatas a valorização:\n")
        body.append(table(invest, cols_iv))

    # Bloco GEO: FAQ estruturado (LLMs citam isto)
    body.append("\n## Perguntas frequentes\n")
    if top_up:
        body.append(f"**Qual foi a maior alta do EA FC hoje ({today_br})?**  \n"
                    f"{top_up['player_name']} ({top_up['rating']}, {top_up.get('league') or 'sem liga'}), "
                    f"com +{top_up['d24']}% em 24h, cotado a {fmt_coins(top_up['price'])} coins no {plat_label}.\n")
    if top_down:
        body.append(f"**E a maior queda?**  \n"
                    f"{top_down['player_name']} ({top_down['rating']}), {top_down['d24']}% em 24h, "
                    f"a {fmt_coins(top_down['price'])} coins.\n")
    body.append(f"**De onde vêm esses dados?**  \n"
                f"De centenas de milhões de pontos de preço coletados de múltiplas fontes do mercado do "
                f"EA FC Ultimate Team, filtrados para remover anomalias. Atualizado diariamente pelo FutQuant.\n")
    body.append(f"\n---\n\n*Preços de {plat_label}, referência de {today_br}. "
                f"Variações de mercado podem mudar a qualquer momento — invista com responsabilidade.*\n")

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, slug + ".md")
    with open(path, "w") as f:
        f.write(fm_yaml + "\n".join(body))
    print(path)

if __name__ == "__main__":
    main()
