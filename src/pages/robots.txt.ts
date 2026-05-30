import type { APIRoute } from "astro";
import config from "@/config";

const AI_SEARCH_USER_AGENTS = [
  "OAI-SearchBot",
  "ChatGPT-User",
  "Claude-SearchBot",
  "Claude-User",
  "PerplexityBot",
  "Perplexity-User",
];

const AI_TRAINING_USER_AGENTS = [
  "GPTBot",
  "ClaudeBot",
  "Google-Extended",
  "CCBot",
  "Applebot-Extended",
];

function getUserAgentRule(userAgent: string, allow: boolean): string {
  const lines = [
    `User-agent: ${userAgent}`,
    allow ? "Allow: /" : "Disallow: /",
  ];

  if (allow && config.ai.crawlers.crawlDelay) {
    lines.push(`Crawl-delay: ${config.ai.crawlers.crawlDelay}`);
  }

  return lines.join("\n");
}

const getRobotsTxt = (sitemapURL: URL) => `
User-agent: *
Allow: /

${[
  ...(config.ai.enabled
    ? AI_SEARCH_USER_AGENTS.map(userAgent =>
        getUserAgentRule(userAgent, config.ai.crawlers.allowSearchBots)
      )
    : []),
  ...(config.ai.enabled
    ? AI_TRAINING_USER_AGENTS.map(userAgent =>
        getUserAgentRule(userAgent, config.ai.crawlers.allowTrainingBots)
      )
    : []),
  ...(config.ai.enabled
    ? config.ai.crawlers.additionalUserAgents.map(userAgent =>
        getUserAgentRule(userAgent, true)
      )
    : []),
]
  .filter(Boolean)
  .join("\n\n")}

Sitemap: ${sitemapURL.href}
`;

export const GET: APIRoute = ({ site }) => {
  const sitemapURL = new URL("sitemap-index.xml", site);
  return new Response(getRobotsTxt(sitemapURL));
};
