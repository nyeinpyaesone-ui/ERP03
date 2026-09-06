import React, { InputHTMLAttributes, forwardRef, useId } from 'react';
import '../../styles/tokens.css';

export type InputVariant = 'default' | 'error' | 'success';
export type InputSize = 'sm' | 'md' | 'lg';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  variant?: InputVariant;
  size?: InputSize;
  leftElement?: React.ReactNode;
  rightElement?: React.ReactNode;
}

/**
 * Professional Input Component
 * 
 * Features:
 * - Composable: Supports label, helper text, icons/elements
 * - Reusable: Multiple sizes and validation states
 * - Accessible: Proper labels, aria-describedby, focus management
 * - Customizable: CSS variables for theming
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      variant = 'default',
      size = 'md',
      leftElement,
      rightElement,
      className = '',
      id: propId,
      disabled,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = propId || generatedId;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    const baseStyles = `
      w-full rounded-md border bg-white
      transition-all duration-200 ease-in-out
      placeholder:text-[var(--color-neutral-400)]
      disabled:bg-[var(--color-neutral-100)] disabled:cursor-not-allowed
      focus:outline-none focus:ring-2 focus:ring-offset-0
    `;

    const variantStyles = {
      default: `
        border-[var(--color-neutral-300)] text-[var(--color-neutral-900)]
        hover:border-[var(--color-neutral-400)]
        focus:border-[var(--color-primary-500)] focus:ring-[var(--color-primary-500)]
      `,
      error: `
        border-[var(--color-error)] text-[var(--color-neutral-900)]
        hover:border-[#dc2626]
        focus:border-[var(--color-error)] focus:ring-[var(--color-error)]
      `,
      success: `
        border-[var(--color-success)] text-[var(--color-neutral-900)]
        hover:border-[#059669]
        focus:border-[var(--color-success)] focus:ring-[var(--color-success)]
      `,
    };

    const sizeStyles = {
      sm: 'h-8 px-2 text-xs',
      md: 'h-10 px-3 text-sm',
      lg: 'h-12 px-4 text-base',
    };

    const hasLeftElement = !!leftElement;
    const hasRightElement = !!rightElement;

    const paddingLeft = hasLeftElement ? (size === 'sm' ? 'pl-8' : size === 'lg' ? 'pl-10' : 'pl-9') : '';
    const paddingRight = hasRightElement ? (size === 'sm' ? 'pr-8' : size === 'lg' ? 'pr-10' : 'pr-9') : '';

    const combinedClassName = `
      ${baseStyles}
      ${variantStyles[variant]}
      ${sizeStyles[size]}
      ${paddingLeft}
      ${paddingRight}
      ${className}
    `.trim();

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className={`
              block mb-1.5 font-medium text-sm
              ${disabled ? 'text-[var(--color-neutral-400)]' : 'text-[var(--color-neutral-700)]'}
              ${variant === 'error' ? 'text-[var(--color-error)]' : ''}
            `}
          >
            {label}
          </label>
        )}

        <div className="relative">
          {leftElement && (
            <div
              className={`
                absolute top-0 bottom-0 flex items-center
                ${size === 'sm' ? 'left-2' : size === 'lg' ? 'left-3' : 'left-2.5'}
                text-[var(--color-neutral-400)]
                ${disabled ? 'text-[var(--color-neutral-300)]' : ''}
              `}
            >
              {leftElement}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            className={combinedClassName}
            disabled={disabled}
            aria-invalid={variant === 'error' ? 'true' : undefined}
            aria-describedby={
              error ? errorId : helperText ? helperId : undefined
            }
            {...props}
          />

          {rightElement && (
            <div
              className={`
                absolute top-0 bottom-0 flex items-center
                ${size === 'sm' ? 'right-2' : size === 'lg' ? 'right-3' : 'right-2.5'}
                text-[var(--color-neutral-400)]
                ${disabled ? 'text-[var(--color-neutral-300)]' : ''}
              `}
            >
              {rightElement}
            </div>
          )}
        </div>

        {error && (
          <p
            id={errorId}
            className="mt-1.5 text-xs text-[var(--color-error)] flex items-center"
            role="alert"
          >
            <svg
              className="w-3 h-3 mr-1"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </p>
        )}

        {!error && helperText && (
          <p
            id={helperId}
            className="mt-1.5 text-xs text-[var(--color-neutral-500)]"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
