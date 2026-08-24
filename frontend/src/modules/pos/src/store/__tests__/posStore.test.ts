import { usePOSStore } from '../posStore';
import type { POSProduct, AppliedDiscount, POSSale, POSShift, POSRegister, POSCategory } from '../../types/pos';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  default: {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
  },
}));

describe('POS Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    usePOSStore.setState({
      cart: {
        items: [],
        subtotal: 0,
        totalDiscount: 0,
        totalTax: 0,
        total: 0,
        itemCount: 0,
        totalQuantity: 0,
        appliedDiscounts: [],
      },
      currentSale: null,
      suspendedSales: [],
      currentShift: null,
      shiftHistory: [],
      currentRegister: null,
      availableRegisters: [],
      products: [],
      categories: [],
      selectedCategory: null,
      searchQuery: '',
      isLoading: false,
      error: null,
      showPaymentModal: false,
      showShiftModal: false,
    });
  });

  describe('Cart Operations', () => {
    const mockProduct: POSProduct = {
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
    };

    it('should add item to empty cart', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 2);

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(1);
      expect(cart.items[0].productId).toBe('product-1');
      expect(cart.items[0].quantity).toBe(2);
      expect(cart.items[0].unitPrice).toBe(100);
      expect(cart.subtotal).toBe(200);
      expect(cart.totalQuantity).toBe(2);
    });

    it('should update quantity when adding same product', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 1);
      state.addToCart(mockProduct, 2);

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(1);
      expect(cart.items[0].quantity).toBe(3);
      expect(cart.subtotal).toBe(300);
    });

    it('should add item with variant', () => {
      const productWithVariant: POSProduct = {
        ...mockProduct,
        variants: [
          {
            id: 'variant-1',
            name: 'Large',
            sku: 'SKU-001-L',
            price: 120,
            stockQuantity: 50,
            attributes: { size: 'L' },
          },
        ],
      };

      const state = usePOSStore.getState();
      state.addToCart(productWithVariant, 1, 'variant-1');

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(1);
      expect(cart.items[0].variantId).toBe('variant-1');
      expect(cart.items[0].unitPrice).toBe(120);
    });

    it('should update cart item quantity', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 5);
      state.updateCartItemQuantity(usePOSStore.getState().cart.items[0].id, 3);

      const cart = usePOSStore.getState().cart;
      expect(cart.items[0].quantity).toBe(3);
      expect(cart.subtotal).toBe(300);
    });

    it('should remove item from cart when quantity is 0 or less', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 2);
      state.updateCartItemQuantity(usePOSStore.getState().cart.items[0].id, 0);

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(0);
    });

    it('should remove item from cart', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 2);
      const itemId = usePOSStore.getState().cart.items[0].id;
      state.removeFromCart(itemId);

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(0);
      expect(cart.subtotal).toBe(0);
    });

    it('should clear cart', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 3);
      state.clearCart();

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(0);
      expect(cart.subtotal).toBe(0);
      expect(cart.total).toBe(0);
    });

    it('should calculate tax correctly for non-tax-inclusive products', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 2);

      const cart = usePOSStore.getState().cart;
      expect(cart.subtotal).toBe(200);
      expect(cart.totalTax).toBe(20); // 10% of 200
      expect(cart.total).toBe(220);
    });

    it('should handle tax-inclusive products correctly', () => {
      const taxInclusiveProduct: POSProduct = {
        ...mockProduct,
        taxInclusive: true,
      };

      const state = usePOSStore.getState();
      state.addToCart(taxInclusiveProduct, 2);

      const cart = usePOSStore.getState().cart;
      expect(cart.subtotal).toBe(200);
      expect(cart.totalTax).toBe(0);
      expect(cart.total).toBe(200);
    });

    it('should apply discount to cart', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 2);

      const discount: AppliedDiscount = {
        id: 'discount-1',
        name: 'Test Discount',
        type: 'fixed_amount',
        value: 20,
        amount: 20,
      };

      state.applyDiscount(discount);

      const cart = usePOSStore.getState().cart;
      expect(cart.appliedDiscounts.length).toBe(1);
      expect(cart.totalDiscount).toBe(20);
      expect(cart.total).toBe(200); // 220 - 20
    });

    it('should remove discount from cart', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 2);

      const discount: AppliedDiscount = {
        id: 'discount-1',
        name: 'Test Discount',
        type: 'fixed_amount',
        value: 20,
        amount: 20,
      };

      state.applyDiscount(discount);
      state.removeDiscount('discount-1');

      const cart = usePOSStore.getState().cart;
      expect(cart.appliedDiscounts.length).toBe(0);
      expect(cart.totalDiscount).toBe(0);
    });

    it('should set customer info', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 1);
      state.setCustomer('customer-1', 'John Doe');

      const cart = usePOSStore.getState().cart;
      expect(cart.customerId).toBe('customer-1');
      expect(cart.customerName).toBe('John Doe');
    });

    it('should set cart notes', () => {
      const state = usePOSStore.getState();
      state.addToCart(mockProduct, 1);
      state.setCartNotes('Special instructions');

      const cart = usePOSStore.getState().cart;
      expect(cart.notes).toBe('Special instructions');
    });
  });

  describe('Suspended Sales', () => {
    const mockSale: POSSale = {
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
      status: 'draft',
      cashierId: 'cashier-1',
      cashierName: 'John',
      registerId: 'register-1',
      registerName: 'Main Register',
      shiftId: 'shift-1',
      receiptPrinted: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    it('should suspend a sale', () => {
      const state = usePOSStore.getState();
      state.suspendSale(mockSale);

      const suspendedSales = usePOSStore.getState().suspendedSales;
      expect(suspendedSales.length).toBe(1);
      expect(suspendedSales[0].id).toBe('sale-1');
    });

    it('should resume a suspended sale', () => {
      const state = usePOSStore.getState();
      state.suspendSale(mockSale);
      state.resumeSale('sale-1');

      const currentSale = usePOSStore.getState().currentSale;
      const suspendedSales = usePOSStore.getState().suspendedSales;
      expect(currentSale?.id).toBe('sale-1');
      expect(suspendedSales.length).toBe(0);
    });

    it('should remove suspended sale', () => {
      const state = usePOSStore.getState();
      state.suspendSale(mockSale);
      state.removeSuspendedSale('sale-1');

      const suspendedSales = usePOSStore.getState().suspendedSales;
      expect(suspendedSales.length).toBe(0);
    });
  });

  describe('Shift Management', () => {
    const mockShift: POSShift = {
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
      status: 'closed',
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

    it('should set current shift', () => {
      const state = usePOSStore.getState();
      state.setCurrentShift(mockShift);

      const currentShift = usePOSStore.getState().currentShift;
      expect(currentShift?.id).toBe('shift-1');
    });

    it('should add shift to history', () => {
      const state = usePOSStore.getState();
      state.addShiftToHistory(mockShift);

      const shiftHistory = usePOSStore.getState().shiftHistory;
      expect(shiftHistory.length).toBe(1);
      expect(shiftHistory[0].id).toBe('shift-1');
    });
  });

  describe('Register Management', () => {
    const mockRegister: POSRegister = {
      id: 'register-1',
      name: 'Main Register',
      code: 'REG-001',
      location: 'Store Front',
      isActive: true,
      cashDrawerConnected: true,
      receiptTemplate: 'default',
    };

    it('should set current register', () => {
      const state = usePOSStore.getState();
      state.setCurrentRegister(mockRegister);

      const currentRegister = usePOSStore.getState().currentRegister;
      expect(currentRegister?.id).toBe('register-1');
    });

    it('should set available registers', () => {
      const state = usePOSStore.getState();
      const registers: POSRegister[] = [mockRegister, { ...mockRegister, id: 'register-2', code: 'REG-002' }];
      state.setAvailableRegisters(registers);

      const availableRegisters = usePOSStore.getState().availableRegisters;
      expect(availableRegisters.length).toBe(2);
    });
  });

  describe('Products & Categories', () => {
    const mockProduct: POSProduct = {
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
    };

    const mockCategory: POSCategory = {
      id: 'cat-1',
      name: 'Test Category',
      code: 'CAT-001',
      color: '#FF0000',
      productCount: 10,
      isActive: true,
      displayOrder: 1,
    };

    it('should set products', () => {
      const state = usePOSStore.getState();
      state.setProducts([mockProduct]);

      const products = usePOSStore.getState().products;
      expect(products.length).toBe(1);
      expect(products[0].id).toBe('product-1');
    });

    it('should set categories', () => {
      const state = usePOSStore.getState();
      state.setCategories([mockCategory]);

      const categories = usePOSStore.getState().categories;
      expect(categories.length).toBe(1);
      expect(categories[0].id).toBe('cat-1');
    });

    it('should set selected category', () => {
      const state = usePOSStore.getState();
      state.setSelectedCategory('cat-1');

      const selectedCategory = usePOSStore.getState().selectedCategory;
      expect(selectedCategory).toBe('cat-1');
    });

    it('should set search query', () => {
      const state = usePOSStore.getState();
      state.setSearchQuery('test product');

      const searchQuery = usePOSStore.getState().searchQuery;
      expect(searchQuery).toBe('test product');
    });
  });

  describe('UI State', () => {
    it('should set loading state', () => {
      const state = usePOSStore.getState();
      state.setIsLoading(true);

      expect(usePOSStore.getState().isLoading).toBe(true);
    });

    it('should set error', () => {
      const state = usePOSStore.getState();
      state.setError('Test error message');

      expect(usePOSStore.getState().error).toBe('Test error message');
    });

    it('should toggle payment modal', () => {
      const state = usePOSStore.getState();
      state.setShowPaymentModal(true);

      expect(usePOSStore.getState().showPaymentModal).toBe(true);
    });

    it('should toggle shift modal', () => {
      const state = usePOSStore.getState();
      state.setShowShiftModal(true);

      expect(usePOSStore.getState().showShiftModal).toBe(true);
    });
  });

  describe('Cart Recalculation', () => {
    it('should recalculate cart with multiple items', () => {
      const state = usePOSStore.getState();
      
      const product1: POSProduct = {
        id: 'product-1',
        sku: 'SKU-001',
        name: 'Product 1',
        categoryId: 'cat-1',
        categoryName: 'Category 1',
        price: 100,
        costPrice: 50,
        taxRate: 10,
        taxInclusive: false,
        stockQuantity: 100,
        unit: 'pcs',
        isActive: true,
      };

      const product2: POSProduct = {
        id: 'product-2',
        sku: 'SKU-002',
        name: 'Product 2',
        categoryId: 'cat-1',
        categoryName: 'Category 1',
        price: 200,
        costPrice: 100,
        taxRate: 5,
        taxInclusive: false,
        stockQuantity: 50,
        unit: 'pcs',
        isActive: true,
      };

      state.addToCart(product1, 2);
      state.addToCart(product2, 1);

      const cart = usePOSStore.getState().cart;
      expect(cart.items.length).toBe(2);
      expect(cart.subtotal).toBe(400); // 200 + 200
      expect(cart.totalQuantity).toBe(3);
    });

    it('should handle multiple discounts', () => {
      const state = usePOSStore.getState();
      state.addToCart({
        id: 'product-1',
        sku: 'SKU-001',
        name: 'Test Product',
        categoryId: 'cat-1',
        categoryName: 'Test Category',
        price: 100,
        costPrice: 50,
        taxRate: 0,
        taxInclusive: false,
        stockQuantity: 100,
        unit: 'pcs',
        isActive: true,
      }, 2);

      const discount1: AppliedDiscount = {
        id: 'discount-1',
        name: 'Discount 1',
        type: 'fixed_amount',
        value: 10,
        amount: 10,
      };

      const discount2: AppliedDiscount = {
        id: 'discount-2',
        name: 'Discount 2',
        type: 'fixed_amount',
        value: 20,
        amount: 20,
      };

      state.applyDiscount(discount1);
      state.applyDiscount(discount2);

      const cart = usePOSStore.getState().cart;
      expect(cart.appliedDiscounts.length).toBe(2);
      expect(cart.totalDiscount).toBe(30);
    });
  });
});
