import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Traviante — Find trips by vibe",
  description:
    "AI visual destination search. Upload a photo or describe your dream trip and discover matching Traviante destinations in seconds.",
  openGraph: {
    title: "Traviante — Find trips by vibe",
    description: "Search destinations by photo or natural language, powered by CLIP.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=Newsreader:ital,wght@0,300;0,400;1,300&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
