# ERP SOLUTION Business Intelligence Dashboard v3.2

## Overview
Executive-level business intelligence dashboard for the ERP SOLUTION platform. Real-time KPIs, revenue analytics, AI-powered forecasting, inventory insights, and activity feeds.

## Features

### 📊 Executive Summary
- Revenue, invoices, customers, products overview cards
- Period comparison (vs previous period / previous year)
- Real-time data refresh every 5 minutes

### 📈 KPI Metrics
- Revenue achievement with progress bars
- Profit margin tracking
- Customer acquisition rate
- Inventory turnover ratio
- Average order value
- Collection period (DSO)

### 📉 Charts & Visualizations
- **Line Charts**: Revenue trends, sales forecasts, customer acquisition
- **Bar Charts**: Inventory value by category, revenue by product
- **Pie Charts**: Stock status distribution (active/low/out)
- **AI Forecast**: Predicted sales with confidence intervals

### 🤖 AI Insights Panel
- Trend detection and anomaly alerts
- Business opportunities identification
- Risk warnings with severity levels
- Actionable recommendations

### 🏆 Top Performers
- Top selling products with images
- Top customers by revenue
- Rankings with trend indicators

### 📋 Activity Feed
- Real-time business activity stream
- Invoice events, payments, orders, stock alerts
- User attribution and timestamps

### 🔍 Detail Screens
- **Revenue Detail**: Daily breakdown, category analysis, data tables
- **Inventory Detail**: Stock anomalies, category breakdown, low stock alerts

## Architecture

```
erp_solution-bi-dashboard/
├── components/
│   ├── charts/
│   │   ├── LineChartCard.tsx      # Reusable line chart wrapper
│   │   ├── BarChartCard.tsx       # Reusable bar chart wrapper
│   │   └── PieChartCard.tsx       # Reusable pie chart wrapper
│   ├── kpi/
│   │   ├── KPICard.tsx            # KPI metric card with progress
│   │   └── SummaryCards.tsx       # Executive summary row
│   ├── filters/
│   │   └── PeriodFilter.tsx       # Period selector & compare options
│   ├── ActivityFeed.tsx           # Real-time activity stream
│   ├── TopLists.tsx               # Top products & customers
│   └── AIInsightsPanel.tsx        # AI-powered insights display
├── screens/
│   ├── DashboardScreen.tsx        # Main BI dashboard
│   ├── RevenueDetailScreen.tsx    # Revenue analytics detail
│   └── InventoryDetailScreen.tsx  # Inventory analytics detail
├── hooks/
│   └── useDashboard.ts            # Data fetching hooks (14 endpoints)
├── types/
│   └── dashboard.ts               # TypeScript interfaces
├── utils/
│   └── dashboard.ts               # Formatting & utilities
├── constants/
│   └── dashboard.ts               # Colors, icons, periods config
├── locales/
│   ├── en/dashboard.json          # English translations
│   └── my/dashboard.json          # Burmese translations
└── DashboardNavigator.tsx         # Stack navigation setup
```

## API Integration

Consumes 14 API endpoints from the ERP SOLUTION OpenAPI spec:

| Hook | Endpoint | Purpose |
|------|----------|---------|
| `useDashboardSummary` | GET /dashboard/summary | Executive overview |
| `useRevenueAnalytics` | GET /dashboard/revenue | Revenue trends |
| `useKPIMetrics` | GET /dashboard/kpis | KPI targets & achievement |
| `useSalesChart` | GET /dashboard/charts/sales | Sales line chart |
| `useInventoryChart` | GET /dashboard/charts/inventory | Inventory bar chart |
| `useCustomerChart` | GET /dashboard/charts/customers | Customer acquisition |
| `useActivities` | GET /dashboard/activities | Activity feed |
| `useTopProducts` | GET /dashboard/top-products | Best sellers |
| `useTopCustomers` | GET /dashboard/top-customers | Top revenue customers |
| `useSalesForecast` | GET /ai/forecast | AI sales prediction |
| `useAIInsights` | GET /ai/insights | AI business insights |
| `useInventoryStats` | GET /inventory/stats | Inventory overview |
| `useAnomalyDetection` | GET /ai/anomaly-detection | Anomaly alerts |

## Dependencies

```json
{
  "react-native-chart-kit": "^6.12.0",
  "react-native-svg": "^13.9.0",
  "react-native-paper": "^5.10.0",
  "@react-navigation/stack": "^6.3.0",
  "react-i18next": "^13.0.0",
  "react-native-safe-area-context": "^4.7.0"
}
```

## Installation

1. Install dependencies:
```bash
npm install react-native-chart-kit react-native-svg
```

2. Add to your navigation:
```tsx
import { DashboardNavigator } from './bi-dashboard/DashboardNavigator';

// In your main navigator:
<Drawer.Screen name="Dashboard" component={DashboardNavigator} />
```

3. Add translations to i18n config:
```tsx
import dashboardEN from './bi-dashboard/locales/en/dashboard.json';
import dashboardMY from './bi-dashboard/locales/my/dashboard.json';

i18n.addResourceBundle('en', 'dashboard', dashboardEN);
i18n.addResourceBundle('my', 'dashboard', dashboardMY);
```

## Usage

```tsx
import { DashboardScreen } from './bi-dashboard/screens/DashboardScreen';

// The dashboard is self-contained with all data fetching,
// filtering, and refresh logic built-in.
```

## Customization

### Adding New KPIs
Edit `constants/dashboard.ts` and add to `KPI_ICONS`:
```ts
export const KPI_ICONS = {
  ...existing,
  newMetric: 'new-icon-name',
};
```

### Custom Chart Colors
Modify `CHART_COLORS` in constants:
```ts
export const CHART_COLORS = {
  ...existing,
  custom: '#FF5722',
};
```

### Period Options
Edit `DASHBOARD_PERIODS` in constants to add/remove periods.

## Performance

- Automatic data refresh every 5 minutes
- AbortController for request cancellation
- Skeleton loaders for all components
- Lazy loading of detail screens
- Image caching for product thumbnails

## Accessibility

- All charts have text alternatives
- Screen reader support for KPI cards
- High contrast mode support
- Touch targets minimum 44x44dp

## License
Proprietary - ERP SOLUTION v3.2

