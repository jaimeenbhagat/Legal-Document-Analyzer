import "./globals.css"

export const metadata = {
  title: "Legal Document Analyzer",
  description: "AI-Powered Legal Document Analysis using RAG",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
