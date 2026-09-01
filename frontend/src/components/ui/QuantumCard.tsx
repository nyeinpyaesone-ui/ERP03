import React from 'react';
import './quantum-tokens.css';

export interface QuantumCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'neon-border';
  hoverEffect?: boolean;
  children: React.ReactNode;
}

export const QuantumCard = React.forwardRef<HTMLDivElement, QuantumCardProps>(
  ({ variant = 'default', hoverEffect = false, className = '', children, ...props }, ref) => {
    const baseStyles = 'relative overflow-hidden rounded-xl transition-all duration-300';
    
    const variants = {
      default: 'bg-[var(--q-color-surface)] border border-[var(--q-color-border)] shadow-[var(--q-shadow-md)]',
      glass: 'bg-[var(--q-color-glass)] backdrop-blur-md border border-[var(--q-color-glass-border)] shadow-[var(--q-shadow-lg)]',
      'neon-border': 'bg-[var(--q-color-surface)] border-2 border-[var(--q-color-primary)] shadow-[0_0_15px_rgba(123,44,191,0.3)]',
    };

    const hoverStyles = hoverEffect 
      ? 'hover:-translate-y-1 hover:shadow-[var(--q-shadow-glow)] hover:border-[var(--q-color-accent)]' 
      : '';

    return (
      <div
        ref={ref}
        className={`${baseStyles} ${variants[variant]} ${hoverStyles} ${className}`}
        {...props}
      >
        {children}
      </div>
    );
  }
);

QuantumCard.displayName = 'QuantumCard';

// Sub-components for composition
export const QuantumCardHeader = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 pb-4 border-b border-[var(--q-color-border)] ${className}`}>
    <h3 className="text-lg font-semibold text-[var(--q-color-text)]">{children}</h3>
  </div>
);

export const QuantumCardContent = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 ${className}`}>{children}</div>
);

export const QuantumCardFooter = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 pt-4 border-t border-[var(--q-color-border)] bg-[var(--q-color-surface-secondary)] ${className}`}>
    {children}
  </div>
);
