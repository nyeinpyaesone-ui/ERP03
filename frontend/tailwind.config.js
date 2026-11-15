/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Noto Sans Myanmar', 'Myanmar Text', 'sans-serif'],
      },
      colors: {
        erp: {
          background: '#F5F7F8',
          surface: '#FFFFFF',
          muted: '#EAF1F0',
          foreground: '#172B2A',
          secondary: '#526766',
          primary: '#087A73',
          primaryForeground: '#FFFFFF',
          secondarySurface: '#DCEFEB',
          secondaryForeground: '#174B47',
          accent: '#A96D16',
          border: '#768B89',
        },
      },
    },
  },
  plugins: [],
};
