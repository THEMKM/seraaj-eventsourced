# Build PxButton Component with Gaming Theme

## 📋 **Task Description**
Create a single `PxButton` component for the UI library with gaming aesthetics. This is the first component of our pixel-art design system.

## 🎯 **Exact Steps to Follow**

### Step 1: Create the component files
```bash
mkdir -p packages/ui/src/components/Button
touch packages/ui/src/components/Button/Button.tsx
touch packages/ui/src/components/Button/Button.module.css
touch packages/ui/src/components/Button/index.ts
```

### Step 2: Implement the Button component
Create `packages/ui/src/components/Button/Button.tsx`:

```typescript
import React from 'react';
import styles from './Button.module.css';
import { clsx } from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  className,
  disabled,
  children,
  ...props
}) => {
  return (
    <button
      className={clsx(
        styles.button,
        styles[variant],
        styles[size],
        {
          [styles.loading]: loading,
          [styles.fullWidth]: fullWidth,
        },
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className={styles.spinner}>⏳</span>
      ) : (
        children
      )}
    </button>
  );
};
```

### Step 3: Add gaming-themed CSS
Create `packages/ui/src/components/Button/Button.module.css`:

```css
.button {
  /* Base gaming button styles */
  font-family: 'Orbitron', monospace;
  font-weight: 500;
  border: 2px solid;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  
  /* Pixel-art clip-path border */
  clip-path: polygon(
    0 0, calc(100% - 8px) 0, 100% 8px,
    100% 100%, 8px 100%, 0 calc(100% - 8px)
  );
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 255, 255, 0.3);
}

/* Variants */
.primary {
  background: linear-gradient(135deg, #FF6B6B, #5F27CD);
  border-color: #FF6B6B;
  color: white;
}

.secondary {
  background: transparent;
  border-color: #00D2D3;
  color: #00D2D3;
}

.success {
  background: #10AC84;
  border-color: #10AC84;
  color: white;
}

/* Sizes */
.sm {
  padding: 8px 16px;
  font-size: 12px;
  min-height: 32px;
}

.md {
  padding: 12px 24px;
  font-size: 14px;
  min-height: 40px;
}

.lg {
  padding: 16px 32px;
  font-size: 16px;
  min-height: 48px;
}

/* States */
.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

.fullWidth {
  width: 100%;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

### Step 4: Create the index file
Create `packages/ui/src/components/Button/index.ts`:

```typescript
export { Button } from './Button';
export type { ButtonProps } from './Button';
```

### Step 5: Update main package exports
Update `packages/ui/src/index.ts`:

```typescript
export { Button as PxButton } from './components/Button';
export type { ButtonProps as PxButtonProps } from './components/Button';
```

### Step 6: Test the component
Create a test file `packages/ui/src/components/Button/Button.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Test Button</Button>);
    expect(screen.getByText('Test Button')).toBeInTheDocument();
  });

  it('applies variant classes', () => {
    render(<Button variant="secondary">Test</Button>);
    expect(screen.getByRole('button')).toHaveClass('secondary');
  });

  it('shows loading state', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByText('⏳')).toBeInTheDocument();
  });
});
```

## ✅ **Definition of Done**
- [ ] Button component renders correctly
- [ ] All 5 variants work (primary, secondary, success, warning, error)
- [ ] All 3 sizes work (sm, md, lg)
- [ ] Loading state shows spinner
- [ ] Gaming aesthetic with clip-path borders
- [ ] Hover effects work smoothly
- [ ] Component can be imported as `PxButton`
- [ ] TypeScript types are correct
- [ ] Basic tests pass

## 🧪 **How to Test**
1. Run `npm run build` in packages/ui
2. Create a test page importing `PxButton`
3. Verify all variants and sizes render
4. Test hover effects and loading state
5. Check TypeScript compilation

**This is a focused, single-component task that should take 1-2 hours to complete.**