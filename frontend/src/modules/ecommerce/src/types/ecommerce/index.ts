export interface StoreProduct {
  id: string;
  sku: string;
  name: string;
  slug: string;
  description: string;
  shortDescription: string;
  price: number;
  compareAtPrice?: number;
  costPrice: number;
  currency: string;
  taxRate: number;
  taxInclusive: boolean;
  stockQuantity: number;
  stockStatus: StockStatus;
  weight: number;
  weightUnit: string;
  dimensions?: {
    length: number;
    width: number;
    height: number;
    unit: string;
  };
  images: ProductImage[];
  categoryId: string;
  categoryName: string;
  categorySlug: string;
  tags: string[];
  attributes: ProductAttribute[];
  variants: ProductVariant[];
  seo: SEOData;
  isActive: boolean;
  isFeatured: boolean;
  isNew: boolean;
  rating: number;
  reviewCount: number;
  salesCount: number;
  createdAt: string;
  updatedAt: string;
}

export type StockStatus = 'in_stock' | 'out_of_stock' | 'pre_order' | 'back_order';

export interface ProductImage {
  id: string;
  url: string;
  alt: string;
  position: number;
  isPrimary: boolean;
}

export interface ProductAttribute {
  id: string;
  name: string;
  values: string[];
  displayType: 'select' | 'color' | 'image' | 'text';
}

export interface ProductVariant {
  id: string;
  sku: string;
  name: string;
  price: number;
  compareAtPrice?: number;
  stockQuantity: number;
  stockStatus: StockStatus;
  weight: number;
  images: string[];
  attributeValues: Record<string, string>;
  barcode?: string;
  isActive: boolean;
}

export interface SEOData {
  title: string;
  description: string;
  keywords: string[];
  ogImage?: string;
}

export interface StoreCategory {
  id: string;
  name: string;
  slug: string;
  description: string;
  imageUrl?: string;
  parentId?: string;
  parentName?: string;
  displayOrder: number;
  productCount: number;
  isActive: boolean;
  children?: StoreCategory[];
  breadcrumbs: BreadcrumbItem[];
}

export interface BreadcrumbItem {
  id: string;
  name: string;
  slug: string;
}

export interface StoreCart {
  id: string;
  customerId?: string;
  sessionId: string;
  items: StoreCartItem[];
  subtotal: number;
  totalDiscount: number;
  totalTax: number;
  shippingCost: number;
  total: number;
  itemCount: number;
  totalQuantity: number;
  couponCode?: string;
  couponDiscount?: number;
  currency: string;
  createdAt: string;
  updatedAt: string;
  expiresAt: string;
}

export interface StoreCartItem {
  id: string;
  productId: string;
  productName: string;
  productSlug: string;
  productImage: string;
  variantId?: string;
  variantName?: string;
  sku: string;
  quantity: number;
  unitPrice: number;
  originalPrice: number;
  discountAmount: number;
  taxAmount: number;
  subtotal: number;
  total: number;
  maxQuantity: number;
  stockStatus: StockStatus;
  isAvailable: boolean;
  attributes: Record<string, string>;
}

export interface StoreOrder {
  id: string;
  orderNumber: string;
  customerId?: string;
  customerEmail: string;
  customerName: string;
  customerPhone?: string;
  status: OrderStatus;
  paymentStatus: PaymentStatus;
  fulfillmentStatus: FulfillmentStatus;
  items: StoreOrderItem[];
  subtotal: number;
  discountTotal: number;
  taxTotal: number;
  shippingTotal: number;
  total: number;
  currency: string;
  shippingAddress: ShippingAddress;
  billingAddress: ShippingAddress;
  shippingMethod: ShippingMethod;
  paymentMethod: PaymentMethod;
  payments: StorePayment[];
  fulfillments: StoreFulfillment[];
  notes: string;
  customerNotes?: string;
  internalNotes?: string;
  couponCode?: string;
  couponDiscount?: number;
  ipAddress?: string;
  userAgent?: string;
  source: 'web' | 'mobile' | 'pos' | 'api';
  createdAt: string;
  updatedAt: string;
  paidAt?: string;
  shippedAt?: string;
  deliveredAt?: string;
  cancelledAt?: string;
  refundedAt?: string;
}

export type OrderStatus = 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'refunded' | 'partially_refunded';
export type PaymentStatus = 'pending' | 'authorized' | 'paid' | 'partially_paid' | 'refunded' | 'failed' | 'cancelled';
export type FulfillmentStatus = 'unfulfilled' | 'partial' | 'fulfilled' | 'returned' | 'restocked';

