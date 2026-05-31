#!/usr/bin/env python3
"""FutQuant — post 'Melhores investimentos' com análise: cartas 84+ em tendência de alta
consistente (24h+7d) cruzadas com a previsão do modelo e níveis técnicos."""
import argparse, os, sys
import fqlib as fq

P = "nfmarket.price_predictions"

def query(platform):
    return f"""
      SELECT u.player_name AS player_name, u.rating AS rating, u.league AS league, u.position AS position,
             toInt64(u.current_price) AS price, round(u.change_pct_24h,1) AS d24, round(u.change_pct_7d,1) AS d7,
             toInt64(u.sma_7d) AS sma7, toInt64(u.min_24h) AS min24, toInt64(u.max_24h) AS max24,
             round(p.prob_rise_5pct*100,0) AS prob_alta, p.signal AS signal,
             round(p.predicted_change_pct_24h,1) AS prev24
      FROM {fq.U} u LEFT JOIN {P} p ON u.resource_id=p.resource_id AND u.platform=p.platform
      WHERE u.platform='{platform}' AND u.{fq.QUALITY} AND u.rating>=84
        AND u.current_price BETWEEN 15000 AND 250000
        AND u.change_pct_24h BETWEEN 1 AND 40 AND u.change_pct_7d BETWEEN 5 AND 90{fq.seg('u')}
      ORDER BY u.change_pct_7d DESC LIMIT 15"""

def analyse(c):
    name, r = c["player_name"], c["rating"]
    line = (f"**{name} ({r})** — {fq.fmt_coins(c['price'])} coins, **+{c['d7']}% em 7 dias** "
            f"(+{c['d24']}% em 24h).")
    sma = fq.trend_vs_sma(c["price"], c["sma7"])
    if sma: line += f" Preço {sma}."
    sig, prob = c.get("signal"), c.get("prob_alta")
    try: prob = int(float(prob))
    except (TypeError, ValueError): prob = None
    pv = None
    try: pv = abs(float(c.get("prev24")))
    except (TypeError, ValueError): pass
    if sig == "rise" and prob and pv and pv <= 35:
        line += f" 🔮 O modelo reforça a tese: **{prob}% de chance de seguir subindo**."
    elif sig == "fall":
        line += " ⚠️ Porém o modelo já vê risco de correção no curtíssimo prazo — entre com cautela."
    else:
        line += " Momentum positivo; acompanhe para escolher o ponto de entrada."
    return line

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="ps", choices=["ps", "pc"])
    ap.add_argument("--ch-ssh", default="local")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "src", "content", "posts"))
    a = ap.parse_args()
    rows = fq.ch_query(query(a.platform), a.ch_ssh)
    if len(rows) < 4:
        print("poucos investimentos hoje; pulando", file=sys.stderr); sys.exit(0)
    plat = fq.PLAT_LABEL[a.platform]; today = fq.today_br_str(); top = rows[0]
    slug = f"melhores-investimentos-ea-fc-{fq.date_slug()}-{a.platform}"
    seg = fq.seg_label()
    title = (f"Melhores investimentos em {seg} no EA FC ({today}): análise e previsões — {plat}" if seg
             else f"Melhores investimentos no EA FC hoje ({today}): análise e previsões — {plat}")
    desc = (f"As cartas 84+ do EA FC Ultimate Team com tendência de alta mais consistente em {today} ({plat}), "
            f"cruzadas com a previsão do modelo FutQuant e níveis técnicos. Onde investir com dado, não palpite.")
    cols = [("player_name","Jogador"),("rating","OVR"),("league","Liga"),("price","Preço"),
            ("d24","24h"),("d7","7d"),("prob_alta","Prob. alta")]
    b = []
    b.append("## Por que estas cartas\n")
    b.append(f"Investir bem no **EA FC Ultimate Team** é seguir tendência sustentada, não pico isolado. O **FutQuant** "
             f"cruza a variação de **24h e 7 dias** de mais de 18 mil cartas e filtra as **84+ que sobem de forma "
             f"consistente** — depois confronta cada uma com a **previsão do nosso modelo**. Resultado de **{today}** "
             f"no **{plat}**:\n")
    b.append(f"> 🔝 **Destaque:** {top['player_name']} ({top['rating']}) acumula **+{top['d7']}% em 7 dias** "
             f"a {fq.fmt_coins(top['price'])} coins.\n")
    b.append("## 💎 Cartas em tendência de alta (84+)\n")
    b.append("Ordenadas pela valorização de 7 dias; *Prob. alta* é a chance estimada de seguir subindo:\n")
    b.append(fq.md_table(rows, cols))
    b.append("\n## 📈 Análise dos destaques\n")
    for c in rows[:5]:
        b.append("- " + analyse(c) + "\n")
    b.append("\n## Como usar esta lista\n")
    b.append("- **24h e 7d positivos juntos** = tendência sustentada, o sinal mais confiável.\n"
             "- Prefira entrar em **correções** (quedas curtas dentro da alta) para reduzir risco.\n"
             "- **Liquidez importa**: cartas de ligas e ratings populares vendem mais rápido.\n"
             "- Use a coluna *Prob. alta* para priorizar: quanto maior, mais o modelo concorda com a tendência.\n")
    b.append(fq.methodology())
    faqs = []
    faqs.append((f"Qual a melhor carta para investir hoje ({today}) no EA FC?",
                 f"{top['player_name']} ({top['rating']}, {top.get('league') or 'sem liga'}) lidera, com +{top['d7']}% "
                 f"em 7 dias a {fq.fmt_coins(top['price'])} coins no {plat}"
                 + (f", e o modelo dá {int(float(top['prob_alta']))}% de chance de seguir subindo." if top.get('prob_alta') else ".")))
    faqs.append(("Investir em FUT dá lucro garantido?",
                 "Não. São probabilidades baseadas em dados históricos; o mercado pode mudar com promoções e "
                 "lançamentos. Use como apoio à decisão, não como garantia."))
    faqs.append(("Com que frequência a lista de investimentos atualiza?",
                 "Várias vezes ao dia, junto com os preços do mercado do EA FC."))
    b.append(fq.faq_block(faqs))
    b.append(fq.disclaimer(plat))
    print(fq.write_post(a.out, slug, title, desc, ["investimentos","trading","previsoes",a.platform],
                        "\n".join(b), featured=True, faq=faqs))

if __name__ == "__main__":
    main()
