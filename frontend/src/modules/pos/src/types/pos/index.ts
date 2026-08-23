export interface POSProduct {
  id: string;
  sku: string;
  name: string;
  description?: string;
  categoryId: string;
  categoryName: string;
  price: number;
  costPrice: number;
  taxRate: number;
  taxInclusive: boolean;
  barcode?: string;
  imageUrl?: string;
  stockQuantity: number;
  unit: string;
  isActive: boolean;
  variants?: ProductVariant[];
  discounts?: ProductDiscount[];
}

export interface ProductVariant {
  id: string;
  name: string;
  sku: string;
  barcode?: string;
  price: number;
  stockQuantity: number;
  attributes: Record<string, string>;
}

export interface ProductDiscount {
  id: string;
  name: string;
  type: 'percentage' | 'fixed_amount';
  value: number;
  minQuantity: number;
  startDate: string;
  endDate: string;
  isActive: boolean;
}

export interface CartItem {
  id: string;
  productId: string;
  productName: string;
  sku: string;
  barcode?: string;
  variantId?: string;
  variantName?: string;
  quantity: number;
  unitPrice: number;
  originalPrice: number;
  discountAmount: number;
  discountPercentage: number;
  taxAmount: number;
  taxRate: number;
  subtotal: number;
  total: number;
  imageUrl?: string;
  notes?: string;
}

export interface Cart {
  items: CartItem[];
  subtotal: number;
  totalDiscount: number;
  totalTax: number;
  total: number;
  itemCount: number;
  totalQuantity: number;
  customerId?: string;
  customerName?: string;
  notes?: string;
  appliedDiscounts: AppliedDiscount[];
}

export interface AppliedDiscount {
  id: string;
  name: string;
  type: 'percentage' | 'fixed_amount';
  value: number;
  amount: number;
}

export interface POSSale {
  id: string;
  saleNumber: string;
  cart: Cart;
  payments: Payment[];
  status: SaleStatus;
  refundAmount?: number;
  refundReason?: string;
  cashierId: string;
  cashierName: string;
  registerId: string;
  registerName: string;
  shiftId: string;
  customerId?: string;
  customerName?: string;
  receiptPrinted: boolean;
  receiptNumber?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export type SaleStatus = 'draft' | 'pending_payment' | 'completed' | 'refunded' | 'cancelled';

export interface Payment {
  id: string;
  method: PaymentMethod;
  amount: number;
  receivedAmount: number;
  changeAmount: number;
  reference?: string;
  status: PaymentStatus;
  processedAt?: string;
  cardLast4?: string;
  cardType?: string;
  bankName?: string;
  transactionId?: string;
}

export type PaymentMethod = 'cash' | 'card' | 'bank_transfer' | 'mobile_money' | 'credit' | 'gift_card' | 'coupon';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export interface POSShift {
  id: string;
  shiftNumber: string;
  cashierId: string;
  cashierName: string;
  registerId: string;
  registerName: string;
  openingAmount: number;
  closingAmount?: number;
  expectedAmount?: number;
  difference?: number;
  status: ShiftStatus;
  openedAt: string;
  closedAt?: string;
  salesCount: number;
  refundsCount: number;
  totalSales: number;
  totalRefunds: number;
  totalCashPayments: number;
  totalCardPayments: number;
  totalOtherPayments: number;
  notes?: string;
}

export type ShiftStatus = 'open' | 'closed' | 'counted';

export interface POSRegister {
  id: string;
  name: string;
  code: string;
  location: string;
  isActive: boolean;
  currentShiftId?: string;
  currentCashierId?: string;
  currentCashierName?: string;
  receiptPrinterName?: string;
  barcodeScannerName?: string;
  cashDrawerConnected: boolean;
  receiptTemplate: string;
}

export interface POSCategory {
  id: string;
  name: string;
  code: string;
  color: string;
  icon?: string;
  parentId?: string;
  productCount: number;
  isActive: boolean;
  displayOrder: number;
}

export interface POSKPI {
  todaySales: number;
  todayTransactions: number;
  todayAverageTicket: number;
  todayItemsSold: number;
  todayRefunds: number;
  currentShiftSales: number;
  currentShiftTransactions: number;
  topProducts: TopProduct[];
  paymentMethodBreakdown: PaymentMethodBreakdown[];
  hourlySales: HourlySale[];
}

export interface TopProduct {
  productId: string;
  productName: string;
  quantity: number;
  revenue: number;
}

export interface PaymentMethodBreakdown {
  method: PaymentMethod;
  amount: number;
  count: number;
  percentage: number;
}

export interface HourlySale {
  hour: number;
  sales: number;
  transactions: number;
}

export interface ReceiptData {
  sale: POSSale;
  storeName: string;
  storeAddress: string;
  storePhone: string;
  storeTaxId: string;
  receiptFooter: string;
  logoUrl?: string;
}

export interface QuickAction {
  id: string;
  name: string;
  icon: string;
  action: 'open_shift' | 'close_shift' | 'cash_in' | 'cash_out' | 'print_last_receipt' | 'return_item' | 'suspend_sale' | 'discount';
  requiresAuth: boolean;
}

