import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'f1-black': '#0A0A0A',
        'f1-red': '#E10600',
      },
    },
  },
  plugins: [],
}
export default config
