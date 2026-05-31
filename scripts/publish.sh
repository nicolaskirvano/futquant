#!/usr/bin/env bash
# FutQuant — publicação automática: sincroniza repo, gera conteúdo do dia e dá push.
# Rodado pelo n8n (via SSH no host do ClickHouse). Idempotente: só commita se houver conteúdo novo.
set -euo pipefail
cd "$(dirname "$0")/.."

# segmento do blog (FQ_SEG / FQ_SEG_LABEL) — define o nicho. Vazio = blog geral.
if [ -f scripts/blog.env ]; then set -a; . scripts/blog.env; set +a; fi
RUN_LEAGUE_ROTATOR="${RUN_LEAGUE_ROTATOR:-1}"

# sincroniza com o remoto (descarta divergência local p/ evitar conflito de push)
git fetch -q origin master
git reset --hard -q origin/master

# gera os posts do dia (ClickHouse local). Cada gerador é tolerante a falha (|| true).
for plat in ps pc; do
  python3 scripts/generate_market_daily.py --ch-ssh local --platform "$plat" || true
  python3 scripts/generate_investments.py  --ch-ssh local --platform "$plat" || true
  python3 scripts/generate_budget.py       --ch-ssh local --platform "$plat" || true
done
# rotador de liga só faz sentido no blog geral (blogs segmentados já são de 1 nicho)
[ "$RUN_LEAGUE_ROTATOR" = "1" ] && python3 scripts/generate_league.py --ch-ssh local --platform ps || true

# commita e publica só se algo mudou
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git -c user.name="futquant-bot" -c user.email="bot@futquant.com" \
      commit -q -m "conteudo: mercado do dia $(date -u +%FT%RZ)"
  git push -q origin master
  echo "PUBLICADO $(date -u +%FT%RZ)"
else
  echo "nada novo $(date -u +%FT%RZ)"
fi
