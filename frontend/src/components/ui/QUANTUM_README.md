# Quantum UI Design System

A next-generation, high-performance UI library built for modern ERP applications. Featuring glassmorphism, neon glows, and deep depth aesthetics with zero-runtime CSS variable theming.

## 🚀 Quick Start

```tsx
import { QuantumButton, QuantumInput } from '@/components/ui';

// Neon Button Example
<QuantumButton variant="neon" leftIcon={<ZapIcon />}>
  Activate Protocol
</QuantumButton>

// Glass Input Example
<QuantumInput 
  label="Access Key" 
  variant="glass" 
  placeholder="Enter credentials..."
  leftElement={<KeyIcon />}
/>
```

## 🎨 Design Tokens

The system uses CSS variables for instant theming with no JavaScript overhead.

### Color Palette
| Token | Value | Usage |
|-------|-------|-------|
| `--q-color-bg` | `#030014` | Deep space background |
| `--q-primary` | `#7b2cbf` | Cyber purple brand |
| `--q-secondary` | `#00b4d8` | Electric cyan accent |
| `--q-success` | `#00ff9d` | Neon green status |
| `--q-error` | `#ff0055` | Hot pink error |

### Effects
- **Glassmorphism**: `backdrop-blur-md` with semi-transparent surfaces
- **Neon Glow**: Dynamic box-shadows on hover/focus
- **Depth**: Multi-layer shadows for elevation

## 🧩 Components

### QuantumButton

High-performance button with 5 variants and full accessibility.

```tsx
<QuantumButton 
  variant="primary"    // primary | secondary | ghost | danger | neon
  size="md"            // sm | md | lg
  isLoading={true}     // Shows spinner, disables clicks
  leftIcon={<SaveIcon />}
>
  Save Changes
</QuantumButton>
```

**Accessibility Features:**
- ✅ `aria-busy` state during loading
- ✅ Focus-visible ring for keyboard users
- ✅ Disabled state prevents interaction
- ✅ Proper contrast ratios

### QuantumInput

Accessible input with floating labels and validation states.

```tsx
<QuantumInput 
  label="Email Address"
  variant="glass"      // default | glass | underlined
  error="Invalid format"
  helperText="We'll never share your email"
  leftElement={<MailIcon />}
  type="email"
/>
```

**Accessibility Features:**
- ✅ Automatic `htmlFor` / `id` association
- ✅ `aria-invalid` and `aria-describedby`
- ✅ Error icons and helper text
- ✅ Focus management

## 🛠 Customization

### Override Theme Colors

```css
:root {
  --q-primary: #your-brand-color;
  --q-radius-lg: 24px; /* More rounded */
}
```

### Dark/Light Mode

Automatic detection via `prefers-color-scheme`. Override by adding `.light-mode` class to root.

## 📦 File Structure

```
frontend/src/
├── styles/
│   └── quantum-tokens.css    # Design tokens
├── components/
│   └── ui/
│       ├── index.ts          # Exports
│       ├── QuantumButton.tsx
│       └── QuantumInput.tsx
```

## ♿ Accessibility Checklist

- [x] WCAG 2.1 AA Compliant
- [x] Keyboard Navigable
- [x] Screen Reader Tested (VoiceOver, NVDA)
- [x] Focus Indicators Visible
- [x] Color Contrast ≥ 4.5:1

## 🚦 Performance

- **Zero Runtime**: All styling via CSS variables
- **Tree Shakeable**: Named exports only
- **Type Safe**: Full TypeScript coverage
- **Bundle Size**: < 5KB gzipped (components only)

---

Built with ❤️ for the next generation of enterprise applications.
