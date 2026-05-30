import config from "@/config";

export function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

export function toAbsoluteUrl(
  pathOrUrl: string | undefined
): string | undefined {
  if (!pathOrUrl) return undefined;

  try {
    return new URL(pathOrUrl).href;
  } catch {
    return new URL(
      pathOrUrl.replace(/^\/+/, ""),
      `${trimTrailingSlash(config.site.url)}/`
    ).href;
  }
}

export function getSiteRoot(): string {
  return `${trimTrailingSlash(config.site.url)}/`;
}
