import { useState, useEffect, useCallback, useRef } from 'react';
import {
  DashboardSummary,
  RevenueAnalytics,
  KPIMetrics,
  ChartData,
  ActivityItem,
  TopProduct,
  TopCustomer,
  DashboardFilter,
  ForecastData,
  AIInsight,
  InventoryStats,
} from '../types/dashboard';

const API_BASE = 'https://api.erp_solution.com/v1';

const useApi = <T>(endpoint: string, params?: Record<string, string>) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);

    try {
      const queryParams = params ? new URLSearchParams(params).toString() : '';
      const url = `${API_BASE}${endpoint}${queryParams ? `?${queryParams}` : ''}`;

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${getToken()}`,
          'Content-Type': 'application/json',
        },
        signal: abortRef.current.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const result = await response.json();
      setData(result);
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }, [endpoint, JSON.stringify(params)]);

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

const getToken = (): string => {
  // Replace with your actual token retrieval logic
  return (globalThis as any).__ERP_TOKEN__ || '';
};

export const useDashboardSummary = (filter: DashboardFilter) => {
  return useApi<DashboardSummary>('/dashboard/summary', {
    period: filter.period,
    compareWith: filter.compareWith,
  });
};

export const useRevenueAnalytics = (period: string) => {
  return useApi<RevenueAnalytics>('/dashboard/revenue', {
    period,
    groupBy: 'daily',
  });
};

export const useKPIMetrics = (period: string) => {
  return useApi<KPIMetrics>('/dashboard/kpis', { period });
};

export const useSalesChart = (period: string = '30d') => {
  return useApi<ChartData>('/dashboard/charts/sales', { period });
};

export const useInventoryChart = () => {
  return useApi<ChartData>('/dashboard/charts/inventory');
};

export const useCustomerChart = (period: string = '30d') => {
  return useApi<ChartData>('/dashboard/charts/customers', { period });
};

export const useActivities = (limit: number = 20, type: string = 'all') => {
  return useApi<ActivityItem[]>('/dashboard/activities', {
    limit: String(limit),
    type,
  });
};

export const useTopProducts = (period: string = 'this_month', limit: number = 10) => {
  return useApi<TopProduct[]>('/dashboard/top-products', {
    period,
    limit: String(limit),
  });
};

export const useTopCustomers = (period: string = 'this_month', limit: number = 10) => {
  return useApi<TopCustomer[]>('/dashboard/top-customers', {
    period,
    limit: String(limit),
  });
};

export const useSalesForecast = (horizon: string = '30d') => {
  return useApi<ForecastData>('/ai/forecast', {
    type: 'sales',
    horizon,
  });
};

export const useAIInsights = (limit: number = 5) => {
  return useApi<AIInsight[]>('/ai/insights', {
    type: 'all',
    limit: String(limit),
  });
};

export const useInventoryStats = () => {
  return useApi<InventoryStats>('/inventory/stats');
};

export const useAnomalyDetection = () => {
  return useApi<Array<{ id: string; module: string; metric: string; severity: string; description: string }>>(
    '/ai/anomaly-detection',
    { module: 'all', sensitivity: 'medium' }
  );
};

export const useDashboardRefresh = (interval: number = 300000) => {
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setLastRefresh(new Date());
    }, interval);

    return () => clearInterval(timer);
  }, [interval]);

  return lastRefresh;
};

export const usePeriodFilter = () => {
  const [filter, setFilter] = useState<DashboardFilter>({
    period: 'this_month',
    compareWith: 'previous_period',
  });

  const setPeriod = useCallback((period: string) => {
    setFilter(prev => ({ ...prev, period }));
  }, []);

  const setCompareWith = useCallback((compareWith: 'previous_period' | 'previous_year') => {
    setFilter(prev => ({ ...prev, compareWith }));
  }, []);

  return { filter, setPeriod, setCompareWith, setFilter };
};

---


# merged-converted (2)-converted.md

# useLanguage (1)-converted.md

import { useTranslation } from 'react-i18next';
import { useCallback } from 'react';

export const useLanguage = () => {
  const { i18n, t } = useTranslation();

  const isMyanmar = i18n.language === 'my';
  const isRTL = false; // Myanmar is LTR

  const getFontFamily = useCallback(() => {
    if (isMyanmar) {
      return {
        regular: 'Pyidaungsu',
        medium: 'Pyidaungsu',
        bold: 'Pyidaungsu',
      };
    }
    return {
      regular: 'Roboto',
      medium: 'Roboto-Medium',
      bold: 'Roboto-Bold',
    };
  }, [isMyanmar]);

  const formatCurrency = useCallback((amount: number) => {
    const formatted = new Intl.NumberFormat(isMyanmar ? 'my-MM' : 'en-US').format(amount);
    return isMyanmar ? `${formatted} ${t('common.currency')}` : `${t('common.currency')} ${formatted}`;
  }, [isMyanmar, t]);

  const formatDate = useCallback((date: Date | string) => {
    const d = new Date(date);
    if (isMyanmar) {
      return d.toLocaleDateString('my-MM', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
    }
    return d.toLocaleDateString('en-US', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  }, [isMyanmar]);

  return {
    language: i18n.language,
    isMyanmar,
    isRTL,
    getFontFamily,
    formatCurrency,
    formatDate,
    changeLanguage: i18n.changeLanguage,
    t,
  };
};

---

# README-i18n (1)-converted.md

# ERP SOLUTION i18n Framework (v2.6 P2)

## Installation

```bash
npm install i18next react-i18next expo-localization react-native-async-storage/async-storage
npm install -D @types/react-native-async-storage
```

## Setup

1. **Copy files to your project:**
   - `src/i18n/` → your `src/i18n/`
   - `src/components/LanguageSwitcher.tsx` → your `src/components/`
   - `src/hooks/useLanguage.ts` → your `src/hooks/`

2. **Initialize i18n in App.tsx:**
   Add `import './src/i18n';` at the top of your App.tsx (before any component imports).

3. **Add font loading for Myanmar:**
   In your `app.json` or `app.config.js`:
   ```json
   {
     "expo": {
       "fonts": [
         {
           "asset": "./assets/fonts/Pyidaungsu-Regular.ttf",
           "family": "Pyidaungsu"
         }
       ]
     }
   }
   ```

## Usage

### In Components
```tsx
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();

<Text>{t('dashboard.title')}</Text>
<Text>{t('dashboard.greeting', { timeOfDay: 'morning', name: 'Aung' })}</Text>
```

### With Interpolation
```tsx
<Text>{t('invoices.overdueAlert', { count: 3 })}</Text>
// Output: "3 invoice(s) overdue" (EN) / "သက်တမ်းကျော် ငွေတောင်းခံလွှာ ၃ စောင်" (MY)
```

### Language Switching
```tsx
import { LanguageSwitcher } from './components/LanguageSwitcher';

// In your Profile/Settings screen:
<LanguageSwitcher />
```

### Currency & Date Formatting
```tsx
import { useLanguage } from './hooks/useLanguage';

const { formatCurrency, formatDate, isMyanmar } = useLanguage();

<Text>{formatCurrency(500000)}</Text>  // "MMK 500,000" or "၅၀၀,၀၀၀ ကျပ်"
<Text>{formatDate(new Date())}</Text>    // Localized date
```

## Adding New Languages

1. Create `src/i18n/locales/[lang-code].json`
2. Import in `src/i18n/index.ts`:
   ```ts
   import fr from './locales/fr.json';
   ```
3. Add to resources:
   ```ts
   const resources = {
     en: { translation: en },
     my: { translation: my },
     fr: { translation: fr },
   };
   ```
4. Add to `LanguageSwitcher` component's `LANGUAGES` array.

## Translation Coverage Check

Run this script to find missing keys:
```bash
node scripts/check-i18n-coverage.js
```

## Key Extraction (Future)

When ready for CI/CD, set up `i18next-parser`:
```bash
npm install -D i18next-parser
```
Add to package.json:
```json
"i18n:extract": "i18next 'src/**/*.{ts,tsx}' -c i18next-parser.config.js"
```

---

# my (1)-converted.md

{
  "common": {
    "appName": "ERP SOLUTION",
    "loading": "ဖွင့်နေသည်...",
    "retry": "ပြန်လည်ကြိုးစားမည်",
    "cancel": "ပယ်ဖျက်မည်",
    "save": "သိမ်းဆည်းမည်",
    "delete": "ဖျက်မည်",
    "edit": "ပြင်ဆင်မည်",
    "create": "ဖန်တီးမည်",
    "search": "ရှာဖွေမည်",
    "filter": "စစ်ထုတ်မည်",
    "all": "အားလုံး",
    "active": "လှုပ်ရှားနေသော",
    "inactive": "အသုံးမပြုသော",
    "pending": "စောင့်ဆိုင်းနေသော",
    "paid": "ပေးဆောင်ပြီးသော",
    "overdue": "သက်တမ်းကျော်နေသော",
    "success": "အောင်မြင်ပါသည်",
    "error": "အမှား",
    "confirm": "အတည်ပြုမည်",
    "back": "နောက်သို့",
    "next": "ရှေ့သို့",
    "done": "ပြီးပါပြီ",
    "close": "ပိတ်မည်",
    "noResults": "ရလဒ်မတွေ့ပါ",
    "pullToRefresh": "စ်ပြန်လည်ရယူရန် ဆွဲချပါ",
    "offline": "အင်တာနက်မရှိပါ",
    "online": "အင်တာနက်ပြန်လည်ရှိပါပြီ",
    "currency": "ကျပ်",
    "dateFormat": "DD/MM/YYYY",
    "timeFormat": "hh:mm A"
  },
  "auth": {
    "loginTitle": "ကြိုဆိုပါသည်",
    "loginSubtitle": "ERP SOLUTION အကောင့်သို့ ဝင်ရောက်ပါ",
    "email": "အီးမေးလ်",
    "emailPlaceholder": "အီးမေးလ်ထည့်ပါ",
    "password": "စကားဝှက်",
    "passwordPlaceholder": "စကားဝှက်ထည့်ပါ",
    "signIn": "ဝင်ရောက်မည်",
    "signingIn": "ဝင်ရောက်နေသည်...",
    "forgotPassword": "စကားဝှက်မေ့နေပါသလား?",
    "forgotPasswordTitle": "စကားဝှက်ပြန်လည်သတ်မှတ်မည်",
    "forgotPasswordSubtitle": "အီးမေးလ်ထည့်ပါ၊ လမ်းညွှန်ချက်များပို့ပေးပါမည်",
    "sendResetLink": "လင့်ပို့ပေးမည်",
    "resetLinkSent": "သင့်အီးမေးလ်သို့ လင့်ပို့ပြီးပါပြီ",
    "biometricPrompt": "ဇီဝမှတ်တမ်းဖြင့် ဝင်ရောက်မည်",
    "biometricError": "ဇီဝမှတ်တမ်းဝင်ရောက်ခြင်း မအောင်မြင်ပါ",
    "invalidCredentials": "အီးမေးလ် သို့မဟုတ် စကားဝှက်မမှန်ပါ",
    "sessionExpired": "အကောင့်သက်တမ်းကုန်ပါပြီ။ ပြန်လည်ဝင်ရောက်ပါ။",
    "logout": "ထွက်မည်",
    "logoutConfirm": "အကောင့်မှ ထွက်ရန် သေချာပါသလား?"
  },
  "dashboard": {
    "title": "ဒက်ရှ်ဘုတ်",
    "greeting": "{{timeOfDay}}မှာ မင်္ဂလာပါ၊ {{name}}",
    "morning": "မနက်ခင်း",
    "afternoon": "နေ့လယ်",
    "evening": "ညနေ",
    "kpi": {
      "revenue": "စုစုပေါင်းဝင်ငွေ",
      "sales": "စုစုပေါင်းရောင်းချမှု",
      "customers": "လှုပ်ရှားနေသော ဖောက်သည်များ",
      "invoices": "စောင့်ဆိုင်းနေသော ငွေတောင်းခံလွှာများ",
      "vsLastMonth": "ပြီးခဲ့သည့်လနှင့် နှိုင်းယှဉ်"
    },
    "charts": {
      "revenueTrend": "ဝင်ငွေအလျား",
      "thisMonth": "ယခုလ",
      "lastMonth": "ပြီးခဲ့သည့်လ"
    },
    "pipeline": {
      "title": "ရောင်းချမှု လမ်းကြောင်း",
      "lead": "ဦးစီးမှု",
      "qualified": "အရည်အချင်းပြည့်မီ",
      "proposal": "အဆိုပြုချက်",
      "negotiation": "ဆွေးနွေးမှု",
      "closed": "အောင်မြင်စွာ ပြီးစီး"
    },
    "recentActivity": {
      "title": "လတ်တလော လှုပ်ရှားမှုများ",
      "invoiceCreated": "{{customer}} အတွက် ငွေတောင်းခံလွှာ #{{number}} ဖန်တီးပြီးပါပြီ",
      "paymentReceived": "{{customer}} ထံမှ {{amount}} ဝင်ငွေရရှိပြီးပါပြီ",
      "contactAdded": "ဆက်သွယ်ရန် အသစ်ထည့်ပြီးပါပြီ - {{name}}",
      "stockUpdated": "{{product}} အတွက် စတော့စ်ပြင်ဆင်ပြီးပါပြီ"
    }
  },
  "contacts": {
    "title": "ဆက်သွယ်ရန်များ",
    "searchPlaceholder": "ဆက်သွယ်ရန်များ ရှာဖွေပါ...",
    "addContact": "ဆက်သွယ်ရန်ထည့်မည်",
    "contactTypes": {
      "customer": "ဖောက်သည်",
      "supplier": "ပေးသွင်းသူ",
      "vendor": "ရောင်းချသူ",
      "employee": "ဝန်ထမ်း"
    },
    "fields": {
      "name": "အမည်",
      "phone": "ဖုန်းနံပါတ်",
      "email": "အီးမေးလ်",
      "company": "ကုမ္ပဏီ",
      "type": "အမျိုးအစား",
      "status": "အခြေအနေ",
      "address": "လိပ်စာ"
    },
    "actions": {
      "call": "ခေါ်ဆိုမည်",
      "email": "အီးမေးလ်ပို့မည်",
      "message": "မက်ဆေ့ချ်ပို့မည်",
      "viewProfile": "ပရိုဖိုင်ကြည့်မည်"
    },
    "emptyState": "ဆက်သွယ်ရန်မရှိသေးပါ။ + နှိပ်ပြီး ပထမဆုံးထည့်ပါ။"
  },
  "invoices": {
    "title": "ငွေတောင်းခံလွှာများ",
    "addInvoice": "ငွေတောင်းခံလွှာထည့်မည်",
    "filters": {
      "all": "ငွေတောင်းခံလွှာအားလုံး",
      "paid": "ပေးဆောင်ပြီးသော",
      "pending": "စောင့်ဆိုင်းနေသော",
      "overdue": "သက်တမ်းကျော်နေသော"
    },
    "fields": {
      "invoiceNumber": "ငွေတောင်းခံလွှာနံပါတ်",
      "customer": "ဖောက်သည်",
      "amount": "ငွေပမာဏ",
      "dueDate": "ပေးဆောင်ရန်နေ့",
      "status": "အခြေအနေ",
      "items": "ပစ္စည်းများ",
      "subtotal": "အစီရင်ခံ",
      "tax": "အခွန်",
      "total": "စုစုပေါင်း",
      "notes": "မှတ်ချက်များ"
    },
    "overdueAlert": "သက်တမ်းကျော် ငွေတောင်းခံလွှာ {{count}} စောင်",
    "createSuccess": "ငွေတောင်းခံလွှာဖန်တီးပြီးပါပြီ",
    "deleteConfirm": "ငွေတောင်းခံလွှာ {{number}} ဖျက်မည်လား? ဤလုပ်ဆောင်ချက်ကို ပြန်လည်ရုပ်သိမ်းမရပါ။",
    "emptyState": "ငွေတောင်းခံလွှာမရှိပါ။ ပထမဆုံးဖန်တီးပါ။"
  },
  "search": {
    "title": "ရှာဖွေမှု",
    "placeholder": "မှတ်တမ်းအားလုံးမှ ရှာဖွေပါ...",
    "recentSearches": "လတ်တလော ရှာဖွေမှုများ",
    "clearHistory": "မှတ်တမ်းရှင်းလင်းမည်",
    "entities": {
      "contacts": "ဆက်သွယ်ရန်များ",
      "invoices": "ငွေတောင်းခံလွှာများ",
      "products": "ပစ္စည်းများ",
      "inventory": "စတော့",
      "transactions": "ငွေကြောင်းများ"
    },
    "results": {
      "contacts": "ဆက်သွယ်ရန် {{count}} ဦး တွေ့ပါသည်",
      "invoices": "ငွေတောင်းခံလွှာ {{count}} စောင် တွေ့ပါသည်",
      "products": "ပစ္စည်း {{count}} ခု တွေ့ပါသည်"
    }
  },
  "aiCopilot": {
    "title": "AI ကူညီသူ",
    "status": {
      "online": "အွန်လိုင်း",
      "offline": "အွန်လိုင်းမရှိ",
      "thinking": "စဉ်းစားနေသည်..."
    },
    "placeholder": "သင့်စီးပွားရေးအကြောင်း မေးခွန်းမေးပါ...",
    "suggestions": {
      "revenue": "ယခုလ ဝင်ငွေဘယ်လောက်လဲ?",
      "overdue": "သက်တမ်းကျော် ငွေတောင်းခံလွှာများ ပြပါ",
      "stock": "စတော့နည်းနေသော ပစ္စည်းများရှိလား?",
      "customer": "အကောင်းဆုံး ဖောက်သည်များဘယ်သူတွေလဲ?"
    },
    "actions": {
      "send": "ပို့မည်",
      "voice": "အသံထွက်ဖြင့်မေးမည်",
      "attach": "ဖိုင်ထည့်မည်",
      "clear": "စကားဝိုင်းရှင်းလင်းမည်"
    },
    "responses": {
      "revenue": "ယခုလ ဝင်ငွေမှာ {{amount}} ဖြစ်ပြီး ပြီးခဲ့သည့်လထက် {{percentage}}% တိုးတက်ပါသည်။",
      "overdue": "သက်တမ်းကျော် ငွေတောင်းခံလွှာ {{count}} စောင် ရှိပြီး စုစုပေါင်း {{amount}} ဖြစ်ပါသည်။",
      "stock": "စတော့နည်းနေသော ပစ္စည်း {{count}} ခု ရှိပါသည် - {{items}}။",
      "greeting": "မင်္ဂလာပါ! ကျွန်ုပ်သည် သင့်ကူညီသူ ဖြစ်ပါသည်။ ဘယ်လိုကူညီရမလဲ?"
    }
  },
  "inventory": {
    "title": "စတော့",
    "stockCard": {
      "onHand": "လက်ရှိစတော့",
      "reserved": "ဘွတ်ကင်ထားသော",
      "available": "ရရှိနိုင်သော",
      "reorderLevel": "မှာယူရမည့်အဆင့်",
      "reorderPoint": "မှာယူမှတ်တိုင်"
    },
    "status": {
      "inStock": "စတော့ရှိသည်",
      "lowStock": "စတော့နည်းနေသည်",
      "outOfStock": "စတော့ကုန်နေသည်",
      "discontinued": "ရပ်ဆိုင်းထားသည်"
    },
    "actions": {
      "adjustStock": "စတော့ပြင်ဆင်မည်",
      "viewHistory": "မှတ်တမ်းကြည့်မည်",
      "setReorderPoint": "မှာယူမှတ်တိုင်းသတ်မှတ်မည်"
    },
    "metrics": {
      "totalItems": "စတော့ပစ္စည်းစုစုပေါင်း",
      "lowStockItems": "စတော့နည်းနေသော ပစ္စည်းများ",
      "totalValue": "စတော့တန်ဖိုးစုစုပေါင်း"
    },
    "emptyState": "စတော့ပစ္စည်းမရှိသေးပါ။ စတော့ထိန်းသိမ်းရန် ပစ္စည်းထည့်ပါ။"
  },
  "profile": {
    "title": "ပရိုဖိုင်",
    "role": {
      "admin": "အက်ဒမင်",
      "manager": "မန်နေဂျာ",
      "sales": "ရောင်းချရေးမှူး",
      "accountant": "စာရင်းကိုင်",
      "inventory": "စတော့မန်နေဂျာ"
    },
    "stats": {
      "invoicesCreated": "ဖန်တီးထားသော ငွေတောင်းခံလွှာများ",
      "customersAdded": "ထည့်ထားသော ဖောက်သည်များ",
      "revenueGenerated": "ဖန်တီးထားသော ဝင်ငွေ"
    },
    "settings": {
      "title": "ဆက်တင်များ",
      "language": "ဘာသာစကား",
      "darkMode": "အမှောင်မုဒ်",
      "notifications": "အကြောင်းကြားချက်များ",
      "biometric": "ဇီဝမှတ်တမ်းဖြင့် ဝင်ရောက်ခြင်း",
      "about": "ERP SOLUTION အကြောင်း",
      "version": "ဗားရှင်း {{version}}"
    },
    "languageOptions": {
      "english": "English",
      "myanmar": "မြန်မာ (Myanmar)"
    }
  }
}

---

# my (1) (1)-converted.md

{
  "common": {
    "appName": "ERP SOLUTION",
    "loading": "ဖွင့်နေသည်...",
    "retry": "ပြန်လည်ကြိုးစားမည်",
    "cancel": "ပယ်ဖျက်မည်",
    "save": "သိမ်းဆည်းမည်",
    "delete": "ဖျက်မည်",
    "edit": "ပြင်ဆင်မည်",
    "create": "ဖန်တီးမည်",
    "search": "ရှာဖွေမည်",
    "filter": "စစ်ထုတ်မည်",
    "all": "အားလုံး",
    "active": "လှုပ်ရှားနေသော",
    "inactive": "အသုံးမပြုသော",
    "pending": "စောင့်ဆိုင်းနေသော",
    "paid": "ပေးဆောင်ပြီးသော",
    "overdue": "သက်တမ်းကျော်နေသော",
    "success": "အောင်မြင်ပါသည်",
    "error": "အမှား",
    "confirm": "အတည်ပြုမည်",
    "back": "နောက်သို့",
    "next": "ရှေ့သို့",
    "done": "ပြီးပါပြီ",
    "close": "ပိတ်မည်",
    "noResults": "ရလဒ်မတွေ့ပါ",
    "pullToRefresh": "စ်ပြန်လည်ရယူရန် ဆွဲချပါ",
    "offline": "အင်တာနက်မရှိပါ",
    "online": "အင်တာနက်ပြန်လည်ရှိပါပြီ",
    "currency": "ကျပ်",
    "dateFormat": "DD/MM/YYYY",
    "timeFormat": "hh:mm A"
  },
  "auth": {
    "loginTitle": "ကြိုဆိုပါသည်",
    "loginSubtitle": "ERP SOLUTION အကောင့်သို့ ဝင်ရောက်ပါ",
    "email": "အီးမေးလ်",
    "emailPlaceholder": "အီးမေးလ်ထည့်ပါ",
    "password": "စကားဝှက်",
    "passwordPlaceholder": "စကားဝှက်ထည့်ပါ",
    "signIn": "ဝင်ရောက်မည်",
    "signingIn": "ဝင်ရောက်နေသည်...",
    "forgotPassword": "စကားဝှက်မေ့နေပါသလား?",
    "forgotPasswordTitle": "စကားဝှက်ပြန်လည်သတ်မှတ်မည်",
    "forgotPasswordSubtitle": "အီးမေးလ်ထည့်ပါ၊ လမ်းညွှန်ချက်များပို့ပေးပါမည်",
    "sendResetLink": "လင့်ပို့ပေးမည်",
    "resetLinkSent": "သင့်အီးမေးလ်သို့ လင့်ပို့ပြီးပါပြီ",
    "biometricPrompt": "ဇီဝမှတ်တမ်းဖြင့် ဝင်ရောက်မည်",
    "biometricError": "ဇီဝမှတ်တမ်းဝင်ရောက်ခြင်း မအောင်မြင်ပါ",
    "invalidCredentials": "အီးမေးလ် သို့မဟုတ် စကားဝှက်မမှန်ပါ",
    "sessionExpired": "အကောင့်သက်တမ်းကုန်ပါပြီ။ ပြန်လည်ဝင်ရောက်ပါ။",
    "logout": "ထွက်မည်",
    "logoutConfirm": "အကောင့်မှ ထွက်ရန် သေချာပါသလား?"
  },
  "dashboard": {
    "title": "ဒက်ရှ်ဘုတ်",
    "greeting": "{{timeOfDay}}မှာ မင်္ဂလာပါ၊ {{name}}",
    "morning": "မနက်ခင်း",
    "afternoon": "နေ့လယ်",
    "evening": "ညနေ",
    "kpi": {
      "revenue": "စုစုပေါင်းဝင်ငွေ",
      "sales": "စုစုပေါင်းရောင်းချမှု",
      "customers": "လှုပ်ရှားနေသော ဖောက်သည်များ",
      "invoices": "စောင့်ဆိုင်းနေသော ငွေတောင်းခံလွှာများ",
      "vsLastMonth": "ပြီးခဲ့သည့်လနှင့် နှိုင်းယှဉ်"
    },
    "charts": {
      "revenueTrend": "ဝင်ငွေအလျား",
      "thisMonth": "ယခုလ",
      "lastMonth": "ပြီးခဲ့သည့်လ"
    },
    "pipeline": {
      "title": "ရောင်းချမှု လမ်းကြောင်း",
      "lead": "ဦးစီးမှု",
      "qualified": "အရည်အချင်းပြည့်မီ",
      "proposal": "အဆိုပြုချက်",
      "negotiation": "ဆွေးနွေးမှု",
      "closed": "အောင်မြင်စွာ ပြီးစီး"
    },
    "recentActivity": {
      "title": "လတ်တလော လှုပ်ရှားမှုများ",
      "invoiceCreated": "{{customer}} အတွက် ငွေတောင်းခံလွှာ #{{number}} ဖန်တီးပြီးပါပြီ",
      "paymentReceived": "{{customer}} ထံမှ {{amount}} ဝင်ငွေရရှိပြီးပါပြီ",
      "contactAdded": "ဆက်သွယ်ရန် အသစ်ထည့်ပြီးပါပြီ - {{name}}",
      "stockUpdated": "{{product}} အတွက် စတော့စ်ပြင်ဆင်ပြီးပါပြီ"
    }
  },
  "contacts": {
    "title": "ဆက်သွယ်ရန်များ",
    "searchPlaceholder": "ဆက်သွယ်ရန်များ ရှာဖွေပါ...",
    "addContact": "ဆက်သွယ်ရန်ထည့်မည်",
    "contactTypes": {
      "customer": "ဖောက်သည်",
      "supplier": "ပေးသွင်းသူ",
      "vendor": "ရောင်းချသူ",
      "employee": "ဝန်ထမ်း"
    },
    "fields": {
      "name": "အမည်",
      "phone": "ဖုန်းနံပါတ်",
      "email": "အီးမေးလ်",
      "company": "ကုမ္ပဏီ",
      "type": "အမျိုးအစား",
      "status": "အခြေအနေ",
      "address": "လိပ်စာ"
    },
    "actions": {
      "call": "ခေါ်ဆိုမည်",
      "email": "အီးမေးလ်ပို့မည်",
      "message": "မက်ဆေ့ချ်ပို့မည်",
      "viewProfile": "ပရိုဖိုင်ကြည့်မည်"
    },
    "emptyState": "ဆက်သွယ်ရန်မရှိသေးပါ။ + နှိပ်ပြီး ပထမဆုံးထည့်ပါ။"
  },
  "invoices": {
    "title": "ငွေတောင်းခံလွှာများ",
    "addInvoice": "ငွေတောင်းခံလွှာထည့်မည်",
    "filters": {
      "all": "ငွေတောင်းခံလွှာအားလုံး",
      "paid": "ပေးဆောင်ပြီးသော",
      "pending": "စောင့်ဆိုင်းနေသော",
      "overdue": "သက်တမ်းကျော်နေသော"
    },
    "fields": {
      "invoiceNumber": "ငွေတောင်းခံလွှာနံပါတ်",
      "customer": "ဖောက်သည်",
      "amount": "ငွေပမာဏ",
      "dueDate": "ပေးဆောင်ရန်နေ့",
      "status": "အခြေအနေ",
      "items": "ပစ္စည်းများ",
      "subtotal": "အစီရင်ခံ",
      "tax": "အခွန်",
      "total": "စုစုပေါင်း",
      "notes": "မှတ်ချက်များ"
    },
    "overdueAlert": "သက်တမ်းကျော် ငွေတောင်းခံလွှာ {{count}} စောင်",
    "createSuccess": "ငွေတောင်းခံလွှာဖန်တီးပြီးပါပြီ",
    "deleteConfirm": "ငွေတောင်းခံလွှာ {{number}} ဖျက်မည်လား? ဤလုပ်ဆောင်ချက်ကို ပြန်လည်ရုပ်သိမ်းမရပါ။",
    "emptyState": "ငွေတောင်းခံလွှာမရှိပါ။ ပထမဆုံးဖန်တီးပါ။"
  },
  "search": {
    "title": "ရှာဖွေမှု",
    "placeholder": "မှတ်တမ်းအားလုံးမှ ရှာဖွေပါ...",
    "recentSearches": "လတ်တလော ရှာဖွေမှုများ",
    "clearHistory": "မှတ်တမ်းရှင်းလင်းမည်",
    "entities": {
      "contacts": "ဆက်သွယ်ရန်များ",
      "invoices": "ငွေတောင်းခံလွှာများ",
      "products": "ပစ္စည်းများ",
      "inventory": "စတော့",
      "transactions": "ငွေကြောင်းများ"
    },
    "results": {
      "contacts": "ဆက်သွယ်ရန် {{count}} ဦး တွေ့ပါသည်",
      "invoices": "ငွေတောင်းခံလွှာ {{count}} စောင် တွေ့ပါသည်",
      "products": "ပစ္စည်း {{count}} ခု တွေ့ပါသည်"
    }
  },
  "aiCopilot": {
    "title": "AI ကူညီသူ",
    "status": {
      "online": "အွန်လိုင်း",
      "offline": "အွန်လိုင်းမရှိ",
      "thinking": "စဉ်းစားနေသည်..."
    },
    "placeholder": "သင့်စီးပွားရေးအကြောင်း မေးခွန်းမေးပါ...",
    "suggestions": {
      "revenue": "ယခုလ ဝင်ငွေဘယ်လောက်လဲ?",
      "overdue": "သက်တမ်းကျော် ငွေတောင်းခံလွှာများ ပြပါ",
      "stock": "စတော့နည်းနေသော ပစ္စည်းများရှိလား?",
      "customer": "အကောင်းဆုံး ဖောက်သည်များဘယ်သူတွေလဲ?"
    },
    "actions": {
      "send": "ပို့မည်",
      "voice": "အသံထွက်ဖြင့်မေးမည်",
      "attach": "ဖိုင်ထည့်မည်",
      "clear": "စကားဝိုင်းရှင်းလင်းမည်"
    },
    "responses": {
      "revenue": "ယခုလ ဝင်ငွေမှာ {{amount}} ဖြစ်ပြီး ပြီးခဲ့သည့်လထက် {{percentage}}% တိုးတက်ပါသည်။",
      "overdue": "သက်တမ်းကျော် ငွေတောင်းခံလွှာ {{count}} စောင် ရှိပြီး စုစုပေါင်း {{amount}} ဖြစ်ပါသည်။",
      "stock": "စတော့နည်းနေသော ပစ္စည်း {{count}} ခု ရှိပါသည် - {{items}}။",
      "greeting": "မင်္ဂလာပါ! ကျွန်ုပ်သည် သင့်ကူညီသူ ဖြစ်ပါသည်။ ဘယ်လိုကူညီရမလဲ?"
    }
  },
  "inventory": {
    "title": "စတော့",
    "stockCard": {
      "onHand": "လက်ရှိစတော့",
      "reserved": "ဘွတ်ကင်ထားသော",
      "available": "ရရှိနိုင်သော",
      "reorderLevel": "မှာယူရမည့်အဆင့်",
      "reorderPoint": "မှာယူမှတ်တိုင်"
    },
    "status": {
      "inStock": "စတော့ရှိသည်",
      "lowStock": "စတော့နည်းနေသည်",
      "outOfStock": "စတော့ကုန်နေသည်",
      "discontinued": "ရပ်ဆိုင်းထားသည်"
    },
    "actions": {
      "adjustStock": "စတော့ပြင်ဆင်မည်",
      "viewHistory": "မှတ်တမ်းကြည့်မည်",
      "setReorderPoint": "မှာယူမှတ်တိုင်းသတ်မှတ်မည်"
    },
    "metrics": {
      "totalItems": "စတော့ပစ္စည်းစုစုပေါင်း",
      "lowStockItems": "စတော့နည်းနေသော ပစ္စည်းများ",
      "totalValue": "စတော့တန်ဖိုးစုစုပေါင်း"
    },
    "emptyState": "စတော့ပစ္စည်းမရှိသေးပါ။ စတော့ထိန်းသိမ်းရန် ပစ္စည်းထည့်ပါ။"
  },
  "profile": {
    "title": "ပရိုဖိုင်",
    "role": {
      "admin": "အက်ဒမင်",
      "manager": "မန်နေဂျာ",
      "sales": "ရောင်းချရေးမှူး",
      "accountant": "စာရင်းကိုင်",
      "inventory": "စတော့မန်နေဂျာ"
    },
    "stats": {
      "invoicesCreated": "ဖန်တီးထားသော ငွေတောင်းခံလွှာများ",
      "customersAdded": "ထည့်ထားသော ဖောက်သည်များ",
      "revenueGenerated": "ဖန်တီးထားသော ဝင်ငွေ"
    },
    "settings": {
      "title": "ဆက်တင်များ",
      "language": "ဘာသာစကား",
      "darkMode": "အမှောင်မုဒ်",
      "notifications": "အကြောင်းကြားချက်များ",
      "biometric": "ဇီဝမှတ်တမ်းဖြင့် ဝင်ရောက်ခြင်း",
      "about": "ERP SOLUTION အကြောင်း",
      "version": "ဗားရှင်း {{version}}"
    },
    "languageOptions": {
      "english": "English",
      "myanmar": "မြန်မာ (Myanmar)"
    }
  }
}

---

# LoginScreen.i18n-example (1)-converted.md

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { TextInput, Button, Text, HelperText } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useLanguage } from '../hooks/useLanguage';

export const LoginScreen: React.FC = () => {
  const { t } = useTranslation();
  const { isMyanmar } = useLanguage();

  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      // Your auth logic here
    } catch (err) {
      setError(t('auth.invalidCredentials'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text
        variant="headlineMedium"
        style={[
          styles.title,
          isMyanmar && { fontFamily: 'Pyidaungsu' }
        ]}
      >
        {t('auth.loginTitle')}
      </Text>

      <Text variant="bodyMedium" style={styles.subtitle}>
        {t('auth.loginSubtitle')}
      </Text>

      <TextInput
        label={t('auth.email')}
        placeholder={t('auth.emailPlaceholder')}
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        style={styles.input}
      />

      <TextInput
        label={t('auth.password')}
        placeholder={t('auth.passwordPlaceholder')}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        style={styles.input}
      />

      {error ? (
        <HelperText type="error" visible={!!error}>
          {error}
        </HelperText>
      ) : null}

      <Button
        mode="contained"
        onPress={handleLogin}
        loading={loading}
        disabled={loading || !email || !password}
        style={styles.button}
      >
        {loading ? t('auth.signingIn') : t('auth.signIn')}
      </Button>

      <Button
        mode="text"
        onPress={() => {/* Navigate to forgot password */}}
        style={styles.linkButton}
      >
        {t('auth.forgotPassword')}
      </Button>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 32,
    opacity: 0.7,
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
    paddingVertical: 6,
  },
  linkButton: {
    marginTop: 16,
  },
});

---

# LanguageSwitcher (1)-converted.md

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { List, RadioButton, Text, Divider } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import AsyncStorage from '@react-native-async-storage/async-storage';

type Language = 'en' | 'my';

interface LanguageOption {
  code: Language;
  label: string;
  nativeLabel: string;
}

const LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', nativeLabel: 'English' },
  { code: 'my', label: 'Myanmar', nativeLabel: 'မြန်မာ' },
];

export const LanguageSwitcher: React.FC = () => {
  const { i18n, t } = useTranslation();
  const currentLanguage = i18n.language as Language;

  const changeLanguage = async (lang: Language) => {
    await i18n.changeLanguage(lang);
    await AsyncStorage.setItem('app-language', lang);
  };

  return (
    <View style={styles.container}>
      <Text variant="titleMedium" style={styles.title}>
        {t('profile.settings.language')}
      </Text>
      <Divider style={styles.divider} />
      {LANGUAGES.map((lang) => (
        <List.Item
          key={lang.code}
          title={lang.nativeLabel}
          description={lang.label}
          right={() => (
            <RadioButton
              value={lang.code}
              status={currentLanguage === lang.code ? 'checked' : 'unchecked'}
              onPress={() => changeLanguage(lang.code)}
            />
          )}
          onPress={() => changeLanguage(lang.code)}
          style={styles.item}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
  },
  title: {
    marginBottom: 8,
  },
  divider: {
    marginBottom: 8,
  },
  item: {
    paddingVertical: 4,
  },
});

---

# index-converted (1)-converted.md

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';
import AsyncStorage from '@react-native-async-storage/async-storage';
import en from './locales/en.json';
import my from './locales/my.json';

const LANGUAGE_DETECTOR = {
  type: 'languageDetector' as const,
  async: true,
  detect: async (callback: (lng: string) => void) => {
    try {
      const savedLanguage = await AsyncStorage.getItem('app-language');
      if (savedLanguage) {
        callback(savedLanguage);
        return;
      }
      const deviceLocale = Localization.locale.split('-')[0];
      callback(deviceLocale === 'my' ? 'my' : 'en');
    } catch {
      callback('en');
    }
  },
  init: () => {},
  cacheUserLanguage: async (lng: string) => {
    await AsyncStorage.setItem('app-language', lng);
  },
};

const resources = {
  en: { translation: en },
  my: { translation: my },
};

i18n
  .use(LANGUAGE_DETECTOR)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;

---

# index (1)-converted.md

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';
import AsyncStorage from '@react-native-async-storage/async-storage';
import en from './locales/en.json';
import my from './locales/my.json';

const LANGUAGE_DETECTOR = {
  type: 'languageDetector' as const,
  async: true,
  detect: async (callback: (lng: string) => void) => {
    try {
      const savedLanguage = await AsyncStorage.getItem('app-language');
      if (savedLanguage) {
        callback(savedLanguage);
        return;
      }
      const deviceLocale = Localization.locale.split('-')[0];
      callback(deviceLocale === 'my' ? 'my' : 'en');
    } catch {
      callback('en');
    }
  },
  init: () => {},
  cacheUserLanguage: async (lng: string) => {
    await AsyncStorage.setItem('app-language', lng);
  },
};

const resources = {
  en: { translation: en },
  my: { translation: my },
};

i18n
  .use(LANGUAGE_DETECTOR)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
    react: {
      useSuspense: false,
    },
  });

export default i18n;

---

# check-i18n-coverage (1)-converted.md

const fs = require('fs');
const path = require('path');

const localesDir = path.join(__dirname, '../src/i18n/locales');
const files = fs.readdirSync(localesDir).filter(f => f.endsWith('.json'));

const translations = {};
files.forEach(file => {
  const content = JSON.parse(fs.readFileSync(path.join(localesDir, file), 'utf8'));
  translations[file.replace('.json', '')] = flattenObject(content);
});

function flattenObject(obj, prefix = '', result = {}) {
  for (const key in obj) {
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      flattenObject(obj[key], `${prefix}${key}.`, result);
    } else {
      result[`${prefix}${key}`] = obj[key];
    }
  }
  return result;
}

const baseLang = 'en';
const baseKeys = Object.keys(translations[baseLang]);

console.log('\n=== i18n Coverage Report ===\n');

Object.keys(translations).forEach(lang => {
  if (lang === baseLang) return;

  const missing = baseKeys.filter(key => !translations[lang][key]);
  const extra = Object.keys(translations[lang]).filter(key => !baseKeys.includes(key));

  console.log(`${lang.toUpperCase()}:`);
  console.log(`  Total keys: ${Object.keys(translations[lang]).length}/${baseKeys.length}`);
  console.log(`  Missing: ${missing.length}`);

  if (missing.length > 0) {
    console.log('  Missing keys:');
    missing.slice(0, 10).forEach(key => console.log(`    - ${key}`));
    if (missing.length > 10) console.log(`    ... and ${missing.length - 10} more`);
  }

  if (extra.length > 0) {
    console.log(`  Extra keys: ${extra.length}`);
  }

  console.log('');
});

---

# App.tsx.i18n-snippet (1)-converted.md

// Add to your App.tsx or root entry point

import './src/i18n'; // Initialize i18n before app render
import * as Sentry from '@sentry/react-native';
import { initSentry } from './src/utils/sentry';
import { PaperProvider } from 'react-native-paper';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RootNavigator } from './src/navigation/RootNavigator';

const queryClient = new QueryClient();

// Initialize Sentry
initSentry();

export default function App() {
  // i18n is auto-initialized via the import
  // Language is detected from device or AsyncStorage

  return (
    <QueryClientProvider client={queryClient}>
      <PaperProvider>
        <NavigationContainer>
          <RootNavigator />
        </NavigationContainer>
      </PaperProvider>
    </QueryClientProvider>
  );
}

---

