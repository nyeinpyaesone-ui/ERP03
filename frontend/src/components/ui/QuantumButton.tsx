import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import '../styles/quantum-tokens.css';

export interface QuantumButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'neon';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
}

/**
 * QuantumButton
 * 
 * A high-performance, accessible button with glassmorphism and neon glow effects.
 * 
 * Features:
 * - 5 Variants (Primary, Secondary, Ghost, Danger, Neon)
 * - 3 Sizes
 * - Loading State with Spinner
 * - Full Accessibility (ARIA, Keyboard Nav)
 * - CSS Variable Theming (No runtime JS)
 */
export const QuantumButton = forwardRef<HTMLButtonElement, QuantumButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = `
      q-reset
      inline-flex items-center justify-center font-medium rounded-lg
      transition-all duration-150 ease-in-out
      focus:outline-none focus-visible:ring-4 focus-visible:ring-[var(--q-glow-focus)]
      disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
      active:scale-95
    `;

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-xs gap-1.5',
      md: 'px-5 py-2.5 text-sm gap-2',
      lg: 'px-7 py-3.5 text-base gap-2.5',
    }[size];

    const variantStyles = {
      primary: `
        bg-[var(--q-primary)] text-white
        hover:bg-[var(--q-primary-glow)] 
        shadow-[var(--q-shadow-md)] hover:shadow-[var(--q-glow-primary)]
        border border-transparent
      `,
      secondary: `
        bg-[var(--q-color-surface)] text-[var(--q-secondary)]
        border border-[var(--q-secondary)]
        hover:bg-[var(--q-secondary)] hover:text-white
        shadow-[var(--q-shadow-sm)]
      `,
      ghost: `
        bg-transparent text-[var(--q-primary-text)]
        hover:bg-[var(--q-color-surface-glass)]
        border border-transparent
      `,
      danger: `
        bg-transparent text-[var(--q-error)]
        border border-[var(--q-error)]
        hover:bg-[var(--q-error)] hover:text-white
        shadow-[var(--q-shadow-sm)]
      `,
      neon: `
        bg-[var(--q-color-bg)] text-[var(--q-success)]
        border border-[var(--q-success)]
        shadow-[0_0_10px_rgba(0,255,157,0.2)]
        hover:shadow-[0_0_25px_rgba(0,255,157,0.6)] hover:bg-[var(--q-success)] hover:text-black
        font-mono tracking-wider
      `,
    }[variant];

    return (
      <button
        ref={ref}
        className={`${baseStyles} ${sizeStyles} ${variantStyles} ${className}`}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        
        {!isLoading && leftIcon && <span className="flex items-center">{leftIcon}</span>}
        
        <span>{children}</span>
        
        {!isLoading && rightIcon && <span className="flex items-center">{rightIcon}</span>}
      </button>
    );
  }
);

QuantumButton.displayName = 'QuantumButton';