export interface StoreOrderItem {
  id: string;
  productId: string;
  productName: string;
  productSlug: string;
  productImage: string;
  variantId?: string;
  variantName?: string;
  sku: string;
  quantity: number;
  unitPrice: number;
  originalPrice: number;
  discountAmount: number;
  taxAmount: number;
  subtotal: number;
  total: number;
  attributes: Record<string, string>;
  fulfillments: OrderItemFulfillment[];
}

export interface OrderItemFulfillment {
  fulfillmentId: string;
  quantity: number;
}

export interface ShippingAddress {
  firstName: string;
  lastName: string;
  company?: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  countryCode: string;
  phone: string;
}

export interface ShippingMethod {
  id: string;
  name: string;
  description: string;
  price: number;
  estimatedDays: string;
  isActive: boolean;
}

export interface StorePayment {
  id: string;
  method: PaymentMethod;
  amount: number;
  currency: string;
  status: PaymentStatus;
  transactionId?: string;
  gatewayResponse?: Record<string, any>;
  processedAt?: string;
  failureReason?: string;
}

export type PaymentMethod = 'cash_on_delivery' | 'bank_transfer' | 'credit_card' | 'debit_card' | 'mobile_money' | 'e_wallet' | 'installment';

export interface StoreFulfillment {
  id: string;
  orderId: string;
  status: FulfillmentStatus;
  trackingNumber?: string;
  trackingUrl?: string;
  carrier?: string;
  service?: string;
  items: FulfillmentItem[];
  shippedAt?: string;
  deliveredAt?: string;
  estimatedDeliveryAt?: string;
  shippingLabelUrl?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FulfillmentItem {
  orderItemId: string;
  productName: string;
  quantity: number;
}

export interface Customer {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  dateOfBirth?: string;
  gender?: 'male' | 'female' | 'other';
  isGuest: boolean;
  addresses: CustomerAddress[];
  defaultShippingAddressId?: string;
  defaultBillingAddressId?: string;
  ordersCount: number;
  totalSpent: number;
  totalRefunded: number;
  averageOrderValue: number;
  lastOrderAt?: string;
  tags: string[];
  notes?: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerAddress {
  id: string;
  firstName: string;
  lastName: string;
  company?: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  countryCode: string;
  phone: string;
  isDefaultShipping: boolean;
  isDefaultBilling: boolean;
}

export interface ProductReview {
  id: string;
  productId: string;
  customerId?: string;
  customerName: string;
  rating: number;
  title: string;
  content: string;
  isVerifiedPurchase: boolean;
  helpfulCount: number;
  notHelpfulCount: number;
  status: ReviewStatus;
  images?: string[];
  reply?: ReviewReply;
  createdAt: string;
  updatedAt: string;
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected';

export interface ReviewReply {
  content: string;
  repliedBy: string;
  repliedAt: string;
}

export interface WishlistItem {
  id: string;
  productId: string;
  productName: string;
  productSlug: string;
  productImage: string;
  unitPrice: number;
  addedAt: string;
}

export interface StoreCoupon {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: 'percentage' | 'fixed_amount' | 'free_shipping' | 'buy_x_get_y';
  value: number;
  minOrderAmount?: number;
  maxDiscountAmount?: number;
  usageLimit?: number;
  usageCount: number;
  usageLimitPerCustomer?: number;
  startDate: string;
  endDate: string;
  applicableProducts?: string[];
  applicableCategories?: string[];
  excludedProducts?: string[];
  excludedCategories?: string[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface EcommerceKPI {
  todayOrders: number;
  todayRevenue: number;
  todayVisitors: number;
  todayConversionRate: number;
  weekOrders: number;
  weekRevenue: number;
  monthOrders: number;
  monthRevenue: number;
  averageOrderValue: number;
  topProducts: TopSellingProduct[];
  topCategories: TopCategory[];
  salesByHour: HourlySale[];
  salesByDay: DailySale[];
  abandonedCarts: number;
  abandonedCartValue: number;
  returnRate: number;
  customerCount: number;
  repeatCustomerRate: number;
}

export interface TopSellingProduct {
  productId: string;
  productName: string;
  productImage: string;
  quantity: number;
  revenue: number;
}

export interface TopCategory {
  categoryId: string;
  categoryName: string;
  orderCount: number;
  revenue: number;
}

export interface HourlySale {
  hour: number;
  orders: number;
  revenue: number;
  visitors: number;
}

export interface DailySale {
  date: string;
  orders: number;
  revenue: number;
  visitors: number;
}

export interface SearchFilters {
  category?: string;
  priceMin?: number;
  priceMax?: number;
  rating?: number;
  inStock?: boolean;
  sortBy: 'relevance' | 'price_asc' | 'price_desc' | 'newest' | 'bestselling' | 'rating';
}

