# Todo AI Chatbot Frontend

React/Next.js frontend for AI-powered task management using natural language.

## Features

- 💬 **Natural Language Chat**: Conversational interface for task management
- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- 🔐 **Better Auth Integration**: Secure authentication
- ⚡ **Real-time Updates**: Live typing indicators and message streaming
- 📱 **Mobile Responsive**: Optimized for all screen sizes
- 🌙 **Dark Mode**: Automatic theme detection

## Tech Stack

- **React**: 18.3.1
- **Next.js**: 15.1.3 (App Router)
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first styling
- **Better Auth**: 1.1.9 (authentication)
- **ChatKit**: @openai/chatkit (AI components)
- **React Hot Toast**: Notification system

## Quick Start

### 1. Prerequisites

```bash
# Install Node.js 18+
node --version  # Should be v18+

# Install npm
npm --version
```

### 2. Environment Setup

```bash
# Navigate to frontend
cd /home/xdev/Hackhthon-II/phase-III/frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env.local

# Edit environment variables
nano .env.local
```

### 3. Environment Variables

```bash
# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000

# Better Auth
NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
```

### 4. Start Development Server

```bash
# Development mode with hot-reload
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run type checking
npm run type-check

# Run linter
npm run lint
```

### 5. Access Application

```bash
# Open browser
open http://localhost:3000

# Or use URL
http://localhost:3000/chat
```

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── ChatInterface.tsx    # Main chat container
│   │   ├── MessageList.tsx      # Message display
│   │   ├── MessageInput.tsx     # Input form
│   │   └── TypingIndicator.tsx  # Loading animation
│   ├── hooks/           # Custom React hooks
│   │   ├── useAuth.ts            # Authentication state
│   │   └── useChat.ts            # Chat functionality
│   ├── lib/             # Libraries and configurations
│   │   ├── auth.ts              # Better Auth client
│   │   └── chatkit.ts           # ChatKit configuration
│   ├── pages/           # Next.js pages
│   │   ├── _app.tsx             # App wrapper
│   │   ├── _document.tsx        # HTML structure
│   │   ├── index.tsx            # Landing page
│   │   ├── chat.tsx             # Main chat interface
│   │   ├── signin.tsx           # Sign in/up
│   │   └── signout.tsx          # Sign out
│   ├── services/        # API services
│   │   ├── api.ts               # API client
│   │   └── chatService.ts       # Chat service
│   ├── styles/          # Global styles
│   │   └── globals.css          # Tailwind imports
│   └── types/           # TypeScript types
│       └── chat.ts             # Chat-related types
├── public/              # Static assets
├── .env.example         # Environment template
├── next.config.js       # Next.js configuration
├── tailwind.config.ts   # Tailwind configuration
└── package.json         # Dependencies
```

## Components

### ChatInterface
Main container for chat functionality. Manages chat state and integrates all sub-components.

### MessageList
Displays chat messages with:
- User/assistant distinction
- Timestamps
- Tool call indicators
- Auto-scroll to latest message
- Empty state handling

### MessageInput
Message composition with:
- Auto-resize textarea
- Send button with loading state
- Keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Character limit enforcement

### TypingIndicator
Animated loading indicator during agent processing.

## Hooks

### useAuth
```typescript
const { user, loading, isAuthenticated } = useAuth();

if (!isAuthenticated) {
  // Redirect to sign in
}
```

### useChat
```typescript
const { messages, loading, error, sendMessage } = useChat();

await sendMessage("Add a task to buy groceries");
```

## Authentication

### Better Auth Setup

Authentication is handled by Better Auth. The integration includes:

- Sign in/up
- Sign out
- Session management
- JWT token handling
- Protected routes

### Protecting Routes

```typescript
import { useAuth } from '@/hooks/useAuth';

export default function ProtectedPage() {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    router.push('/signin');
    return null;
  }
  
  // Render protected content
}
```

## ChatKit Configuration

ChatKit is configured in `src/lib/chatkit.ts`:

```typescript
import { chatKit } from '@/lib/chatkit';

const response = await chatKit.chat(userId, messages);
```

### Features
- REST adapter for backend API
- Domain allowlist for security
- Error handling with retry logic
- Timeout configuration (30s)

### Allowed Tools
- `add_task`
- `list_tasks`
- `complete_task`
- `update_task`
- `delete_task`

## Styling

### Tailwind CSS

The app uses Tailwind CSS for styling with:

- Mobile-first responsive design
- Dark mode support
- Custom color palette
- Consistent spacing

### Customization

Edit `tailwind.config.ts` to customize:
- Colors
- Spacing
- Breakpoints
- Fonts

## Troubleshooting

### Backend Connection

```bash
# Check API URL
echo $NEXT_PUBLIC_API_URL

# Test connection
curl $NEXT_PUBLIC_API_URL/health
```

### Authentication Issues

```bash
# Check Better Auth URL
echo $NEXT_PUBLIC_BETTER_AUTH_URL

# Clear session
localStorage.clear()
```

### Build Errors

```bash
# Clear Next.js cache
rm -rf .next

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Rebuild
npm run build
```

### TypeScript Errors

```bash
# Check types
npm run type-check

# Auto-fix issues
npm run lint -- --fix
```

## Development

### Adding New Components

1. Create component in `src/components/`
2. Use TypeScript with proper types
3. Add Tailwind classes for styling
4. Export from `src/components/index.ts`

### Adding New Pages

1. Create page in `src/pages/`
2. Wrap in Layout component if needed
3. Add authentication protection
4. Update navigation

### Testing Locally

```bash
# Run development server
npm run dev

# Open browser
http://localhost:3000

# Test different screen sizes
# - Desktop: 1920x1080
# - Tablet: 768x1024
# - Mobile: 375x667
```

## Deployment

### Production Build

```bash
# Build optimized bundle
npm run build

# Test production build locally
npm start

# Deploy to Vercel
vercel --prod
```

### Environment Variables

Set these in your hosting platform:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_BETTER_AUTH_URL=https://yourdomain.com
```

### Performance Optimization

- Static pages pre-rendered
- Images optimized
- CSS minified
- JavaScript bundled
- CDN configured

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile Safari: iOS 14+

## Contributing

1. Follow React best practices
2. Use TypeScript for type safety
3. Write component tests
4. Follow linting rules
5. Test on multiple devices

## License

MIT

## Support

For issues and questions:
- Check component documentation
- Review examples in code
- Open an issue on GitHub
