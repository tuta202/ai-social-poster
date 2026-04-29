import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0A0E1A',
          900: '#0D1120',
          800: '#111827',
          700: '#1A2235',
        },
        brand: {
          purple: '#7C3AED',
          'purple-light': '#A855F7',
          cyan: '#06B6D4',
          'cyan-light': '#22D3EE',
        }
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      backgroundImage: {
        'dot-grid': 'radial-gradient(circle, rgba(124,58,237,0.15) 1px, transparent 1px)',
        'gradient-brand': 'linear-gradient(135deg, #7C3AED, #06B6D4)',
      },
      backgroundSize: {
        'dot-grid': '24px 24px',
      },
      boxShadow: {
        'glow-purple': '0 0 20px rgba(124,58,237,0.4)',
        'glow-cyan': '0 0 20px rgba(6,182,212,0.4)',
      }
    },
  },
  plugins: [],
} satisfies Config
