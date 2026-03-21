import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PathForge — AI-Powered Adaptive Onboarding',
  description: 'Parse what you claim, prove what you know, and get a personalized learning path generated from scratch — not from a pre-authored menu.',
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
