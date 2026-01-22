# Modern Toast Notification System

A beautiful, accessible, and fully-featured toast notification system built with React, Framer Motion, and design tokens.

## Features

- **Four toast variants**: Success, Error, Warning, and Info
- **Smooth animations**: Slide-in animations using Framer Motion
- **Progress indicator**: Visual progress bar showing time remaining
- **Hover to pause**: Pause countdown on hover to read longer messages
- **Auto-dismiss**: Configurable duration (default 3 seconds)
- **Manual dismiss**: Click close button or programmatic dismissal
- **Responsive positioning**: Top-right (default), bottom-right, top-left, bottom-left
- **Stack management**: Handles multiple toasts with smooth layout animations
- **Accessibility**: ARIA attributes and keyboard navigation support
- **Modern design**: Uses design tokens for consistent colors, shadows, and spacing

## Quick Start

### 1. Wrap your app with ToastProvider

```tsx
// app/layout.tsx
import { ToastProvider } from '@/components/ui/ToastContainer'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  )
}
```

### 2. Use the toast hook in your components

```tsx
import { useToast } from '@/components/ui/ToastContainer'

function MyComponent() {
  const { showSuccess, showError, showWarning, showInfo } = useToast()

  const handleSuccess = () => {
    showSuccess('Operation completed successfully!')
  }

  const handleError = () => {
    showError('Something went wrong. Please try again.')
  }

  const handleWarning = () => {
    showWarning('This action cannot be undone.')
  }

  const handleInfo = () => {
    showInfo('New features are available!')
  }

  return (
    <div>
      <button onClick={handleSuccess}>Show Success</button>
      <button onClick={handleError}>Show Error</button>
      <button onClick={handleWarning}>Show Warning</button>
      <button onClick={handleInfo}>Show Info</button>
    </div>
  )
}
```

## API Reference

### ToastProvider Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| children | ReactNode | - | Your application tree |
| position | 'top-right' \| 'bottom-right' \| 'top-left' \| 'bottom-left' | 'top-right' | Toast container position |
| maxToasts | number | 5 | Maximum number of visible toasts |

### Toast Hook Methods

#### showSuccess(message, duration?)
Shows a success toast (green theme)

```tsx
showSuccess('Task created successfully!')
showSuccess('Task created successfully!', 5000) // Custom 5s duration
```

#### showError(message, duration?)
Shows an error toast (red theme)

```tsx
showError('Failed to save changes')
```

#### showWarning(message, duration?)
Shows a warning toast (amber/yellow theme)

```tsx
showWarning('Your session is about to expire')
```

#### showInfo(message, duration?)
Shows an info toast (blue theme)

```tsx
showInfo('New update available')
```

## Design System Integration

The toast system uses design tokens for consistent styling:

- **Colors**: Uses semantic color tokens (success, error, warning, primary)
- **Shadows**: Applies elevation with shadow tokens
- **Spacing**: Follows 8pt grid system
- **Border Radius**: Consistent rounded corners
- **Animations**: Uses Framer Motion variants from animations library

### Color Mapping

| Toast Type | Background | Border | Icon | Text |
|------------|-----------|--------|------|------|
| Success | green-50 | green-500 | green-600 | green-900 |
| Error | red-50 | red-500 | red-600 | red-900 |
| Warning | amber-50 | amber-500 | amber-600 | amber-900 |
| Info | indigo-50 | indigo-500 | indigo-600 | indigo-900 |

## Animations

The toast system includes sophisticated animations:

### Entrance Animation
- Slides in from the right (slideInRight variant)
- Smooth opacity fade-in
- Scale effect for depth

### Exit Animation
- Slides out to the right
- Opacity fade-out
- Smooth layout repositioning

### Progress Bar
- Animated countdown showing time remaining
- Smooth linear animation
- Pauses on hover

### Stacked Toasts
- Layout animations when toasts are added/removed
- Smooth repositioning of existing toasts
- Maintains visual hierarchy

## Accessibility

The toast system follows WCAG 2.1 AA guidelines:

