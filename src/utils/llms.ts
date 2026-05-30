import { getRelativeLocaleUrl } from "astro:i18n";
import { getCollection, type CollectionEntry } from "astro:content";
import config from "@/config";
import { getPostUrl } from "@/utils/getPostPaths";
import { getSortedPosts } from "@/utils/getSortedPosts";
import { toAbsoluteUrl } from "@/utils/url";

type EntryWithBody = {
  body?: string;
};

function escapeMarkdown(value: string): string {
  return value.replace(/\[/g, "\\[").replace(/\]/g, "\\]");
}

function normalizeMarkdownBody(value: string): string {
  return value
    .replace(/^import\s.+$/gm, "")
    .replace(/^export\s.+$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function getEntryBody(entry: CollectionEntry<"posts" | "pages">): string {
  return normalizeMarkdownBody(((entry as EntryWithBody).body ?? "").trim());
}

function formatPostLink(post: CollectionEntry<"posts">): string {
  const url = toAbsoluteUrl(
    getPostUrl(post.id, post.filePath, config.site.lang)
  );
  const details = [
    post.data.description,
    post.data.tags.length > 0 ? `Tags: ${post.data.tags.join(", ")}` : "",
    `Published: ${post.data.pubDatetime.toISOString().slice(0, 10)}`,
  ]
    .filter(Boolean)
    .join(" ");

  return `- [${escapeMarkdown(post.data.title)}](${url}): ${details}`;
}

function formatPageLink(page: CollectionEntry<"pages">): string {
  const url = toAbsoluteUrl(getRelativeLocaleUrl(config.site.lang, page.id));
  return `- [${escapeMarkdown(page.data.title)}](${url}): ${
    page.data.description ?? "Static page"
  }`;
}

async function getPublishedContent() {
  const posts = getSortedPosts(await getCollection("posts")).slice(
    0,
    config.ai.llms.maxPosts
  );
  const pages = await getCollection("pages");

  return { posts, pages };
}

export async function generateLlmsTxt(): Promise<string> {
  const { posts, pages } = await getPublishedContent();
  const siteUrl = toAbsoluteUrl("/") ?? config.site.url;
  const lines = [
    `# ${config.site.title}`,
    "",
    `> ${config.site.description}`,
    "",
    `Canonical site: ${siteUrl}`,
    `Primary language: ${config.site.lang}`,
    `Author: ${config.site.author}`,
    "",
    "This file is a concise guide for language models and AI search systems. Use canonical URLs for citations, prefer current published posts, and treat post dates as part of the answer context.",
    "",
    "## Key Pages",
    ...pages.map(formatPageLink),
    "",
    "## Recent Posts",
    ...posts.map(formatPostLink),
    "",
    "## Feeds and Discovery",
    `- [RSS feed](${toAbsoluteUrl("/rss.xml")}): Latest published posts.`,
    `- [Sitemap index](${toAbsoluteUrl("/sitemap-index.xml")}): Complete crawlable URL set.`,
    ...(config.ai.llms.includeFullText
      ? [
          `- [Full LLM context](${toAbsoluteUrl(
            "/llms-full.txt"
          )}): Markdown export of the listed published content.`,
        ]
      : []),
    "",
    "## Structured Data",
    "- The site publishes schema.org JSON-LD for WebSite, Blog, publisher, BlogPosting, and breadcrumbs where applicable.",
  ];

  return `${lines.join("\n").trim()}\n`;
}

export async function generateLlmsFullTxt(): Promise<string> {
  if (!config.ai.llms.includeFullText) {
    return generateLlmsTxt();
  }

  const { posts, pages } = await getPublishedContent();
  const sections = [
    `# ${config.site.title} Full LLM Context`,
    "",
    `> ${config.site.description}`,
    "",
    `Source index: ${toAbsoluteUrl("/llms.txt")}`,
    "",
    "## Pages",
    ...pages.flatMap(page => [
      "",
      `### ${page.data.title}`,
      "",
      `URL: ${toAbsoluteUrl(getRelativeLocaleUrl(config.site.lang, page.id))}`,
      page.data.description ? `Description: ${page.data.description}` : "",
      "",
      getEntryBody(page),
    ]),
    "",
    "## Posts",
    ...posts.flatMap(post => [
      "",
      `### ${post.data.title}`,
      "",
      `URL: ${toAbsoluteUrl(getPostUrl(post.id, post.filePath, config.site.lang))}`,
      `Published: ${post.data.pubDatetime.toISOString()}`,
      post.data.modDatetime
        ? `Modified: ${post.data.modDatetime.toISOString()}`
        : "",
      `Description: ${post.data.description}`,
      `Tags: ${post.data.tags.join(", ")}`,
      "",
      getEntryBody(post),
    ]),
  ].filter(line => line !== "");

  return `${sections.join("\n").trim()}\n`;
}
