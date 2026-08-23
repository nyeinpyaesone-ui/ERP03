# ERP SOLUTION Mobile App v2.5

**React Native Mobile App** for ERP SOLUTION System

---

## Features

### Screens
| Screen | Features |
|--------|----------|
| **Login** | Email/password auth, secure storage, biometric ready |
| **Dashboard** | KPI cards, revenue chart, pipeline progress, activity feed |
| **Contacts** | Search, filter, call button, status badges, FAB add |
| **Invoices** | Segmented filter (All/Paid/Pending/Overdue), amount display |
| **Search** | Full-text search, facet filters, recent searches, entity icons |
| **AI Copilot** | Chat interface, streaming simulation, suggestion chips |
| **Inventory** | Stock levels, reorder alerts, progress bars |
| **Profile** | User info, stats, settings, dark mode toggle, logout |

### Technical Stack
- **React Native** 0.73 with Expo SDK 50
- **TypeScript** for type safety
- **React Navigation** (Stack + Bottom Tabs)
- **React Native Paper** for Material Design components
- **TanStack Query** for server state management
- **Zustand** for client state (auth, theme)
- **React Native Chart Kit** for charts
- **Axios** for API calls
- **Expo Secure Store** for token storage
- **Expo Local Authentication** for biometric auth (ready)
- **Expo Notifications** for push notifications (ready)
- **Expo Camera** for document scanning (ready)

### Design System
- Light/Dark theme support
- Myanmar font stack ready (Pyidaungsu, Noto Sans Myanmar)
- Consistent with v2.2 UI/UX Pro Max design tokens
- Responsive layouts for phones and tablets

---

## Quick Start

```bash
# Install dependencies
npm install

# Start Expo development server
npx expo start

# Run on iOS simulator
i

# Run on Android emulator
a

# Run on web
w
```

---

## API Integration

Update `src/utils/api.ts` with your backend URL:

```typescript
const API_BASE_URL = 'https://your-api-domain.com/api/v1';
// or for local development:
// const API_BASE_URL = 'http://localhost:8000/api/v1';
```

All API endpoints from v2.4 are supported:
- `/api/v1/erp/*` — Core ERP (contacts, invoices, products)
- `/api/v1/search/*` — Full-text search
- `/api/v1/knowledge/*` — Knowledge system
- `/api/v1/core/*` — Accounting, CRM, Inventory, Purchasing
- `/api/v1/myanmar/*` — Myanmar translation & validation

---

## File Structure

```
erp_solution-mobile-app/
├── App.tsx                          # Root component
├── package.json                     # Dependencies
├── tsconfig.json                    # TypeScript config
├── src/
│   ├── navigation/
│   │   └── AppNavigator.tsx          # Stack + Tab navigation
│   ├── screens/
│   │   ├── LoginScreen.tsx          # Authentication
│   │   ├── DashboardScreen.tsx      # Home dashboard
│   │   ├── ContactsScreen.tsx       # Contact list
│   │   ├── InvoicesScreen.tsx       # Invoice list
│   │   ├── SearchScreen.tsx         # Global search
│   │   ├── AICopilotScreen.tsx      # AI chat
│   │   ├── InventoryScreen.tsx      # Stock levels
│   │   └── ProfileScreen.tsx        # Settings & profile
│   ├── store/
│   │   ├── authStore.ts             # Auth state (Zustand)
│   │   └── themeStore.ts            # Theme state (Zustand)
│   └── utils/
│       ├── theme.ts                 # Design tokens
│       └── api.ts                   # API client
└── README.md
```

---

## Build History

| Version | Feature | Files |
|---------|---------|-------|
| v2.4 | Core ERP Modules | 205 |
| **v2.5** | **Mobile App (React Native)** | **215** |

---

## Remaining Roadmap

| Priority | Feature |
|----------|---------|
| P2 | Multi-language i18n |
| P3 | Kubernetes Deployment |
| P3 | Manufacturing / MRP |
| P3 | Payroll / HR |
| P3 | Retail POS |
| P3 | E-commerce Storefront |

