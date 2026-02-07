# Todo Frontend

A modern, responsive task management application built with Next.js 16, TypeScript, and Tailwind CSS.

## Features

- **User Authentication**: Secure sign up and sign in with Better Auth
- **Task Management**: Create, read, update, and delete tasks
- **Real-time Updates**: Immediate UI feedback for all actions
- **Toast Notifications**: Success and error messages for user actions
- **Responsive Design**: Mobile-first approach that works on all screen sizes (320px+)
- **Accessibility**: WCAG AA compliant with keyboard navigation and screen reader support
- **Error Handling**: Global error boundary for graceful error recovery
- **Loading States**: Visual feedback for all async operations

## Prerequisites

- **Node.js**: 18.0.0 or higher
- **npm**: 8.0.0 or higher (comes with Node.js)

## Installation

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:

   Create a `.env.local` file in the frontend directory:

   ```bash
   touch .env.local
   ```

   Add the following environment variables:

   ```env
   # Backend API URL
   NEXT_PUBLIC_API_URL=http://localhost:8000

   # Better Auth Configuration
   NEXT_PUBLIC_AUTH_URL=http://localhost:3000
   NEXT_PUBLIC BETTER_AUTH_URL=http://localhost:8000/auth
   ```

   Replace the URLs with your actual backend and frontend URLs.

## Running the Application

### Development Mode

Start the development server with hot reload:

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### Production Build

Build the application for production:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

### Linting

Run the linter to check for code issues:

```bash
npm run lint
```

### Formatting

Format code with Prettier:

```bash
npm run format
```

Check formatting without making changes:

```bash
npm run format:check
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Authentication pages (login, signup)
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── signup/
│   │   │       └── page.tsx
│   │   ├── dashboard/         # Main dashboard page
│   │   │   └── page.tsx
│   │   ├── layout.tsx         # Root layout with error boundary
│   │   ├── page.tsx           # Home/landing page
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── auth/              # Authentication components
│   │   │   ├── LoginForm.tsx
│   │   │   └── SignupForm.tsx
│   │   ├── task/              # Task-related components
│   │   │   ├── ConfirmDeleteDialog.tsx
│   │   │   ├── CreateTaskForm.tsx
│   │   │   ├── EditTaskModal.tsx
│   │   │   ├── TaskItem.tsx
│   │   │   └── TaskList.tsx
│   │   ├── ui/                # UI components
│   │   │   ├── Toast.tsx
│   │   │   └── ToastContainer.tsx
│   │   └── ErrorBoundary.tsx  # Global error boundary
│   ├── lib/                   # Utility libraries
│   │   ├── api.ts             # Central API client
│   │   └── auth.ts            # Better Auth configuration
│   └── types/                 # TypeScript type definitions
│       └── task.ts            # Task-related types
├── public/                    # Static assets
├── .env.local                 # Environment variables (create this)
├── next.config.ts             # Next.js configuration
├── tailwind.config.ts         # Tailwind CSS configuration
├── tsconfig.json              # TypeScript configuration
└── package.json               # Dependencies and scripts
```

## Component Overview

### Authentication Components

#### `LoginForm`
- User sign-in form with email/password
- Form validation and error handling
- Redirects to dashboard on success
- Located at `/login`

#### `SignupForm`
- User registration form with name/email/password
- Client-side validation
- Error display for registration failures
- Located at `/signup`

### Task Components

#### `CreateTaskForm`
- Form to create new tasks
- Title (required) and description (optional) fields
- Character counters for validation
- Loading state during submission
- Success/error toast notifications

#### `TaskList`
- Displays list of tasks with loading and empty states
- Shows task count and completion statistics
- Responsive layout for mobile and desktop

#### `TaskItem`
- Individual task display component
- Checkbox to toggle completion status
- Edit and delete action buttons
- Visual indication of completed tasks
- Relative date formatting (e.g., "2 hours ago")

#### `EditTaskModal`
- Modal dialog for editing tasks
- Pre-filled form with existing task data
- Loading state during save
- ESC key and backdrop click to close
- Touch-friendly buttons on mobile

#### `ConfirmDeleteDialog`
- Confirmation dialog before task deletion
- Warning message with task title
- Loading state during deletion
- Keyboard and mouse accessibility

### UI Components

#### `Toast` & `ToastContainer`
- Toast notification system for success/error messages
- Auto-dismiss after 3 seconds
- Manual dismiss capability
- Smooth animations
- Context-based API via `useToast()` hook

#### `ErrorBoundary`
- Global error boundary for React component errors
- User-friendly error messages
- Error details in development mode
- "Try Again" button to reload
- Prevents white screen of death

## Development Guidelines

### Code Style

- **TypeScript**: All components must use TypeScript with proper type definitions
- **Client Components**: Use `'use client'` directive for components with interactivity
- **Server Components**: Default to server components when no client-side features needed
- **Naming**: Use PascalCase for components, camelCase for functions and variables

### Styling

- **Tailwind CSS**: Use Tailwind utility classes for all styling
- **Responsive Design**: Mobile-first approach with `sm:`, `md:`, `lg:` breakpoints
- **Color Palette**: Use semantic color names (blue for primary, red for danger, green for success)
- **Spacing**: Use Tailwind's spacing scale (2, 4, 8, 12, 16, etc.)

### Accessibility

- **Keyboard Navigation**: All interactive elements must be keyboard accessible
- **ARIA Labels**: Add appropriate `aria-label` attributes to buttons and controls
- **Focus Indicators**: Ensure visible focus states for all interactive elements
- **Touch Targets**: Minimum 44x44px for touch-friendly buttons on mobile
- **Color Contrast**: Meet WCAG AA standards for text and background colors

### API Integration

- **Central API Client**: Always use the `api` client from `@/lib/api`
- **Error Handling**: Handle API errors with try-catch blocks
- **Loading States**: Show loading indicators during async operations
- **Toast Notifications**: Provide feedback for success/error actions

### Best Practices

1. **Component Size**: Keep components focused and under 300 lines
2. **Props Interface**: Define explicit interfaces for component props
3. **Callbacks**: Use `useCallback` for event handlers passed to child components
4. **State Management**: Use local state with `useState` for component-specific data
5. **Form Validation**: Validate on both client and server side
6. **Error Messages**: Provide clear, actionable error messages

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_AUTH_URL` | Frontend URL for auth callbacks | `http://localhost:3000` |
| `NEXT_PUBLIC_BETTER_AUTH_URL` | Better Auth backend URL | `http://localhost:8000/auth` |

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Responsive Breakpoints

- **Mobile**: < 640px (default)
- **Tablet**: 640px - 1024px (`sm:`, `md:`)
- **Desktop**: > 1024px (`lg:`, `xl:`)

Minimum supported screen width: 320px

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
# Kill process on port 3000
npx kill-port 3000

# Or use a different port
npm run dev -- -p 3001
```

### Module Not Found Errors

If you encounter module not found errors:

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Build Errors

If the production build fails:

```bash
# Clear Next.js cache
rm -rf .next

# Rebuild
npm run build
```

## Contributing

When contributing to this frontend:

1. Follow the existing code style and structure
2. Add TypeScript types for all new components and functions
3. Ensure responsive design for mobile and desktop
4. Test keyboard navigation and accessibility
5. Add loading states for async operations
6. Provide user feedback with toast notifications
7. Run linting and formatting before committing

## License

This project is part of the Todo Application Hackathon project.
