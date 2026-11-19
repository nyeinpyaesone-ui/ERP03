/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Noto Sans Myanmar', 'Myanmar Text', 'Padauk', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        erp: {
          background: '#F4F7FA',
          surface: '#FFFFFF',
          surfaceMuted: '#EAF0F5',
          foreground: '#172B3A',
          foregroundMuted: '#465B6B',
          primary: '#087A73',
          primaryForeground: '#FFFFFF',
          secondary: '#18344D',
          secondaryForeground: '#FFFFFF',
          accent: '#B76E16',
          border: '#738394',
        },
      },
    },
  },
  plugins: [],
};
