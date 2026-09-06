# Formulas & Algorithms Reference

Comprehensive documentation of mathematical formulas, algorithms, and calculation patterns used across the ERP system.

## Table of Contents

1. [Financial Calculations](#financial-calculations)
2. [Inventory & Supply Chain](#inventory--supply-chain)
3. [HR & Payroll](#hr--payroll)
4. [Project Management](#project-management)
5. [Analytics & Reporting](#analytics--reporting)
6. [Data Processing Algorithms](#data-processing-algorithms)

---

## Financial Calculations

### 1.1 Tax Calculations

#### Basic Tax Formula
```typescript
taxAmount = baseAmount × (taxRate / 100)
totalWithTax = baseAmount + taxAmount
```

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:140-142
export const calculateWithTax = (amount: number, taxRate: number): number => {
  return amount * (1 + taxRate / 100);
};
```

#### Multi-Tier Tax Calculation
For jurisdictions with multiple tax layers (e.g., state + local):
```typescript
totalTax = baseAmount × Σ(taxRate_i / 100)
where i = 1 to n tax layers
```

### 1.2 Discount Calculations

#### Single Discount
```typescript
discountAmount = originalPrice × (discountRate / 100)
finalPrice = originalPrice - discountAmount
finalPrice = originalPrice × (1 - discountRate / 100)
```

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:149-160
export const calculateDiscount = (originalPrice: number, discountRate: number): number => {
  return originalPrice * (discountRate / 100);
};

export const applyDiscount = (originalPrice: number, discountRate: number): number => {
  return originalPrice - calculateDiscount(originalPrice, discountRate);
};
```

#### Compound Discounts (Sequential)
When multiple discounts apply sequentially:
```typescript
finalPrice = originalPrice × (1 - d₁) × (1 - d₂) × ... × (1 - dₙ)
```

⚠️ **Note:** Sequential discounts are NOT additive. A 20% + 10% discount is NOT 30%, but rather:
```
finalPrice = original × (1 - 0.20) × (1 - 0.10) = original × 0.72 (28% total discount)
```

### 1.3 Growth Rate Calculations

#### Percentage Growth Rate
```typescript
growthRate = ((current - previous) / previous) × 100
```

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:112-115
export const calculateGrowthRate = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};
```

#### Edge Cases Handled:
- `previous = 0, current > 0` → Returns 100% (infinite growth approximation)
- `previous = 0, current = 0` → Returns 0% (no change)
- `previous < 0` → Standard formula applies (can yield counterintuitive results)

### 1.4 Cart & Order Totals

#### Line Item Subtotal
```typescript
lineSubtotal = quantity × unitPrice
```

#### Order Total with Tax and Discounts
```typescript
subtotal = Σ(quantityᵢ × priceᵢ) for all items
totalDiscount = Σ(discountAmountᵢ)
totalTax = Σ(taxAmountᵢ)
grandTotal = subtotal - totalDiscount + totalTax
```

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:131-133
export const calculateTotal = <T extends { quantity: number; price: number }>(items: T[]): number => {
  return items.reduce((sum, item) => sum + item.quantity * item.price, 0);
};

// frontend/src/shared/utils/storeHelpers.ts:123-151
export const calculateCartTotals = <T extends {
  quantity: number;
  subtotal?: number;
  taxAmount?: number;
  discountAmount?: number;
}>(items: T[]): {
  subtotal: number;
  totalTax: number;
  totalDiscount: number;
  totalQuantity: number;
  itemCount: number;
} => {
  const subtotal = items.reduce((sum, item) => sum + (item.subtotal || item.quantity * 0), 0);
  const totalTax = items.reduce((sum, item) => sum + (item.taxAmount || 0), 0);
  const totalDiscount = items.reduce((sum, item) => sum + (item.discountAmount || 0), 0);
  const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);
  
  return {
    subtotal,
    totalTax,
    totalDiscount,
    totalQuantity,
    itemCount: items.length,
  };
};
```

### 1.5 Currency Rounding

#### Banker's Rounding (Round Half to Even)
Prevents bias in financial calculations:
```typescript
round(value, decimals) = 
  if fractional_part = 0.5:
    round to nearest even number
  else:
    standard rounding
```

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:214-217
export const roundTo = (value: number, decimals: number = 2): number => {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
};
```

---

## Inventory & Supply Chain

### 2.1 Stock Level Calculations

#### Available Stock
```typescript
availableStock = physicalStock + onOrder - reserved - backorders
```

#### Reorder Point (ROP)
```typescript
ROP = (averageDailySales × leadTimeDays) + safetyStock
```

#### Safety Stock Calculation
Using standard deviation method:
```typescript
safetyStock = z-score × σ_demand × √leadTime
where:
  z-score = service level factor (e.g., 1.65 for 95% service level)
  σ_demand = standard deviation of daily demand
```

### 2.2 Economic Order Quantity (EOQ)

Classic inventory optimization formula:
```typescript
EOQ = √((2 × D × S) / H)
where:
  D = annual demand (units)
  S = ordering cost per order
  H = holding cost per unit per year
```

#### Total Annual Cost
```typescript
TC = (D × P) + (D/EOQ × S) + (EOQ/2 × H)
where:
  P = price per unit
```

### 2.3 Inventory Turnover

#### Turnover Ratio
```typescript
inventoryTurnover = COGS / averageInventory
where:
  COGS = Cost of Goods Sold (period)
  averageInventory = (beginningInventory + endingInventory) / 2
```

#### Days Sales of Inventory (DSI)
```typescript
DSI = 365 / inventoryTurnover
```

---

## HR & Payroll

### 3.1 Salary Calculations

#### Gross Pay (Hourly with Overtime)
```typescript
if hoursWorked ≤ 40:
  grossPay = hoursWorked × hourlyRate
else:
  grossPay = (40 × hourlyRate) + ((hoursWorked - 40) × hourlyRate × overtimeMultiplier)
where:
  overtimeMultiplier = 1.5 (time-and-a-half) or 2.0 (double-time)
```

#### Net Pay
```typescript
netPay = grossPay - deductions - taxes
where:
  deductions = insurance + retirement + union_dues + etc.
  taxes = federal_tax + state_tax + local_tax + social_security + medicare
```

### 3.2 Leave Accrual

#### Monthly Accrual Rate
```typescript
monthlyAccrual = annualAllowance / 12
```

#### Pro-rated Accrual (Mid-year Hire)
```typescript
accruedLeave = monthlyAccrual × monthsRemainingInYear
```

#### Leave Balance
```typescript
balance = previousBalance + accrued - used - expired
```

### 3.3 Payroll Tax Calculations

#### Progressive Tax Brackets
```typescript
tax = Σ(bracketWidthᵢ × bracketRateᵢ) + (excess × marginalRate)
```

Example (simplified US federal tax 2024):
| Bracket | Rate |
|---------|------|
| $0 - $11,600 | 10% |
| $11,601 - $47,150 | 12% |
| $47,151 - $100,525 | 22% |
| ... | ... |

---

## Project Management

### 4.1 Earned Value Management (EVM)

#### Planned Value (PV)
```typescript
PV = budgetAtCompletion × plannedPercentComplete
```

#### Earned Value (EV)
```typescript
EV = budgetAtCompletion × actualPercentComplete
```

#### Cost Performance Index (CPI)
```typescript
CPI = EV / AC
where:
  AC = Actual Cost
CPI > 1 = under budget
CPI < 1 = over budget
```

#### Schedule Performance Index (SPI)
```typescript
SPI = EV / PV
SPI > 1 = ahead of schedule
SPI < 1 = behind schedule
```

#### Estimate at Completion (EAC)
Multiple formulas based on assumptions:

**Typical Variance:**
```typescript
EAC = BAC / CPI
```

**New Estimate:**
```typescript
EAC = AC + Bottom-up ETC
```

**Variants Considered:**
```typescript
EAC = AC + (BAC - EV) / (CPI × SPI)
```

### 4.2 Task Duration Estimation

#### PERT (Program Evaluation Review Technique)
```typescript
expectedDuration = (optimistic + 4 × mostLikely + pessimistic) / 6
standardDeviation = (pessimistic - optimistic) / 6
```

#### Confidence Intervals
```typescript
68% confidence: expectedDuration ± 1σ
95% confidence: expectedDuration ± 2σ
99.7% confidence: expectedDuration ± 3σ
```

---

## Analytics & Reporting

### 5.1 Key Performance Indicators (KPIs)

#### Customer Acquisition Cost (CAC)
```typescript
CAC = totalMarketingAndSalesCost / newCustomersAcquired
```

#### Customer Lifetime Value (CLV)
Simple formula:
```typescript
CLV = averageOrderValue × purchaseFrequency × customerLifespan
```

Advanced (with discount rate):
```typescript
CLV = Σ((marginᵢ) / (1 + r)ⁱ) for i = 1 to n
where:
  r = discount rate
  n = customer lifespan in periods
```

#### Churn Rate
```typescript
churnRate = (customersLostDuringPeriod / customersAtStartOfPeriod) × 100
```

#### Retention Rate
```typescript
retentionRate = ((customersEnd - customersNew) / customersStart) × 100
```

### 5.2 Trend Analysis

#### Moving Average (SMA)
```typescript
SMAₜ = (Σ(priceᵢ)) / n for i = t-n+1 to t
```

#### Exponential Moving Average (EMA)
```typescript
EMAₜ = (priceₜ × α) + (EMAₜ₋₁ × (1 - α))
where:
  α = smoothing factor = 2 / (n + 1)
```

**Implementation Pattern:**
```typescript
const calculateEMA = (values: number[], period: number): number[] => {
  const alpha = 2 / (period + 1);
  const ema: number[] = [];
  ema[0] = values[0];
  
  for (let i = 1; i < values.length; i++) {
    ema[i] = (values[i] * alpha) + (ema[i-1] * (1 - alpha));
  }
  
  return ema;
};
```

### 5.3 Conversion Funnel Metrics

#### Conversion Rate
```typescript
conversionRate = (conversions / visitors) × 100
```

#### Funnel Drop-off Rate
```typescript
dropOffRate = ((visitorsStep₁ - visitorsStep₂) / visitorsStep₁) × 100
```

---

## Data Processing Algorithms

### 6.1 Debounce Algorithm

Prevents excessive function calls by delaying execution until after a quiet period.

**Time Complexity:** O(1) per call  
**Space Complexity:** O(1)

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:167-177
export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};
```

**Use Cases:**
- Search input (wait for user to stop typing)
- Window resize handlers
- Auto-save functionality

### 6.2 Throttle Algorithm

Ensures a function is called at most once in a specified time interval.

**Time Complexity:** O(1) per call  
**Space Complexity:** O(1)

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:184-197
export const throttle = <T extends (...args: any[]) => void>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean = false;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};
```

**Use Cases:**
- Scroll event handlers
- Button click prevention
- API rate limiting

### 6.3 Array Operations

#### Update Item in Array
**Time Complexity:** O(n)  
**Space Complexity:** O(n) - creates new array (immutable pattern)

**Implementation:**
```typescript
// frontend/src/shared/utils/storeHelpers.ts:49-58
export const updateArrayItem = <T extends Record<string, any>>(
  array: T[],
  itemId: string | number,
  updates: Partial<T>,
  idField: keyof T = 'id' as keyof T
): T[] => {
  return array.map((item) =>
    item[idField] === itemId ? { ...item, ...updates } : item
  );
};
```

#### Upsert (Update or Insert)
**Time Complexity:** O(n)  
**Space Complexity:** O(n)

**Implementation:**
```typescript
// frontend/src/shared/utils/storeHelpers.ts:103-117
export const upsertInArray = <T extends Record<string, any>>(
  array: T[],
  item: T,
  idField: keyof T = 'id' as keyof T
): T[] => {
  const existingIndex = array.findIndex((i) => i[idField] === item[idField]);
  
  if (existingIndex >= 0) {
    const newArray = [...array];
    newArray[existingIndex] = item;
    return newArray;
  }
  
  return [...array, item];
};
```

### 6.4 Number Formatting Algorithms

#### Compact Number Notation (K, M, B)
Uses Intl.NumberFormat for locale-aware formatting:

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:44-49
export const formatCompactNumber = (value: number, locale = 'en-US'): string => {
  return new Intl.NumberFormat(locale, {
    notation: 'compact',
    compactDisplay: 'short',
  }).format(value);
};
```

**Examples:**
- `1,500` → `"1.5K"`
- `2,300,000` → `"2.3M"`
- `4,500,000,000` → `"4.5B"`

#### Relative Time Formatting
**Algorithm:**
```typescript
if diff < 1 minute: "Just now"
else if diff < 60 minutes: "{X}m ago"
else if diff < 24 hours: "{X}h ago"
else if diff < 7 days: "{X}d ago"
else: formatted date
```

**Implementation:**
```typescript
// frontend/src/shared/utils/helpers.ts:72-85
export const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateString);
};
```

---

## System Alignment Notes

### Precision & Rounding Strategy

1. **Financial Calculations**: Always round to 2 decimal places using banker's rounding
2. **Percentages**: Display with 1-2 decimal places based on magnitude
3. **Large Numbers**: Use compact notation for UI, full precision for calculations
4. **Intermediate Values**: Maintain full precision until final display

### Error Handling in Calculations

```typescript
// Division by zero protection
if (denominator === 0) {
  return numerator > 0 ? Infinity : 0; // Context-dependent
}

// Null/undefined handling
const safeValue = value ?? 0; // Default to zero
const safeValue = value ?? defaultValue; // Use domain-specific default
```

### Performance Considerations

1. **Memoization**: Use `React.memo` and `useMemo` for expensive calculations
2. **Web Workers**: Offload heavy computations (>100ms) to background threads
3. **Batching**: Group multiple updates to minimize re-renders
4. **Lazy Loading**: Defer calculation-heavy components until needed

### Thread Safety (Backend)

For Python backend calculations:
- Use `decimal.Decimal` for financial calculations (avoid float precision issues)
- Implement database-level locking for concurrent inventory updates
- Use atomic operations where possible: `F()` expressions in Django ORM

---

## Related Documentation

- [System Architecture](./ARCHITECTURE_DECISIONS.md)
- [API Summary](./API_SUMMARY.md)
- [Testing Strategy](./TESTING.md)
- [Database Migrations](./DATABASE_MIGRATIONS.md)

---

**Last Updated:** 2026-08-17  
**Version:** 1.0  
**Maintained By:** Development Team
