import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import '../../styles/tokens.css';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

/**
 * Professional Button Component
 * 
 * Features:
 * - Composable: Accepts icons and children
 * - Reusable: Multiple variants and sizes
 * - Accessible: Keyboard navigation, focus states, aria attributes
 * - Customizable: CSS variables for theming
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className = '',
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = `
      inline-flex items-center justify-center
      font-medium rounded-md
      transition-all duration-200 ease-in-out
      focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
      disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
      ${fullWidth ? 'w-full' : ''}
    `;

    const variantStyles = {
      primary: `
        bg-[var(--color-primary-500)] text-white
        hover:bg-[var(--color-primary-600)]
        active:bg-[var(--color-primary-700)]
        focus-visible:ring-[var(--color-primary-500)]
        shadow-sm hover:shadow-md
      `,
      secondary: `
        bg-[var(--color-neutral-100)] text-[var(--color-neutral-900)]
        hover:bg-[var(--color-neutral-200)]
        active:bg-[var(--color-neutral-300)]
        focus-visible:ring-[var(--color-neutral-500)]
      `,
      outline: `
        bg-transparent border border-[var(--color-neutral-300)] text-[var(--color-neutral-700)]
        hover:bg-[var(--color-neutral-50)] hover:border-[var(--color-neutral-400)]
        active:bg-[var(--color-neutral-100)]
        focus-visible:ring-[var(--color-primary-500)]
      `,
      ghost: `
        bg-transparent text-[var(--color-neutral-700)]
        hover:bg-[var(--color-neutral-100)]
        active:bg-[var(--color-neutral-200)]
        focus-visible:ring-[var(--color-neutral-500)]
      `,
      danger: `
        bg-[var(--color-error)] text-white
        hover:bg-[#dc2626]
        active:bg-[#b91c1c]
        focus-visible:ring-[var(--color-error)]
      `,
    };

    const sizeStyles = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 text-sm',
      lg: 'h-12 px-6 text-base',
    };

    const combinedClassName = `
      ${baseStyles}
      ${variantStyles[variant]}
      ${sizeStyles[size]}
      ${className}
    `.trim();

    return (
      <button
        ref={ref}
        className={combinedClassName}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
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
        
        {!isLoading && leftIcon && (
          <span className={`${children ? 'mr-2' : ''}`}>{leftIcon}</span>
        )}
        
        {children}
        
        {!isLoading && rightIcon && (
          <span className={`${children ? 'ml-2' : ''}`}>{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
