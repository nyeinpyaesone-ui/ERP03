export interface DashboardSummary {
  revenue: {
    current: number;
    previous: number;
    change: number;
    changePercent: number;
  };
  invoices: {
    total: number;
    paid: number;
    overdue: number;
    draft: number;
  };
  customers: {
    total: number;
    new: number;
    active: number;
  };
  products: {
    total: number;
    lowStock: number;
    outOfStock: number;
  };
  orders: {
    total: number;
    pending: number;
    completed: number;
  };
  cashFlow: {
    inflow: number;
    outflow: number;
    net: number;
  };
  period: string;
}

export interface RevenueAnalytics {
  period: string;
  data: Array<{
    date: string;
    revenue: number;
    invoices: number;
    orders: number;
  }>;
  total: number;
  average: number;
  growth: number;
}

export interface KPIMetric {
  value: number;
  target: number;
  achievement: number;
}

export interface KPIMetrics {
  revenue: KPIMetric;
  profitMargin: KPIMetric;
  customerAcquisition: KPIMetric;
  inventoryTurnover: KPIMetric;
  averageOrderValue: KPIMetric;
  collectionPeriod: KPIMetric;
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    color: string;
  }>;
}

export interface ActivityItem {
  id: string;
  type: 'invoice_created' | 'invoice_paid' | 'invoice_overdue' | 'contact_created' | 'order_placed' | 'product_low_stock' | 'payment_received' | 'user_login' | 'system';
  title: string;
  description: string;
  entityType: string;
  entityId: string;
  userName: string;
  userAvatar: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface TopProduct {
  productId: string;
  productName: string;
  sku: string;
  quantitySold: number;
  revenue: number;
  image: string;
}

export interface TopCustomer {
  contactId: string;
  contactName: string;
  email: string;
  totalRevenue: number;
  invoiceCount: number;
  lastOrder: string;
}

export interface DashboardPeriod {
  label: string;
  value: string;
}

export interface DashboardFilter {
  period: string;
  compareWith: 'previous_period' | 'previous_year';
  dateRange?: { from: string; to: string };
}

export interface ForecastData {
  type: string;
  horizon: string;
  data: Array<{
    date: string;
    predicted: number;
    lowerBound: number;
    upperBound: number;
    confidence: number;
  }>;
  accuracy: number;
  trend: 'up' | 'down' | 'stable';
}

export interface AIInsight {
  id: string;
  type: 'trend' | 'anomaly' | 'opportunity' | 'risk' | 'recommendation';
  title: string;
  description: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  module: string;
  metric: string;
  currentValue: number;
  previousValue: number;
  changePercent: number;
  suggestedAction: string;
  createdAt: string;
}

export interface InventoryStats {
  totalProducts: number;
  totalStockValue: number;
  lowStockCount: number;
  outOfStockCount: number;
  warehouseCount: number;
  categoryCount: number;
  topCategories: Array<{
    category: string;
    productCount: number;
    stockValue: number;
  }>;
}

export interface SalesForecast {
  productId?: string;
  horizon: string;
  data: Array<{
    date: string;
    predicted: number;
    lowerBound: number;
    upperBound: number;
  }>;
  accuracy: number;
}

