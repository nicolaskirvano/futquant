#!/usr/bin/env python3
"""FutQuant — post 'Mercado do Dia' em formato de ANÁLISE PROFUNDA:
sentimento macro + altas/baixas + previsões do modelo + níveis técnicos + metodologia + FAQ.
Dados: ClickHouse nf_market_filter_universe (preço/técnico) + price_predictions (previsão).
"""
import argparse, os, sys
import fqlib as fq

P = "nfmarket.price_predictions"

def q_movers(platform, direction):
    cond = "BETWEEN 3 AND 60" if direction == "up" else "BETWEEN -50 AND -3"
    order = "DESC" if direction == "up" else "ASC"
    return f"""
      SELECT u.player_name AS player_name, u.rating AS rating, u.league AS league, u.position AS position,
             toInt64(u.current_price) AS price, round(u.change_pct_24h,1) AS d24, round(u.change_pct_7d,1) AS d7,
             toInt64(u.min_24h) AS min24, toInt64(u.max_24h) AS max24,
             u.support_level AS sup, u.resistance_level AS res, toInt64(u.sma_7d) AS sma7,
             round(p.predicted_change_pct_24h,1) AS prev24, round(p.prob_rise_5pct*100,0) AS prob_alta,
             p.signal AS signal
      FROM {fq.U} u LEFT JOIN {P} p ON u.resource_id=p.resource_id AND u.platform=p.platform
      WHERE u.platform='{platform}' AND u.{fq.QUALITY} AND u.rating>=80
        AND u.current_price>=20000 AND u.change_pct_24h {cond}{fq.seg('u')}
      ORDER BY u.change_pct_24h {order} LIMIT 10"""

def q_forecast(platform, sig):
    order = "p.prob_rise_5pct DESC" if sig == "rise" else "p.prob_rise_5pct ASC"
    return f"""
      SELECT u.player_name AS player_name, u.rating AS rating, u.league AS league,
             toInt64(u.current_price) AS price, round(p.predicted_change_pct_24h,1) AS prev24,
             toInt64(u.current_price * (1 + p.predicted_change_pct_24h/100)) AS preco_prev,
             round(p.prob_rise_5pct*100,0) AS prob_alta, p.signal AS signal
      FROM {fq.U} u INNER JOIN {P} p ON u.resource_id=p.resource_id AND u.platform=p.platform
      WHERE u.platform='{platform}' AND u.{fq.QUALITY} AND u.rating>=83
        AND u.current_price BETWEEN 15000 AND 400000 AND p.signal='{sig}' AND p.confidence>=0.8
        AND abs(p.predicted_change_pct_24h) BETWEEN 2 AND 35{fq.seg('u')}
      ORDER BY {order} LIMIT 8"""

def q_sentiment(platform):
    return f"""
      SELECT countIf(change_pct_24h>0) AS up, countIf(change_pct_24h<0) AS down,
             countIf(change_pct_24h=0) AS flat, round(avg(change_pct_24h),2) AS avg
      FROM {fq.U} WHERE platform='{platform}' AND {fq.QUALITY} AND rating>=80 AND current_price>=5000{fq.seg()}"""

