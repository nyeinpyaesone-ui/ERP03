import axios from 'axios';
import {
  posProductAPI,
  posCategoryAPI,
  posSaleAPI,
  posShiftAPI,
  posRegisterAPI,
  posKPIAPI,
} from '../posApi';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock env config
jest.mock('../../config/env', () => ({
  env: {
    apiUrl: 'http://test-api.com',
  },
}));

describe('POS API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Product API', () => {
    const mockProducts = [
      {
        id: 'product-1',
        sku: 'SKU-001',
        name: 'Test Product',
        categoryId: 'cat-1',
        categoryName: 'Test Category',
        price: 100,
        costPrice: 50,
        taxRate: 10,
        taxInclusive: false,
        stockQuantity: 100,
        unit: 'pcs',
        isActive: true,
      },
    ];

    it('should get all products', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockProducts });

      const result = await posProductAPI.getAll({ category: 'cat-1', search: 'test' });

      expect(mockedAxios.get).toHaveBeenCalledWith('/products', {
        params: { category: 'cat-1', search: 'test' },
      });
      expect(result).toEqual(mockProducts);
    });

    it('should get product by barcode', async () => {
      const mockProduct = mockProducts[0];
      mockedAxios.get.mockResolvedValueOnce({ data: mockProduct });

      const result = await posProductAPI.getByBarcode('123456');

      expect(mockedAxios.get).toHaveBeenCalledWith('/products/barcode/123456');
      expect(result).toEqual(mockProduct);
    });

    it('should get product by id', async () => {
      const mockProduct = mockProducts[0];
      mockedAxios.get.mockResolvedValueOnce({ data: mockProduct });

      const result = await posProductAPI.getById('product-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/products/product-1');
      expect(result).toEqual(mockProduct);
    });

    it('should check stock', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: { available: true, quantity: 50 } });

      const result = await posProductAPI.checkStock('product-1', 5, 'variant-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/products/product-1/stock', {
        params: { quantity: 5, variantId: 'variant-1' },
      });
      expect(result).toEqual({ available: true, quantity: 50 });
    });
  });

  describe('Category API', () => {
    const mockCategories = [
      {
        id: 'cat-1',
        name: 'Category 1',
        code: 'CAT-001',
        color: '#FF0000',
        productCount: 10,
        isActive: true,
        displayOrder: 1,
      },
    ];

    it('should get all categories', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockCategories });

      const result = await posCategoryAPI.getAll();

      expect(mockedAxios.get).toHaveBeenCalledWith('/categories');
      expect(result).toEqual(mockCategories);
    });

    it('should get category by id', async () => {
      const mockCategory = mockCategories[0];
      mockedAxios.get.mockResolvedValueOnce({ data: mockCategory });

      const result = await posCategoryAPI.getById('cat-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/categories/cat-1');
      expect(result).toEqual(mockCategory);
    });
  });

  describe('Sale API', () => {
    const mockSale = {
      id: 'sale-1',
      saleNumber: 'SALE-001',
      cart: {
        items: [],
        subtotal: 100,
        totalDiscount: 0,
        totalTax: 10,
        total: 110,
        itemCount: 1,
        totalQuantity: 1,
        appliedDiscounts: [],
      },
      payments: [],
      status: 'completed' as const,
      cashierId: 'cashier-1',
      cashierName: 'John',
      registerId: 'register-1',
      registerName: 'Main Register',
      shiftId: 'shift-1',
      receiptPrinted: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    it('should create a sale', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: mockSale });

      const result = await posSaleAPI.create({
        cart: mockSale.cart,
        registerId: 'register-1',
        shiftId: 'shift-1',
        customerId: 'customer-1',
      });

      expect(mockedAxios.post).toHaveBeenCalledWith('/sales', {
        cart: mockSale.cart,
        registerId: 'register-1',
        shiftId: 'shift-1',
        customerId: 'customer-1',
      });
      expect(result).toEqual(mockSale);
    });

    it('should get all sales', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: [mockSale] });

      const result = await posSaleAPI.getAll({
        shiftId: 'shift-1',
        status: 'completed',
      });

      expect(mockedAxios.get).toHaveBeenCalledWith('/sales', {
        params: { shiftId: 'shift-1', status: 'completed' },
      });
      expect(result).toEqual([mockSale]);
    });

    it('should get sale by id', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockSale });

      const result = await posSaleAPI.getById('sale-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/sales/sale-1');
      expect(result).toEqual(mockSale);
    });

    it('should add payment to sale', async () => {
      const paymentData = {
        method: 'cash' as const,
        amount: 110,
        receivedAmount: 120,
        changeAmount: 10,
      };

      mockedAxios.post.mockResolvedValueOnce({ data: { ...mockSale, payments: [paymentData] } });

      const result = await posSaleAPI.addPayment('sale-1', paymentData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/sales/sale-1/payments', paymentData);
      expect(result.payments).toContainEqual(paymentData);
    });

    it('should complete a sale', async () => {
      mockedAxios.patch.mockResolvedValueOnce({ data: { ...mockSale, status: 'completed' } });

      const result = await posSaleAPI.completeSale('sale-1');

      expect(mockedAxios.patch).toHaveBeenCalledWith('/sales/sale-1/complete');
      expect(result.status).toBe('completed');
    });

    it('should refund a sale', async () => {
      const refundData = { amount: 50, reason: 'Customer request' };
      mockedAxios.post.mockResolvedValueOnce({ data: { ...mockSale, status: 'refunded', refundAmount: 50 } });

      const result = await posSaleAPI.refund('sale-1', refundData);

      expect(mockedAxios.post).toHaveBeenCalledWith('/sales/sale-1/refund', refundData);
      expect(result.status).toBe('refunded');
    });

    it('should cancel a sale', async () => {
      mockedAxios.patch.mockResolvedValueOnce({ data: { ...mockSale, status: 'cancelled' } });

      const result = await posSaleAPI.cancel('sale-1', 'Customer changed mind');

      expect(mockedAxios.patch).toHaveBeenCalledWith('/sales/sale-1/cancel', {
        reason: 'Customer changed mind',
      });
      expect(result.status).toBe('cancelled');
    });

    it('should get receipt', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: { receiptUrl: 'http://receipt.com/123' } });

      const result = await posSaleAPI.getReceipt('sale-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/sales/sale-1/receipt');
      expect(result).toEqual({ receiptUrl: 'http://receipt.com/123' });
    });

    it('should print receipt', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: { success: true } });

      const result = await posSaleAPI.printReceipt('sale-1');

      expect(mockedAxios.post).toHaveBeenCalledWith('/sales/sale-1/print-receipt');
      expect(result).toEqual({ success: true });
    });
  });

  describe('Shift API', () => {
    const mockShift = {
      id: 'shift-1',
      shiftNumber: 'SHIFT-001',
      cashierId: 'cashier-1',
      cashierName: 'John Doe',
      registerId: 'register-1',
      registerName: 'Main Register',
      openingAmount: 100,
      closingAmount: 500,
      expectedAmount: 480,
      difference: 20,
      status: 'closed' as const,
      openedAt: new Date().toISOString(),
      closedAt: new Date().toISOString(),
      salesCount: 10,
      refundsCount: 1,
      totalSales: 500,
      totalRefunds: 20,
      totalCashPayments: 400,
      totalCardPayments: 100,
      totalOtherPayments: 0,
    };

    it('should open a shift', async () => {
      mockedAxios.post.mockResolvedValueOnce({ data: mockShift });

      const result = await posShiftAPI.open({
        registerId: 'register-1',
        cashierId: 'cashier-1',
        openingAmount: 100,
        notes: 'Starting morning shift',
      });

      expect(mockedAxios.post).toHaveBeenCalledWith('/shifts/open', {
        registerId: 'register-1',
        cashierId: 'cashier-1',
        openingAmount: 100,
        notes: 'Starting morning shift',
      });
      expect(result).toEqual(mockShift);
    });

    it('should close a shift', async () => {
      mockedAxios.patch.mockResolvedValueOnce({ data: { ...mockShift, status: 'counted' } });

      const result = await posShiftAPI.close('shift-1', {
        closingAmount: 500,
        countedAmount: 495,
        notes: 'Ending shift',
      });

      expect(mockedAxios.patch).toHaveBeenCalledWith('/shifts/shift-1/close', {
        closingAmount: 500,
        countedAmount: 495,
        notes: 'Ending shift',
      });
      expect(result.status).toBe('counted');
    });

    it('should get current shift', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockShift });

      const result = await posShiftAPI.getCurrent('register-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/shifts/current/register-1');
      expect(result).toEqual(mockShift);
    });

    it('should get shift history', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: [mockShift] });

      const result = await posShiftAPI.getHistory({
        cashierId: 'cashier-1',
        dateFrom: '2024-01-01',
      });

      expect(mockedAxios.get).toHaveBeenCalledWith('/shifts', {
        params: { cashierId: 'cashier-1', dateFrom: '2024-01-01' },
      });
      expect(result).toEqual([mockShift]);
    });

    it('should get shift by id', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockShift });

      const result = await posShiftAPI.getById('shift-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/shifts/shift-1');
      expect(result).toEqual(mockShift);
    });
  });

  describe('Register API', () => {
    const mockRegister = {
      id: 'register-1',
      name: 'Main Register',
      code: 'REG-001',
      location: 'Store Front',
      isActive: true,
      cashDrawerConnected: true,
      receiptTemplate: 'default',
    };

    it('should get all registers', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: [mockRegister] });

      const result = await posRegisterAPI.getAll();

      expect(mockedAxios.get).toHaveBeenCalledWith('/registers');
      expect(result).toEqual([mockRegister]);
    });

    it('should get register by id', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockRegister });

      const result = await posRegisterAPI.getById('register-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/registers/register-1');
      expect(result).toEqual(mockRegister);
    });

    it('should update register', async () => {
      const updatedRegister = { ...mockRegister, location: 'New Location' };
      mockedAxios.put.mockResolvedValueOnce({ data: updatedRegister });

      const result = await posRegisterAPI.update('register-1', { location: 'New Location' });

      expect(mockedAxios.put).toHaveBeenCalledWith('/registers/register-1', {
        location: 'New Location',
      });
      expect(result).toEqual(updatedRegister);
    });
  });

  describe('KPI API', () => {
    const mockKPI = {
      todaySales: 5000,
      todayTransactions: 50,
      todayAverageTicket: 100,
      todayItemsSold: 200,
      todayRefunds: 2,
      currentShiftSales: 1000,
      currentShiftTransactions: 10,
      topProducts: [
        { productId: 'product-1', productName: 'Product 1', quantity: 20, revenue: 2000 },
      ],
      paymentMethodBreakdown: [
        { method: 'cash' as const, amount: 3000, count: 30, percentage: 60 },
        { method: 'card' as const, amount: 2000, count: 20, percentage: 40 },
      ],
      hourlySales: [
        { hour: 9, sales: 500, transactions: 5 },
        { hour: 10, sales: 800, transactions: 8 },
      ],
    };

    it('should get dashboard KPI', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: mockKPI });

      const result = await posKPIAPI.getDashboard('register-1', 'shift-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/kpi/dashboard', {
        params: { registerId: 'register-1', shiftId: 'shift-1' },
      });
      expect(result).toEqual(mockKPI);
    });

    it('should get daily report', async () => {
      mockedAxios.get.mockResolvedValueOnce({ data: { date: '2024-01-01', totalSales: 5000 } });

      const result = await posKPIAPI.getDailyReport('2024-01-01', 'register-1');

      expect(mockedAxios.get).toHaveBeenCalledWith('/reports/daily', {
        params: { date: '2024-01-01', registerId: 'register-1' },
      });
      expect(result).toEqual({ date: '2024-01-01', totalSales: 5000 });
    });

    it('should get sales report', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: {
          period: '2024-01',
          totalSales: 50000,
          groupedBy: 'month',
        },
      });

      const result = await posKPIAPI.getSalesReport({
        dateFrom: '2024-01-01',
        dateTo: '2024-01-31',
        groupBy: 'month',
      });

      expect(mockedAxios.get).toHaveBeenCalledWith('/reports/sales', {
        params: {
          dateFrom: '2024-01-01',
          dateTo: '2024-01-31',
          groupBy: 'month',
        },
      });
      expect(result).toEqual({
        period: '2024-01',
        totalSales: 50000,
        groupedBy: 'month',
      });
    });
  });
});
