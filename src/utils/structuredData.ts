import type { ResolvedAstroPaperConfig } from "@/types/config";
import { toAbsoluteUrl, getSiteRoot } from "./url";

type JsonLdValue =
  | string
  | number
  | boolean
  | null
  | JsonLdValue[]
  | { [key: string]: JsonLdValue | undefined };

type BreadcrumbItem = {
  name: string;
  url: string;
};

type BlogPostingInput = {
  title?: string;
  description?: string;
  canonicalURL?: string;
  ogImage?: string;
  pubDatetime?: Date;
  modDatetime?: Date | null;
  author?: string;
  tags?: string[];
};

function compactJsonLd<T extends JsonLdValue>(value: T): T {
  if (Array.isArray(value)) {
    return value
      .filter(item => item !== undefined && item !== null && item !== "")
      .map(item => compactJsonLd(item)) as T;
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value)
        .filter(
          ([, entry]) => entry !== undefined && entry !== null && entry !== ""
        )
        .map(([key, entry]) => [key, compactJsonLd(entry as JsonLdValue)])
    ) as T;
  }

  return value;
}

export function serializeJsonLd(value: JsonLdValue): string {
  return JSON.stringify(compactJsonLd(value));
}

export function getPublisher(config: ResolvedAstroPaperConfig) {
  const publisher = config.site.publisher;
  const sameAs =
    publisher?.sameAs ??
    config.socials.map(({ url }) => url).filter(url => url.startsWith("http"));

  return compactJsonLd({
    "@type": publisher?.type ?? "Person",
    name: publisher?.name ?? config.site.author,
    url: publisher?.url ?? config.site.profile ?? config.site.url,
    ...(publisher?.logo && {
      logo: {
        "@type": "ImageObject",
        url: toAbsoluteUrl(publisher.logo),
      },
    }),
    sameAs,
  });
}

export function getGlobalStructuredData(config: ResolvedAstroPaperConfig) {
  const siteRoot = getSiteRoot();
  const publisher = getPublisher(config);
  const searchUrl = `${siteRoot}search?q={search_term_string}`;

  return compactJsonLd({
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebSite",
        "@id": `${siteRoot}#website`,
        url: siteRoot,
        name: config.site.title,
        description: config.site.description,
        inLanguage: config.site.lang,
        publisher,
        ...(config.features.search && {
          potentialAction: {
            "@type": "SearchAction",
            target: searchUrl,
            "query-input": "required name=search_term_string",
          },
        }),
      },
      {
        "@type": "Blog",
        "@id": `${siteRoot}#blog`,
        url: siteRoot,
        name: config.site.title,
        description: config.site.description,
        inLanguage: config.site.lang,
        publisher,
      },
      {
        ...publisher,
        "@id": `${siteRoot}#publisher`,
      },
    ],
  });
}

export function getBlogPostingStructuredData(
  config: ResolvedAstroPaperConfig,
  input: BlogPostingInput
) {
  const canonicalURL = input.canonicalURL ?? getSiteRoot();
  const canonicalId = canonicalURL.replace(/#.*$/, "");
  const publisher = getPublisher(config);
  const authorUrl = toAbsoluteUrl(config.site.profile);
  const imageUrl = toAbsoluteUrl(input.ogImage);

  return compactJsonLd({
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    "@id": `${canonicalId}#article`,
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": canonicalURL,
    },
    headline: input.title ?? config.site.title,
    description: input.description,
    image: imageUrl ? [imageUrl] : undefined,
    datePublished: input.pubDatetime?.toISOString(),
    dateModified:
      input.modDatetime?.toISOString() ?? input.pubDatetime?.toISOString(),
    author: [
      {
        "@type": "Person",
        name: input.author ?? config.site.author,
        url: authorUrl,
      },
    ],
    publisher,
    keywords: input.tags,
    inLanguage: config.site.lang,
    isAccessibleForFree: true,
    speakable: {
      "@type": "SpeakableSpecification",
      cssSelector: ["h1", "h2", "blockquote"],
    },
  });
}

export function getFaqStructuredData(
  faq: { q: string; a: string }[] | undefined
) {
  if (!faq || faq.length === 0) return null;
  return compactJsonLd({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faq.map(({ q, a }) => ({
      "@type": "Question",
      name: q,
      acceptedAnswer: { "@type": "Answer", text: a },
    })),
  });
}

export function getBreadcrumbStructuredData(items: BreadcrumbItem[]) {
  return compactJsonLd({
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: toAbsoluteUrl(item.url),
    })),
  });
}
