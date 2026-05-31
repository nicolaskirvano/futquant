#!/usr/bin/env python3
"""FutQuant — post 'Melhores investimentos do dia' (cartas em tendência consistente de alta)."""
import argparse, os, sys
import fqlib as fq

def query(platform):
    return f"""
      SELECT player_name, rating, league, position, toInt64(current_price) AS price,
             round(change_pct_24h,1) AS d24, round(change_pct_7d,1) AS d7
      FROM {fq.U}
      WHERE platform='{platform}' AND {fq.QUALITY} AND rating>=84
        AND current_price BETWEEN 15000 AND 250000
        AND change_pct_24h BETWEEN 1 AND 40 AND change_pct_7d BETWEEN 5 AND 90
      ORDER BY change_pct_7d DESC LIMIT 15"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default="ps", choices=["ps", "pc"])
    ap.add_argument("--ch-ssh", default="local")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "src", "content", "posts"))
    a = ap.parse_args()
    rows = fq.ch_query(query(a.platform), a.ch_ssh)
    if len(rows) < 4:
        print("poucos investimentos hoje; pulando", file=sys.stderr); sys.exit(0)
    plat = fq.PLAT_LABEL[a.platform]; today = fq.today_br_str()
    top = rows[0]
    slug = f"melhores-investimentos-ea-fc-{fq.date_slug()}-{a.platform}"
    title = f"Melhores investimentos no EA FC hoje ({today}) — {plat}"
    desc = (f"As cartas 84+ do EA FC Ultimate Team com tendência de alta mais consistente em {today} "
            f"({plat}): candidatas a valorização com base em dados de 24h e 7 dias.")
    cols = [("player_name","Jogador"),("rating","OVR"),("league","Liga"),("price","Preço"),("d24","24h"),("d7","7d")]
    body = []
    body.append(f"Investir bem no **EA FC Ultimate Team** é ler tendência, não palpite. O **FutQuant** cruza a "
                f"variação de **24 horas e 7 dias** de mais de 18 mil cartas e destaca abaixo as **84+ que vêm "
                f"subindo de forma consistente** — as melhores candidatas a valorização em **{today}** no **{plat}**.\n")
    body.append(f"> 🔝 **Destaque:** {top['player_name']} ({top['rating']}) acumula **+{top['d7']}% em 7 dias** "
                f"(+{top['d24']}% nas últimas 24h), a {fq.fmt_coins(top['price'])} coins.\n")
    body.append("## 💎 Cartas em tendência de alta (84+)\n")
    body.append("Subindo em **24h e 7 dias** — o sinal mais confiável de momentum de mercado:\n")
    body.append(fq.md_table(rows, cols))
    body.append("\n## Como ler esta lista\n")
    body.append("- **24h** e **7d** positivos juntos = tendência sustentada, não pico isolado.\n"
                "- Prefira entrar em correções (quedas curtas dentro da alta) para reduzir risco.\n"
                "- Liquidez importa: cartas de ligas/rating populares vendem mais rápido.\n")
    body.append("\n## Perguntas frequentes\n")
    body.append(f"**Qual a melhor carta para investir hoje ({today}) no EA FC?**  \n"
                f"Pelos dados do FutQuant, {top['player_name']} ({top['rating']}, {top.get('league') or 'sem liga'}) "
                f"lidera, com +{top['d7']}% em 7 dias a {fq.fmt_coins(top['price'])} coins no {plat}.\n")
    body.append(f"**Esses dados são atualizados?**  \nSim — recalculados várias vezes ao dia a partir do mercado real, "
                f"sem anomalias de preço.\n")
    body.append(fq.disclaimer(plat))
    print(fq.write_post(a.out, slug, title, desc, ["investimentos","trading",a.platform], "\n".join(body), featured=False))

if __name__ == "__main__":
    main()
