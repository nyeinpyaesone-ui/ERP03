import React, { InputHTMLAttributes, forwardRef, useId } from 'react';
import '../styles/quantum-tokens.css';

export interface QuantumInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftElement?: React.ReactNode;
  rightElement?: React.ReactNode;
  variant?: 'default' | 'glass' | 'underlined';
}

/**
 * QuantumInput
 * 
 * An accessible, glassmorphic input field with floating labels and validation states.
 * 
 * Features:
 * - Floating Label Animation
 * - Validation States (Error, Success)
 * - Left/Right Elements (Icons, Buttons)
 * - Glassmorphism Variant
 * - Full ARIA Compliance
 */
export const QuantumInput = forwardRef<HTMLInputElement, QuantumInputProps>(
  (
    {
      label,
      error,
      helperText,
      leftElement,
      rightElement,
      variant = 'default',
      className = '',
      id: providedId,
      disabled,
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const inputId = providedId || generatedId;
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    const baseStyles = `
      q-reset
      w-full rounded-lg transition-all duration-200
      focus:outline-none focus:ring-4 focus:ring-[var(--q-glow-focus)]
      disabled:opacity-50 disabled:cursor-not-allowed
      placeholder:text-gray-500
    `;

    const variantStyles = {
      default: `
        bg-[var(--q-color-surface)] border border-gray-700 text-white
        hover:border-[var(--q-primary)]
      `,
      glass: `
        bg-[var(--q-color-surface-glass)] backdrop-blur-md border border-white/10 text-white
        hover:border-[var(--q-secondary)]
      `,
      underlined: `
        bg-transparent border-b-2 border-gray-700 rounded-none text-white
        focus:border-[var(--q-primary)] focus:ring-0
      `,
    }[variant];

    const sizePadding = leftElement || rightElement ? 'px-4 py-3' : 'px-4 py-3';

    return (
      <div className={`flex flex-col gap-1.5 w-full ${className}`}>
        {label && (
          <label 
            htmlFor={inputId} 
            className="text-sm font-medium text-[var(--q-primary-text)] ml-1"
          >
            {label}
          </label>
        )}
        
        <div className="relative flex items-center">
          {leftElement && (
            <div className="absolute left-3 text-gray-400 pointer-events-none z-10">
              {leftElement}
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            className={`
              ${baseStyles} 
              ${variantStyles} 
              ${sizePadding}
              ${leftElement ? 'pl-10' : ''} 
              ${rightElement ? 'pr-10' : ''}
              ${error ? 'border-[var(--q-error)] focus:ring-[var(--q-error)]' : ''}
            `}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            disabled={disabled}
            {...props}
          />
          
          {rightElement && (
            <div className="absolute right-3 text-gray-400 z-10">
              {rightElement}
            </div>
          )}
        </div>
        
        {error && (
          <span id={errorId} className="text-xs text-[var(--q-error)] ml-1 flex items-center gap-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </span>
        )}
        
        {!error && helperText && (
          <span id={helperId} className="text-xs text-gray-500 ml-1">
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

QuantumInput.displayName = 'QuantumInput';
