import "./globals.css";
import { ToastProvider } from "./ToastContext";

export const metadata = {
  title: "SentimentIQ — ML-Powered Sentiment Analysis",
  description:
    "Production-grade sentiment analysis platform powered by DistilBERT and GoEmotions. Analyze reviews, scrape e-commerce products, and get deep insights with emotion detection and aspect-based analysis.",
  keywords: "sentiment analysis, NLP, machine learning, product reviews, emotion detection",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0a0a0f" />
      </head>
      <body>
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
