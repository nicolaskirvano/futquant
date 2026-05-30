import type { APIRoute } from "astro";
import config from "@/config";
import { generateLlmsFullTxt } from "@/utils/llms";

export const GET: APIRoute = async () => {
  if (!config.ai.enabled || !config.ai.llms.includeFullText) {
    return new Response("Not found", { status: 404 });
  }

  return new Response(await generateLlmsFullTxt(), {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
};
