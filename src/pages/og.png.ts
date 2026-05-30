import type { APIRoute } from "astro";
import satori from "satori";
import sharp from "sharp";
import { fontData, experimental_getFontFileURL } from "astro:assets";
import { getFontPathByWeight } from "@/utils/getFontPathByWeight";
import config from "@/config";

export const GET: APIRoute = async context => {
  const bodyFonts = fontData["--font-inter"];
  const displayFonts = fontData["--font-archivo"];
  const regularFontPath = getFontPathByWeight(bodyFonts, 400);
  const displayFontPath = getFontPathByWeight(displayFonts, 900);

  if (regularFontPath === undefined || displayFontPath === undefined) {
    throw new Error("Cannot find the font path.");
  }

  const [regularData, displayData] = await Promise.all([
    fetch(experimental_getFontFileURL(regularFontPath, context.url)).then(res =>
      res.arrayBuffer()
    ),
    fetch(experimental_getFontFileURL(displayFontPath, context.url)).then(res =>
      res.arrayBuffer()
    ),
  ]);

  const svg = await satori(
    {
      type: "div",
      props: {
        style: {
          background: "#0F1015",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          fontFamily: "Inter",
          color: "#F7F2E8",
        },
        children: [
          {
            type: "div",
            props: {
              style: {
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontSize: 22,
                color: "#8E8A7C",
              },
              children: [
                {
                  type: "span",
                  props: { children: "EAFC · FUT TRADING · BANCA BAIXA" },
                },
                {
                  type: "span",
                  props: { style: { color: "#E89860" }, children: "EAFC" },
                },
              ],
            },
          },
          {
            type: "div",
            props: {
              style: {
                border: "2px solid #25282F",
                background: "#1B1D24",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                width: "100%",
                height: "72%",
                padding: 48,
              },
              children: [
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex",
                      flexDirection: "column",
                      fontFamily: "Archivo",
                      fontSize: 108,
                      lineHeight: 0.88,
                      fontWeight: 900,
                      maxWidth: 780,
                    },
                    children: [
                      {
                        type: "span",
                        props: { children: "BANCA" },
                      },
                      {
                        type: "span",
                        props: {
                          style: { color: "#E89860" },
                          children: "BAIXA FC",
                        },
                      },
                    ],
                  },
                },
                {
                  type: "div",
                  props: {
                    style: {
                      display: "flex",
                      justifyContent: "space-between",
                      gap: 32,
                      width: "100%",
                      alignItems: "flex-end",
                    },
                    children: [
                      {
                        type: "p",
                        props: {
                          style: {
                            fontSize: 30,
                            lineHeight: 1.25,
                            margin: 0,
                            maxWidth: 620,
                            color: "#D4CDB8",
                          },
                          children: config.site.description,
                        },
                      },
                      {
                        type: "div",
                        props: {
                          style: {
                            fontSize: 26,
                            color: "#E89860",
                            fontWeight: 700,
                          },
                          children: new URL(config.site.url).hostname,
                        },
                      },
                    ],
                  },
                },
              ],
            },
          },
          {
            type: "div",
            props: {
              style: {
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                color: "#8E8A7C",
                fontSize: 20,
              },
              children: ["FLUXO · OFERTA · MOMENTO", "@bancabaixafc"],
            },
          },
        ],
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
