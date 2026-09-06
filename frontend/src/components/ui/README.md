# Professional UI Component Library

A production-ready, accessible, and customizable React component library built for enterprise applications.

## Core Principles

- **Composable**: Combine small parts to build complex screens.
- **Reusable**: Use the same code in many places with consistent behavior.
- **Accessible**: WCAG 2.1 compliant with proper ARIA attributes and keyboard navigation.
- **Customizable**: Themeable via CSS variables (design tokens).

## Installation

Ensure the `tokens.css` is imported in your application entry point:

```tsx
// In your main.tsx or index.tsx
import './styles/tokens.css';
```

## Components

### Button

Professional button with multiple variants, sizes, and states.

```tsx
import { Button } from '@/components/ui';

// Basic usage
<Button variant="primary">Click Me</Button>

// With loading state
<Button isLoading>Loading...</Button>

// With icons
<Button leftIcon={<Icon />}>Upload</Button>

// Variants: primary | secondary | outline | ghost | danger
// Sizes: sm | md | lg
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | ButtonVariant | 'primary' | Visual style |
| size | ButtonSize | 'md' | Component size |
| isLoading | boolean | false | Shows spinner |
| leftIcon | ReactNode | - | Icon before text |
| rightIcon | ReactNode | - | Icon after text |
| fullWidth | boolean | false | Full width button |
| disabled | boolean | false | Disabled state |

### Input

Form input with label, validation states, and helper text.

```tsx
import { Input } from '@/components/ui';

// Basic usage
<Input label="Email" type="email" placeholder="you@example.com" />

// With error
<Input 
  label="Password" 
  error="Must be at least 8 characters" 
  variant="error" 
/>

// With helper text
<Input 
  label="Username" 
  helperText="Choose a unique name" 
/>

// With icon
<Input 
  label="Search" 
  leftElement={<SearchIcon />} 
/>
```

**Props:**
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| label | string | - | Field label |
| error | string | - | Error message |
| helperText | string | - | Helper text |
| variant | InputVariant | 'default' | default \| error \| success |
| size | InputSize | 'md' | sm \| md \| lg |
| leftElement | ReactNode | - | Icon/element on left |
| rightElement | ReactNode | - | Icon/element on right |
| disabled | boolean | false | Disabled state |

## Design Tokens

All components use CSS custom properties defined in `tokens.css`:

- **Colors**: Neutral palette, Primary brand, Semantic (success, warning, error)
- **Typography**: Font families, sizes, weights, line heights
- **Spacing**: 4px grid system (space-1 to space-16)
- **Borders**: Radius, widths, colors
- **Shadows**: Elevation levels (sm, md, lg, xl)
- **Transitions**: Fast, normal, slow easing curves
- **Focus Rings**: Accessible focus indicators

### Customization

Override tokens in your CSS to match your brand:

```css
:root {
  --color-primary-500: #your-brand-color;
  --font-sans: 'Your Font', sans-serif;
  --radius-md: 8px;
}
```

## Accessibility

All components follow WCAG 2.1 guidelines:

- ✅ Proper semantic HTML (`<button>`, `<label>`, `<input>`)
- ✅ ARIA attributes (`aria-busy`, `aria-invalid`, `aria-describedby`)
- ✅ Keyboard navigation (Tab, Enter, Space)
- ✅ Focus visible states with clear outlines
- ✅ Screen reader support with descriptive labels

## File Structure

```
frontend/src/
├── components/
│   └── ui/
│       ├── Button.tsx      # Button component
│       ├── Input.tsx       # Input component
│       └── index.ts        # Public API exports
├── styles/
│   └── tokens.css          # Design tokens (CSS variables)
└── App.examples.tsx        # Usage examples
```

## Testing

Test components with keyboard and screen readers:

1. **Keyboard**: Tab through all interactive elements
2. **Screen Reader**: Verify labels and announcements
3. **Visual**: Check focus rings and hover states
4. **Contrast**: Ensure color ratios meet WCAG AA standards

## Future Components

Planned additions:
- Modal, Card, Select
- Checkbox, Radio, Switch
- Badge, Avatar, Tooltip
- Spinner, Alert, Table

---

Built following industry best practices from Vercel, Stripe, and Atlassian design systems.
