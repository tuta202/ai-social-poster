import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  className?: string
}

export default function PageWrapper({ children, className = '' }: Props) {
  return (
    <div
      className={`min-h-screen bg-[#0A0E1A] ${className}`}
      style={{
        backgroundImage: 'radial-gradient(circle, rgba(124,58,237,0.12) 1px, transparent 1px)',
        backgroundSize: '24px 24px',
      }}
    >
      {children}
    </div>
  )
}
