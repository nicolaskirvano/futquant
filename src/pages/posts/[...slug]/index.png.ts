import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import { fontData, experimental_getFontFileURL } from "astro:assets";
import satori from "satori";
import sharp from "sharp";
import { getFontPathByWeight } from "@/utils/getFontPathByWeight";
import { getPostSlug } from "@/utils/getPostPaths";
import config from "@/config";

export async function getStaticPaths() {
  if (!config.features.dynamicOgImage) {
    return [];
  }

  const posts = await getCollection("posts").then(p =>
    p.filter(({ data }) => !data.draft && !data.ogImage)
  );

  return posts.map(post => ({
    params: { slug: getPostSlug(post.id, post.filePath) },
    props: post,
  }));
}

export const GET: APIRoute = async ({ props, url }) => {
  if (!config.features.dynamicOgImage) {
    return new Response(null, { status: 404, statusText: "Not found" });
  }

  const bodyFonts = fontData["--font-inter"];
  const displayFonts = fontData["--font-archivo"];
  const regularFontPath = getFontPathByWeight(bodyFonts, 400);
  const displayFontPath = getFontPathByWeight(displayFonts, 900);

  if (regularFontPath === undefined || displayFontPath === undefined) {
    throw new Error("Cannot find the font path.");
  }

  const [regularData, displayData] = await Promise.all([
    fetch(experimental_getFontFileURL(regularFontPath, url)).then(res =>
      res.arrayBuffer()
    ),
    fetch(experimental_getFontFileURL(displayFontPath, url)).then(res =>
      res.arrayBuffer()
    ),
  ]);

  const svg = await satori(
    {
      type: "div",
      props: {
        style: {
          background: "#0F1015",
          color: "#F7F2E8",
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Inter",
        },
        children: {
          type: "div",
          props: {
            style: {
              border: "2px solid #25282F",
              background: "#1B1D24",
              width: "88%",
              height: "80%",
              padding: 48,
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            },
            children: [
              {
                type: "div",
                props: {
                  style: {
                    width: "100%",
                    display: "flex",
                    justifyContent: "space-between",
                    color: "#8E8A7C",
                    fontSize: 22,
                  },
                  children: [
                    "EAFC · FUT TRADING · BANCA BAIXA",
                    {
                      type: "span",
                      props: {
                        style: { color: "#E89860" },
                        children: "EAFC",
                      },
                    },
                  ],
                },
              },
              {
                type: "div",
                props: {
                  style: {
                    fontFamily: "Archivo",
                    fontSize: 82,
                    lineHeight: 0.98,
                    fontWeight: 900,
                    color: "#F7F2E8",
                    maxHeight: "62%",
                    overflow: "hidden",
                  },
                  children: props.data.title,
                },
              },
              {
                type: "div",
                props: {
                  style: {
                    display: "flex",
                    justifyContent: "space-between",
                    width: "100%",
                    color: "#8E8A7C",
                    fontSize: 24,
                  },
                  children: [
                    `por ${props.data.author}`,
                    {
                      type: "span",
                      props: {
                        style: { color: "#E89860", fontWeight: 700 },
                        children: config.site.title,
                      },
                    },
                  ],
                },
              },
            ],
          },
        },
      },
    },
    {
      width: 1200,
      height: 630,
      embedFont: true,
      fonts: [
        {
          name: "Inter",
          data: regularData,
          weight: 400,
          style: "normal",
        },
        {
          name: "Archivo",
          data: displayData,
          weight: 900,
          style: "normal",
        },
      ],
    }
  );

  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();

  return new Response(new Uint8Array(pngBuffer), {
    headers: { "Content-Type": "image/png" },
  });
};