- **ARIA Attributes**:
  - `role="alert"`: Identifies the element as an alert
  - `aria-live="polite"`: Announces changes politely
  - `aria-atomic="true"`: Toast content is read as a whole
  - `aria-label="Close notification"`: Accessible close button label

- **Keyboard Navigation**:
  - Close button is keyboard accessible
  - Focus management with visible focus indicators

- **Color Contrast**:
  - All text meets 4.5:1 contrast ratio
  - Icon backgrounds provide sufficient contrast

## Customization

### Changing Position

```tsx
<ToastProvider position="bottom-right">
  {children}
</ToastProvider>
```

### Adjusting Maximum Toasts

```tsx
<ToastProvider maxToasts={3}>
  {children}
</ToastProvider>
```

### Custom Duration

```tsx
const { showSuccess } = useToast()

// Show for 5 seconds instead of default 3
showSuccess('Message here', 5000)
```

## Responsive Behavior

The toast container is responsive:

- **Desktop (>640px)**: Full pointer events, interactive toasts
- **Mobile (≤640px)**: Optimized touch targets, responsive positioning

Toasts adapt to screen size:
- Maximum width: 400px (container)
- Flexible message width
- Responsive icon and button sizes

## Best Practices

### When to Use Toasts

- **Success**: Confirm completed actions (save, delete, create)
- **Error**: Report failures with actionable feedback
- **Warning**: Alert users to important information
- **Info**: Provide helpful tips or updates

### Message Writing

- **Be concise**: Keep messages under 2 lines
- **Be specific**: Tell users what happened
- **Be actionable**: Include next steps when relevant
- **Use plain language**: Avoid technical jargon

### Duration Guidelines

- **Success**: 2-3 seconds
- **Info**: 3-4 seconds
- **Warning**: 4-5 seconds
- **Error**: 5-6 seconds (users need time to read)

## Examples

### Form Validation

```tsx
function handleSubmit() {
  try {
    await submitForm(data)
    showSuccess('Form submitted successfully!')
  } catch (error) {
    showError('Failed to submit form. Please check your inputs.')
  }
}
```

### API Operations

```tsx
async function deleteTask(id: string) {
  try {
    await taskApi.delete(id)
    showSuccess('Task deleted successfully!')
  } catch (error) {
    showError('Failed to delete task. Please try again.')
  }
}
```

### Session Management

```tsx
useEffect(() => {
  const warningTimer = setTimeout(() => {
    showWarning('Your session will expire in 5 minutes.')
  }, 25 * 60 * 1000)

  return () => clearTimeout(warningTimer)
}, [])
```

### Feature Announcements

```tsx
function showNewFeature() {
  showInfo('Check out our new dark mode feature!', 6000)
}
```

## Performance Considerations

- **Efficient Rendering**: Uses React.memo and useCallback for optimization
- **Animation Performance**: GPU-accelerated transforms and opacity
- **Memory Management**: Automatic cleanup of toast timers
- **Bundle Size**: Tree-shakeable imports (Framer Motion)

## Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Full support

## Migration Guide

### From Old Toast System

The new system is backward compatible. Simply update your imports:

```tsx
// Old
import { useToast } from '@/components/ui/ToastContainer'

// New (same import!)
import { useToast } from '@/components/ui/ToastContainer'

// Old methods still work
const { showSuccess, showError } = useToast()

// New methods available
const { showWarning, showInfo } = useToast()
```

## Troubleshooting

### Toasts not appearing

- Ensure ToastProvider wraps your app
- Check that you're calling toast methods within components
- Verify z-index doesn't conflict with other fixed elements

### Animations not smooth

- Check that Framer Motion is installed
- Verify browser supports CSS transforms
- Check for conflicting CSS transitions

### Progress bar not accurate

- Ensure timer isn't being cleared prematurely
- Check that hover state is working correctly

## Future Enhancements

Potential features for future versions:

- Action buttons within toasts
- Rich content (HTML formatting)
- Custom icons
- Sound effects
- Toast categories with filtering
- Persistent toast history
- Custom animation variants

## License

This component is part of your application and follows the same license.
