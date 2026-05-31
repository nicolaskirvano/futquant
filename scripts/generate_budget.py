#!/usr/bin/env python3
"""FutQuant — post 'Joias baratas' (cartas com bom rating e preço baixo, custo-benefício)."""
import argparse, os, sys
import fqlib as fq

def query(platform):
    return f"""
      SELECT player_name, rating, league, position, toInt64(current_price) AS price,
             round(change_pct_7d,1) AS d7
      FROM {fq.U}
      WHERE platform='{platform}' AND {fq.QUALITY} AND rating>=83
        AND current_price BETWEEN 1500 AND 15000
        AND change_pct_24h BETWEEN -15 AND 60{fq.seg()}
      ORDER BY rating DESC, current_price ASC LIMIT 15"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="ps", choices=["ps", "pc"])
    ap.add_argument("--ch-ssh", default="local")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "src", "content", "posts"))
    a = ap.parse_args()
    rows = fq.ch_query(query(a.platform), a.ch_ssh)
    if len(rows) < 4:
        print("poucas joias hoje; pulando", file=sys.stderr); sys.exit(0)
    plat = fq.PLAT_LABEL[a.platform]; today = fq.today_br_str()
    top = rows[0]
    slug = f"jogadores-baratos-ea-fc-{fq.date_slug()}-{a.platform}"
    seg = fq.seg_label()
    title = (f"Jogadores baratos de {seg} no EA FC ({today}) — joias por menos de 15k — {plat}" if seg
             else f"Jogadores baratos e bons no EA FC ({today}) — joias 83+ por menos de 15k — {plat}")
    desc = (f"As melhores cartas custo-benefício do EA FC Ultimate Team em {today} ({plat}): "
            f"jogadores 83+ por menos de 15 mil coins para montar time forte gastando pouco.")
    cols = [("player_name","Jogador"),("rating","OVR"),("position","Pos"),("league","Liga"),("price","Preço"),("d7","7d")]
    body = []
    body.append(f"Dá para montar um time forte no **EA FC Ultimate Team** sem torrar coins. O **FutQuant** filtrou as "
                f"**cartas 83+ que custam menos de 15 mil coins** em **{today}** no **{plat}** — puro custo-benefício, "
                f"sem anomalias de preço.\n")
    body.append(f"> 💰 **Melhor pechincha:** {top['player_name']} ({top['rating']}) por apenas "
                f"{fq.fmt_coins(top['price'])} coins.\n")
    body.append("## 💎 Joias baratas (83+, abaixo de 15k)\n")
    body.append("Ordenadas por rating; *7d* mostra a variação na semana (quanto menor, mais 'no fundo' a carta está):\n")
    body.append(fq.md_table(rows, cols))
    body.append("\n## 📈 Destaques\n")
    for c in rows[:5]:
        d7 = c.get("d7")
        nota = ""
        try:
            d7f = float(d7)
            if d7f <= -8: nota = " — vem **caindo na semana**, pode ser ponto de entrada barato."
            elif d7f >= 15: nota = " — já **valorizando**, sinal de procura crescente."
        except (TypeError, ValueError): pass
        body.append(f"- **{c['player_name']} ({c['rating']}, {c.get('position') or '—'})** da {c.get('league') or '—'}, "
                    f"a apenas **{fq.fmt_coins(c['price'])} coins**{nota}\n")
    body.append("\n## Por que estas cartas?\n")
    body.append("- **Rating 83+** garante atributos competitivos para a maioria dos modos.\n"
                "- **Abaixo de 15k** cabe em qualquer banca, ideal para início de temporada ou times secundários.\n"
                "- Filtramos preços anômalos para você não cair em cotação irreal.\n")
    body.append(fq.methodology())
    faqs = []
    faqs.append((f"Qual o melhor jogador barato do EA FC hoje ({today})?",
                 f"{top['player_name']} ({top['rating']}, {top.get('league') or 'sem liga'}) aparece como melhor "
                 f"custo-benefício, a {fq.fmt_coins(top['price'])} coins no {plat}."))
    faqs.append(("Quais os melhores jogadores baratos para começar no EA FC Ultimate Team?",
                 "Cartas com rating 83+ que custam menos de 15 mil coins entregam o melhor custo-benefício para "
                 "montar um time competitivo gastando pouco. A lista é atualizada todos os dias."))
    faqs.append(("Esses preços são reais?",
                 "Sim — vêm do mercado do EA FC, atualizados várias vezes ao dia e filtrados contra anomalias."))
    body.append(fq.faq_block(faqs))
    body.append(fq.disclaimer(plat))
    print(fq.write_post(a.out, slug, title, desc, ["baratos","custo-beneficio","budget",a.platform],
                        "\n".join(body), faq=faqs))

if __name__ == "__main__":
    main()
