/**
 * UI Component Library - Entry Point
 *
 * Export all reusable, accessible, and customizable components.
 * Includes both Standard and Quantum (Next-Gen) design systems.
 */

// Design Tokens
import '../styles/tokens.css';          // Standard ERP Theme
import '../styles/quantum-tokens.css';  // Quantum Neon Theme

// Standard Components (Legacy/Stable)
export { default as Button } from './Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './Button';

export { default as Input } from './Input';
export type { InputProps, InputVariant, InputSize } from './Input';

// Quantum Components (Next-Gen/Experimental)
export { QuantumButton } from './QuantumButton';
export type { QuantumButtonProps } from './QuantumButton';

export { QuantumInput } from './QuantumInput';
export type { QuantumInputProps } from './QuantumInput';

export { QuantumCard, QuantumCardHeader, QuantumCardContent, QuantumCardFooter } from './QuantumCard';
export type { QuantumCardProps } from './QuantumCard';

export { QuantumBadge } from './QuantumBadge';
export type { QuantumBadgeProps } from './QuantumBadge';