def analyse(card, kind):
    """Mini-análise textual de uma carta (com níveis técnicos + previsão)."""
    name, r = card["player_name"], card["rating"]
    price = fq.fmt_coins(card["price"])
    rng = f"{fq.fmt_coins(card['min24'])}–{fq.fmt_coins(card['max24'])}"
    verb = "subiu" if kind == "up" else "caiu"
    pct = card["d24"]
    line = (f"**{name} ({r})** {verb} **{'+' if float(pct)>0 else ''}{pct}%** em 24h, a **{price} coins** "
            f"(faixa do dia: {rng}).")
    sma = fq.trend_vs_sma(card["price"], card["sma7"])
    if sma: line += f" Está {sma}."
    sig = card.get("signal")
    try:
        prob = int(float(card.get("prob_alta")))
    except (TypeError, ValueError):
        prob = None
    if sig == "rise":
        if kind == "up":
            line += f" 🔮 O modelo projeta **continuidade da alta**" + (f" ({prob}% de chance de subir mais)." if prob else ".")
        else:
            line += f" 🔮 O modelo projeta **recuperação** (reversão para alta)" + (f", com {prob}% de probabilidade." if prob else ".")
    elif sig == "fall":
        if kind == "up":
            line += " ⚠️ Mas o modelo projeta **reversão para queda** nas próximas 24h — pode ser topo."
        else:
            line += " ⚠️ O modelo projeta **continuidade da queda** — ainda não encontrou fundo."
    else:
        line += " O modelo vê **estabilização** no curto prazo."
    return line

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="ps", choices=["ps", "pc"])
    ap.add_argument("--ch-ssh", default="local")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "src", "content", "posts"))
    a = ap.parse_args()
    plat = fq.PLAT_LABEL[a.platform]; today = fq.today_br_str()

    ups = fq.ch_query(q_movers(a.platform, "up"), a.ch_ssh)
    downs = fq.ch_query(q_movers(a.platform, "down"), a.ch_ssh)
    rises = fq.ch_query(q_forecast(a.platform, "rise"), a.ch_ssh)
    falls = fq.ch_query(q_forecast(a.platform, "fall"), a.ch_ssh)
    sent = (fq.ch_query(q_sentiment(a.platform), a.ch_ssh) or [{}])[0]
    if not ups and not downs:
        print("sem dados de mercado; abortando", file=sys.stderr); sys.exit(0)

    up_n, down_n, avg = int(sent.get("up",0)), int(sent.get("down",0)), float(sent.get("avg",0))
    sentiment = fq.market_sentiment(up_n, down_n, avg)
    slug = f"mercado-ea-fc-{fq.date_slug()}-{a.platform}"
    seg = fq.seg_label()
    title = (f"{seg} no EA FC hoje ({today}): mercado, altas, baixas e previsões — {plat}" if seg
             else f"Mercado do EA FC hoje ({today}): análise de altas, baixas e previsões — {plat}")
    desc = (f"Análise completa do mercado do EA FC Ultimate Team em {today} ({plat}): sentimento do dia, "
            f"maiores altas e baixas, previsões do modelo FutQuant e níveis técnicos. Dados reais e curados.")
    top_up = ups[0] if ups else None
    top_down = downs[0] if downs else None

    mv_cols = [("player_name","Jogador"),("rating","OVR"),("league","Liga"),("price","Preço"),
               ("d24","24h"),("d7","7d")]
    fc_cols = [("player_name","Jogador"),("rating","OVR"),("price","Preço atual"),
               ("preco_prev","Preço previsto 24h"),("prob_alta","Prob. alta")]

    b = []
    # Resumo macro
    b.append("## 📊 Resumo do mercado hoje\n")
    b.append(f"Em **{today}**, o mercado do **EA FC Ultimate Team** no **{plat}** está em {sentiment}: "
             f"das cartas relevantes (80+ acima de 5k coins), **{up_n} subiram** e **{down_n} caíram**, "
             f"com variação média de **{avg}%** nas últimas 24 horas. "
             f"{'Bom momento para vender quem valorizou e ficar de olho em correções para comprar.' if avg<0 else 'Mercado comprador — cuidado para não pagar topo em cartas já esticadas.'}\n")
    if top_up and top_down:
        b.append(f"> 🟢 **Maior alta:** {top_up['player_name']} ({top_up['rating']}) **+{top_up['d24']}%** · "
                 f"🔴 **Maior baixa:** {top_down['player_name']} ({top_down['rating']}) **{top_down['d24']}%**\n")

    # Altas
    b.append("## 🟢 Maiores altas (24h)\n")
    b.append(fq.md_table(ups, mv_cols) if ups else "_Sem altas relevantes hoje._\n")
    if ups:
        b.append("\n### Análise das altas\n")
        for c in ups[:3]:
            b.append("- " + analyse(c, "up") + "\n")

    # Baixas
    b.append("\n## 🔴 Maiores baixas (24h)\n")
    b.append(fq.md_table(downs, mv_cols) if downs else "_Sem baixas relevantes hoje._\n")
    if downs:
        b.append("\n### Análise das baixas\n")
        for c in downs[:3]:
            b.append("- " + analyse(c, "down") + "\n")

    # Previsões do modelo
    if rises:
        b.append("\n## 🔮 O que o modelo prevê para as próximas 24h\n")
        b.append("As cartas que o modelo FutQuant aponta com **maior probabilidade de valorização** "
                 "(sinal de alta, confiança alta):\n")
        b.append(fq.md_table(rises, fc_cols))
    if falls:
        b.append("\n## ⚠️ Cuidado: o modelo projeta queda\n")
        b.append("Cartas com **maior probabilidade de desvalorizar** nas próximas 24h — evite comprar agora:\n")
        b.append(fq.md_table(falls, [("player_name","Jogador"),("rating","OVR"),("price","Preço atual"),
                                     ("prev24","Variação prevista")]))

    # Metodologia (E-E-A-T)
    b.append("\n## 📐 Como o FutQuant lê o mercado\n")
    b.append("Nossos números vêm de **centenas de milhões de pontos de preço** coletados de múltiplas fontes do "
             "mercado do EA FC, atualizados várias vezes ao dia. Antes de publicar, removemos **anomalias de preço** "
             "(cotações irreais de cartas extintas ou erros de coleta). As previsões usam um modelo treinado no "
             "histórico de cada carta, considerando **médias móveis (24h e 7 dias)**, **níveis de suporte e "
             "resistência** e a volatilidade recente. Por isso você vê aqui o que a maioria dos sites não mostra: "
             "não só o preço, mas **para onde ele tende a ir**.\n")

    # FAQ estruturado (vira FAQPage JSON-LD via frontmatter)
    faqs = []
    if top_up:
        faqs.append((f"Qual foi a maior alta do EA FC hoje ({today})?",
                     f"{top_up['player_name']} ({top_up['rating']}, {top_up.get('league') or 'sem liga'}), "
                     f"com +{top_up['d24']}% em 24h, a {fq.fmt_coins(top_up['price'])} coins no {plat}."))
    if top_down:
        faqs.append(("E a maior queda do dia?",
                     f"{top_down['player_name']} ({top_down['rating']}), {top_down['d24']}% em 24h, "
                     f"a {fq.fmt_coins(top_down['price'])} coins."))
    if rises:
        rb = rises[0]
        faqs.append(("Qual carta tem mais chance de subir amanhã no EA FC?",
                     f"Pelo modelo FutQuant, {rb['player_name']} ({rb['rating']}) — "
                     f"{int(float(rb['prob_alta']))}% de probabilidade de alta, a {fq.fmt_coins(rb['price'])} coins."))
    faqs.append(("O mercado do EA FC está em alta ou baixa hoje?",
                 f"Hoje o mercado está em {sentiment.replace('**','')}, com {up_n} cartas em alta "
                 f"contra {down_n} em queda (média {avg}%)."))
    faqs.append(("Os dados de preço do FutQuant são confiáveis?",
                 "Sim — preços reais do mercado, atualizados várias vezes ao dia e filtrados contra anomalias. "
                 "As previsões são probabilísticas e servem de apoio, não garantia."))
    b.append(fq.faq_block(faqs))
    b.append(fq.disclaimer(plat))

    tags = ["mercado", "precos", "previsoes", "altas-e-baixas", a.platform]
    print(fq.write_post(a.out, slug, title, desc, tags, "\n".join(b), featured=True, faq=faqs))

if __name__ == "__main__":
    main()
