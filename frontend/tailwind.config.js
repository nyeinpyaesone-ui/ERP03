/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Noto Sans Myanmar', 'Myanmar Text', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        erp: {
          background: '#F5F8F7',
          surface: '#FFFFFF',
          surfaceMuted: '#EAF1EF',
          foreground: '#162B29',
          foregroundMuted: '#475F5B',
          primary: '#0D6B63',
          primaryForeground: '#FFFFFF',
          secondary: '#D8E8E4',
          secondaryForeground: '#163E39',
          accent: '#A7660F',
          border: '#788B87',
        },
      },
    },
  },
  plugins: [],
};
