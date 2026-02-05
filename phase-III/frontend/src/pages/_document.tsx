/**
 * _document.tsx - Custom Document
 *
 * Customizes the HTML document structure for the Next.js application.
 * Includes proper meta tags and CSS imports.
 */

import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta charSet="utf-8" />
        <meta name="theme-color" content="#2563eb" />
        <meta name="description" content="Todo AI Chatbot - Your intelligent task assistant" />

        {/* Favicon */}
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <body className="bg-gray-50 dark:bg-gray-950">
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
