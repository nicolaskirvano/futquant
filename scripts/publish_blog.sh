#!/usr/bin/env bash
# Engine compartilhada — publica QUALQUER blog: publish_blog.sh <slug>
# Geradores vêm de /opt/blog-factory/_engine/scripts (fonte única). Conteúdo e segmento
# vêm do repo do blog (/opt/blog-factory/<slug>). Idempotente.
set -euo pipefail
ENGINE=/opt/blog-factory/_engine
slug="${1:?uso: publish_blog.sh <slug>}"
blog="/opt/blog-factory/$slug"
cd "$blog"

# segmento do blog (FQ_SEG / FQ_SEG_LABEL); vazio = geral
if [ -f scripts/blog.env ]; then set -a; . scripts/blog.env; set +a; fi
RUN_LEAGUE_ROTATOR="${RUN_LEAGUE_ROTATOR:-1}"

# sincroniza conteúdo com o remoto
git fetch -q origin master
git reset --hard -q origin/master

OUT="$blog/src/content/posts"
for plat in ps pc; do
  python3 "$ENGINE/scripts/generate_market_daily.py" --ch-ssh local --platform "$plat" --out "$OUT" || true
  python3 "$ENGINE/scripts/generate_investments.py"  --ch-ssh local --platform "$plat" --out "$OUT" || true
  python3 "$ENGINE/scripts/generate_budget.py"       --ch-ssh local --platform "$plat" --out "$OUT" || true
done
[ "$RUN_LEAGUE_ROTATOR" = "1" ] && python3 "$ENGINE/scripts/generate_league.py" --ch-ssh local --platform ps --out "$OUT" || true

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git -c user.name="${slug}-bot" -c user.email="bot@${slug}.local" \
      commit -q -m "conteudo: $(date -u +%FT%RZ)"
  git push -q origin master
  echo "PUBLICADO $slug $(date -u +%FT%RZ)"
else
  echo "nada novo $slug $(date -u +%FT%RZ)"
fi
