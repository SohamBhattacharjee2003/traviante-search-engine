import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Traviante — Your AI travel concierge",
  description:
    "Chat with Traviante's AI concierge. Describe your dream trip or upload a photo of a place you love, and discover premium destinations matched to your vibe.",
  openGraph: {
    title: "Traviante — Your AI travel concierge",
    description:
      "Conversational destination discovery. Describe a trip or share a photo; our AI surfaces premium matches.",
    type: "website",
  },
};

// Applied before first paint so a saved theme never flashes the default.
const noFlashTheme = `try{var t=localStorage.getItem('traviante-theme');if(t){document.documentElement.dataset.theme=t;}}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="aurora" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFlashTheme }} />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400&family=Inter:wght@400;500;600;700&family=Newsreader:ital,wght@0,300;0,400;1,300;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
