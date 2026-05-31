#!/usr/bin/env python3
"""FutQuant — post 'Destaque da Liga' (rotativo por dia: panorama de preços de uma liga)."""
import argparse, os, sys, datetime, unicodedata, re
import fqlib as fq

# Nomes EXATOS das ligas no ClickHouse. Rotaciona por dia do ano -> cobertura ampla ao longo do tempo.
LEAGUES = [
    "Premier League", "LALIGA EA SPORTS", "Serie A TIM", "Bundesliga", "Ligue 1 McDonald's",
    "Eredivisie", "Liga Portugal", "Trendyol Süper Lig", "ROSHN Saudi League", "MLS",
]

def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")

def q_top(platform, league, order, where_extra=""):
    return f"""
      SELECT player_name, rating, position, toInt64(current_price) AS price,
             round(change_pct_24h,1) AS d24, round(change_pct_7d,1) AS d7
      FROM {fq.U}
      WHERE platform='{platform}' AND {fq.QUALITY} AND league='{league}'
        AND current_price>=2000 {where_extra}
      ORDER BY {order} LIMIT 10"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="ps", choices=["ps", "pc"])
    ap.add_argument("--ch-ssh", default="local")
    ap.add_argument("--league", default=None, help="força uma liga (senão rotaciona por dia)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "src", "content", "posts"))
    a = ap.parse_args()
    doy = fq.br().timetuple().tm_yday
    league = a.league or LEAGUES[doy % len(LEAGUES)]
    plat = fq.PLAT_LABEL[a.platform]; today = fq.today_br_str()

    valuable = fq.ch_query(q_top(a.platform, league, "current_price DESC"), a.ch_ssh)
    risers = fq.ch_query(q_top(a.platform, league, "change_pct_7d DESC", "AND change_pct_7d BETWEEN 3 AND 90 AND rating>=78"), a.ch_ssh)
    if len(valuable) < 4:
        print(f"poucos dados p/ {league}; pulando", file=sys.stderr); sys.exit(0)

    slug = f"mercado-{slugify(league)}-ea-fc-{fq.date_slug()}-{a.platform}"
    title = f"Mercado da {league} no EA FC ({today}): cartas mais valiosas e em alta — {plat}"
    desc = (f"Panorama de preços da {league} no EA FC Ultimate Team em {today} ({plat}): "
            f"os jogadores mais caros e os que mais valorizam na liga, com dados reais.")
    cols_v = [("player_name","Jogador"),("rating","OVR"),("position","Pos"),("price","Preço"),("d24","24h")]
    cols_r = [("player_name","Jogador"),("rating","OVR"),("position","Pos"),("price","Preço"),("d7","7d")]
    top = valuable[0]
    body = []
    body.append(f"A **{league}** é uma das ligas mais usadas no **EA FC Ultimate Team** — e seus preços se mexem todo dia. "
                f"O **FutQuant** acompanha cada carta da liga e traz abaixo o panorama de **{today}** no **{plat}**.\n")
    body.append(f"> 👑 **Carta mais valiosa da {league}:** {top['player_name']} ({top['rating']}), "
                f"a {fq.fmt_coins(top['price'])} coins.\n")
    body.append(f"## 👑 Mais valiosos da {league}\n")
    body.append(fq.md_table(valuable, cols_v))
    if len(risers) >= 3:
        body.append(f"\n## 📈 Em alta na {league} (7 dias)\n")
        body.append(f"Cartas da liga que mais valorizaram na última semana:\n")
        body.append(fq.md_table(risers, cols_r))
    if len(risers) >= 2:
        body.append(f"\n## 📈 Análise da {league}\n")
        body.append(f"A carta mais valiosa da liga é **{top['player_name']} ({top['rating']})**, a "
                    f"{fq.fmt_coins(top['price'])} coins. ")
        r0 = risers[0]
        body.append(f"No movimento da semana, **{r0['player_name']} ({r0['rating']})** lidera as altas "
                    f"(+{r0['d7']}% em 7 dias), sinal de procura crescente por cartas da {league}. "
                    f"Quem busca custo-benefício na liga deve observar as cartas que ainda não dispararam.\n")
    body.append(fq.methodology())
    faqs = []
    faqs.append((f"Qual o jogador mais caro da {league} no EA FC hoje?",
                 f"{top['player_name']} ({top['rating']}), a {fq.fmt_coins(top['price'])} coins no {plat} em {today}."))
    if len(risers) >= 1:
        r = risers[0]
        faqs.append((f"Quem mais valorizou na {league} esta semana no EA FC?",
                     f"{r['player_name']} ({r['rating']}), +{r['d7']}% em 7 dias, a {fq.fmt_coins(r['price'])} coins."))
    faqs.append((f"Onde ver os preços das cartas da {league} no EA FC Ultimate Team?",
                 f"O FutQuant acompanha os preços de todas as cartas da {league}, atualizados todos os dias, "
                 f"com as mais valiosas e as que mais valorizam."))
    body.append(fq.faq_block(faqs))
    body.append(fq.disclaimer(plat))
    tags = ["liga", slugify(league), "mercado", a.platform]
    print(fq.write_post(a.out, slug, title, desc, tags, "\n".join(body), faq=faqs))

if __name__ == "__main__":
    main()
