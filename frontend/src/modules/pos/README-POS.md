# ERP SOLUTION Retail POS Module (v2.9)

## Overview
Full-featured Point of Sale system integrated with Inventory, Invoices, and Accounting modules. Designed for fast checkout, barcode scanning, and multi-payment processing.

## Features

### 1. Product Catalog
- Grid view with category filtering
- Barcode scanning (camera + hardware scanner ready)
- Stock level indicators
- Variant support (size, color, etc.)
- Dynamic pricing and discounts
- Quick search by name, SKU, or barcode

### 2. Shopping Cart
- Real-time cart with quantity adjustment
- Automatic tax calculation (inclusive/exclusive)
- Item-level and cart-level discounts
- Customer assignment for loyalty/credit tracking
- Suspend/resume sales
- Cart notes for special instructions

### 3. Payment Processing
- Multiple payment methods: Cash, Card, Bank Transfer, Mobile Money, Credit, Gift Card, Coupon
- Split payments across methods
- Automatic change calculation for cash
- Reference tracking for non-cash payments
- Partial payment support
- Receipt generation

### 4. Shift Management
- Open/close shift with cash count
- Register assignment
- Cashier tracking
- Expected vs actual cash reconciliation
- Difference reporting
- Shift history and audit trail

### 5. Sales & Reporting
- Real-time sales dashboard
- Payment method breakdown
- Hourly sales heatmap
- Top products ranking
- Daily/weekly/monthly reports
- Refund and void tracking
- Export to Excel/PDF

## Screens

| Screen | Description |
|--------|-------------|
| POSScreen | Main selling interface with product grid + cart |
| PaymentModal | Multi-method payment processing overlay |
| ShiftManagement | Open/close shifts, register selection |
| POSReports | Sales analytics, hourly trends, top products |

## Installation

### 1. Copy files to project
```bash
cp -r src/screens/pos/* your-project/src/screens/pos/
cp -r src/types/pos/* your-project/src/types/pos/
cp -r src/store/posStore.ts your-project/src/store/
cp -r src/services/api/posApi.ts your-project/src/services/api/
cp -r src/hooks/usePOS.ts your-project/src/hooks/
cp -r src/navigation/POSNavigator.tsx your-project/src/navigation/
cp -r src/components/pos/* your-project/src/components/pos/
```

### 2. Add POS tab to main navigation
```tsx
import { POSNavigator } from './navigation/POSNavigator';

// In your BottomTab.Navigator:
<Tab.Screen
  name="POS"
  component={POSNavigator}
  options={{
    tabBarIcon: ({ color }) => (
      <MaterialCommunityIcons name="cart" size={24} color={color} />
    ),
  }}
/>
```

### 3. Add PaymentModal to POS screen
```tsx
// In POSScreen.tsx or App wrapper:
import { PaymentModal } from './components/pos/PaymentModal';

// Render at root level:
<PaymentModal />
```

### 4. Backend API Endpoints Required

```
GET    /api/v1/pos/products
GET    /api/v1/pos/products/barcode/:barcode
GET    /api/v1/pos/products/:id/stock

GET    /api/v1/pos/categories

POST   /api/v1/pos/sales
GET    /api/v1/pos/sales
GET    /api/v1/pos/sales/:id
POST   /api/v1/pos/sales/:id/payments
PATCH  /api/v1/pos/sales/:id/complete
POST   /api/v1/pos/sales/:id/refund
PATCH  /api/v1/pos/sales/:id/cancel
GET    /api/v1/pos/sales/:id/receipt
POST   /api/v1/pos/sales/:id/print-receipt

POST   /api/v1/pos/shifts/open
PATCH  /api/v1/pos/shifts/:id/close
GET    /api/v1/pos/shifts/current/:registerId
GET    /api/v1/pos/shifts
GET    /api/v1/pos/shifts/:id

GET    /api/v1/pos/registers

GET    /api/v1/pos/kpi/dashboard
GET    /api/v1/pos/reports/daily
GET    /api/v1/pos/reports/sales
```

## Hardware Integration

### Barcode Scanner
```tsx
// Using expo-camera for barcode scanning
import { CameraView, useCameraPermissions } from 'expo-camera';

// In your barcode scanner component:
<CameraView
  barcodeScannerSettings={{ barcodeTypes: ['ean13', 'ean8', 'upc_a', 'code128'] }}
  onBarcodeScanned={({ data }) => {
    setBarcodeInput(data);
    handleBarcodeSubmit();
  }}
/>
```

### Receipt Printer
```tsx
// Using expo-print for thermal printer support
import * as Print from 'expo-print';

const printReceipt = async (sale: POSSale) => {
  await Print.printAsync({
    html: generateReceiptHTML(sale),
    printerUrl: currentRegister?.receiptPrinterName,
  });
};
```

### Cash Drawer
```tsx
// Trigger cash drawer via Bluetooth/USB serial
import { Serial } from 'expo-serial';

const openCashDrawer = async () => {
  if (currentRegister?.cashDrawerConnected) {
    await Serial.writeAsync(currentRegister.id, '\x1B\x70\x00\x19\xFA');
  }
};
```

## Integration Points

- **Inventory**: Real-time stock deduction on sale, restock on refund
- **Invoices**: POS sales auto-generate simplified invoices
- **Accounting**: Daily sales summary posted to GL
- **Contacts**: Customer loyalty tracking, credit sales
- **Manufacturing**: Component kit sales trigger BOM explosion
- **HR**: Cashier shift tracking, sales commission calculation

## Myanmar-Specific Features

- Mobile Money integration (Wave, KBZPay, CB Pay)
- Myanmar tax calculation (5% commercial tax)
- Local currency formatting (MMK with Myanmar numerals)
- Receipt in Myanmar language
- Fiscal printer compliance ready

## Next Steps

1. **Loyalty Program** - Points accumulation, tier management, rewards
2. **Gift Cards** - Purchase, redemption, balance tracking
3. **Multi-Store** - Cross-store inventory, consolidated reporting
4. **E-commerce Sync** - Online orders integrated with POS
5. **Kitchen Display** - Order routing for F&B operations
6. **Self-Service Kiosk** - Customer-facing ordering interface

