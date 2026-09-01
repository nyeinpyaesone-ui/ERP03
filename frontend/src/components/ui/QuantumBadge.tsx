import React from 'react';
import './quantum-tokens.css';

export interface QuantumBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'neon';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export const QuantumBadge = React.forwardRef<HTMLSpanElement, QuantumBadgeProps>(
  ({ variant = 'default', size = 'md', className = '', children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-full transition-all duration-200';
    
    const variants = {
      default: 'bg-[var(--q-color-surface-secondary)] text-[var(--q-color-text)] border border-[var(--q-color-border)]',
      success: 'bg-[var(--q-color-success-bg)] text-[var(--q-color-success)] border border-[var(--q-color-success)]',
      warning: 'bg-[var(--q-color-warning-bg)] text-[var(--q-color-warning)] border border-[var(--q-color-warning)]',
      danger: 'bg-[var(--q-color-danger-bg)] text-[var(--q-color-danger)] border border-[var(--q-color-danger)]',
      neon: 'bg-[var(--q-color-accent-bg)] text-[var(--q-color-accent)] border border-[var(--q-color-accent)] shadow-[0_0_10px_rgba(0,180,216,0.4)]',
    };

    const sizes = {
      sm: 'px-2 py-0.5 text-xs',
      md: 'px-3 py-1 text-sm',
      lg: 'px-4 py-1.5 text-base',
    };

    return (
      <span
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {children}
      </span>
    );
  }
);

QuantumBadge.displayName = 'QuantumBadge';
