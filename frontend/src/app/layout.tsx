import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Shopping Deals Chat Agent',
  description: 'AI-powered chat agent that finds the best shopping deals',
  other: {
    'impact-site-verification': 'cc0b73e4-0349-4d50-a969-90f273f33231',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
} 