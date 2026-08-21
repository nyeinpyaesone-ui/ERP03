import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(null);

/**
 * Provides theme state and controls to descendant components.
 * @returns {JSX.Element} The theme context provider containing the child components.
 */
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, isDark: theme === 'dark' }}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Access the current theme state and controls.
 * @returns {{ theme: string, toggleTheme: Function, isDark: boolean }} The theme context value.
 * @throws {Error} If called outside a `ThemeProvider`.
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}

