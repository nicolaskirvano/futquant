import type { APIRoute } from "astro";
import config from "@/config";
import { generateLlmsTxt } from "@/utils/llms";

export const GET: APIRoute = async () => {
  if (!config.ai.enabled) {
    return new Response("Not found", { status: 404 });
  }

  return new Response(await generateLlmsTxt(), {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  });
};
