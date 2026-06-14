import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0f1419',
        surface: '#1a2332',
        surface2: '#243044',
        border: '#2d3a4f',
        text: '#e8edf4',
        muted: '#8b9cb3',
        accent: '#3b82f6',
        success: '#22c55e',
        fail: '#ef4444',
        warn: '#f59e0b',
      },
    },
  },
  plugins: [],
} satisfies Config;
