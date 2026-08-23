import { useEcommerceStore } from '../ecommerceStore';

// Mock AsyncStorage and zustand persist
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

describe('Ecommerce Store', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store state before each test
    useEcommerceStore.setState({
      products: [],
      featuredProducts: [],
      newProducts: [],
      selectedProduct: null,
      categories: [],
      selectedCategory: null,
      cart: null,
      orders: [],
      selectedOrder: null,
      customer: null,
      isAuthenticated: false,
      wishlist: [],
      searchQuery: '',
      searchFilters: { sortBy: 'relevance' },
      searchResults: [],
      isLoading: false,
      error: null,
      showCartModal: false,
      showCheckoutModal: false,
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = useEcommerceStore.getState();
      
      expect(state.products).toEqual([]);
      expect(state.featuredProducts).toEqual([]);
      expect(state.newProducts).toEqual([]);
      expect(state.selectedProduct).toBeNull();
      expect(state.categories).toEqual([]);
      expect(state.cart).toBeNull();
      expect(state.orders).toEqual([]);
      expect(state.customer).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.wishlist).toEqual([]);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('product actions', () => {
    it('should set products', () => {
      const mockProducts = [
        { id: '1', name: 'Product 1', sku: 'SKU1' },
        { id: '2', name: 'Product 2', sku: 'SKU2' },
      ];

      useEcommerceStore.getState().setProducts(mockProducts as any);
      
      expect(useEcommerceStore.getState().products).toEqual(mockProducts);
    });

    it('should set featured products', () => {
      const mockProducts = [{ id: '1', name: 'Featured Product' }];

      useEcommerceStore.getState().setFeaturedProducts(mockProducts as any);
      
      expect(useEcommerceStore.getState().featuredProducts).toEqual(mockProducts);
    });

    it('should set new products', () => {
      const mockProducts = [{ id: '1', name: 'New Product' }];

      useEcommerceStore.getState().setNewProducts(mockProducts as any);
      
      expect(useEcommerceStore.getState().newProducts).toEqual(mockProducts);
    });

    it('should set selected product', () => {
      const mockProduct = { id: '1', name: 'Selected Product' };

      useEcommerceStore.getState().setSelectedProduct(mockProduct as any);
      
      expect(useEcommerceStore.getState().selectedProduct).toEqual(mockProduct);
    });

    it('should clear selected product', () => {
      useEcommerceStore.getState().setSelectedProduct({ id: '1', name: 'Product' } as any);
      useEcommerceStore.getState().setSelectedProduct(null);
      
      expect(useEcommerceStore.getState().selectedProduct).toBeNull();
    });
  });

  describe('category actions', () => {
    it('should set categories', () => {
      const mockCategories = [
        { id: '1', name: 'Category 1', slug: 'cat1' },
        { id: '2', name: 'Category 2', slug: 'cat2' },
      ];

      useEcommerceStore.getState().setCategories(mockCategories as any);
      
      expect(useEcommerceStore.getState().categories).toEqual(mockCategories);
    });

    it('should set selected category', () => {
      const mockCategory = { id: '1', name: 'Selected Category' };

      useEcommerceStore.getState().setSelectedCategory(mockCategory as any);
      
      expect(useEcommerceStore.getState().selectedCategory).toEqual(mockCategory);
    });
  });

  describe('cart actions', () => {
    it('should set cart', () => {
      const mockCart = {
        id: 'cart-1',
        items: [],
        subtotal: 0,
        total: 0,
        itemCount: 0,
      };

      useEcommerceStore.getState().setCart(mockCart as any);
      
      expect(useEcommerceStore.getState().cart).toEqual(mockCart);
    });

    it('should clear cart', () => {
      useEcommerceStore.getState().setCart({ id: 'cart-1', items: [] } as any);
      useEcommerceStore.getState().clearCart();
      
      expect(useEcommerceStore.getState().cart).toBeNull();
    });

    it('should apply coupon', () => {
      const mockCart = {
        id: 'cart-1',
        items: [],
        subtotal: 100,
        total: 100,
        couponCode: undefined,
      } as any;

      useEcommerceStore.getState().setCart(mockCart);
      useEcommerceStore.getState().applyCoupon({ code: 'SAVE10' } as any);
      
      expect(useEcommerceStore.getState().cart?.couponCode).toBe('SAVE10');
    });

    it('should remove coupon', () => {
      const mockCart = {
        id: 'cart-1',
        items: [],
        subtotal: 100,
        total: 90,
        couponCode: 'SAVE10',
        couponDiscount: 10,
      } as any;

      useEcommerceStore.getState().setCart(mockCart);
      useEcommerceStore.getState().removeCoupon();
      
      expect(useEcommerceStore.getState().cart?.couponCode).toBeUndefined();
      expect(useEcommerceStore.getState().cart?.couponDiscount).toBeUndefined();
    });
  });

  describe('order actions', () => {
    it('should set orders', () => {
      const mockOrders = [
        { id: '1', orderNumber: 'ORD-001', status: 'pending' },
        { id: '2', orderNumber: 'ORD-002', status: 'delivered' },
      ];

      useEcommerceStore.getState().setOrders(mockOrders as any);
      
      expect(useEcommerceStore.getState().orders).toEqual(mockOrders);
    });

    it('should set selected order', () => {
      const mockOrder = { id: '1', orderNumber: 'ORD-001' };

      useEcommerceStore.getState().setSelectedOrder(mockOrder as any);
      
      expect(useEcommerceStore.getState().selectedOrder).toEqual(mockOrder);
    });

    it('should add order to the beginning of orders list', () => {
      const existingOrder = { id: '1', orderNumber: 'ORD-001' };
      const newOrder = { id: '2', orderNumber: 'ORD-002' };

      useEcommerceStore.getState().setOrders([existingOrder] as any);
      useEcommerceStore.getState().addOrder(newOrder as any);
      
      const orders = useEcommerceStore.getState().orders;
      expect(orders[0]).toEqual(newOrder);
      expect(orders.length).toBe(2);
    });
  });

  describe('customer actions', () => {
    it('should set customer', () => {
      const mockCustomer = {
        id: 'cust-1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
      };

      useEcommerceStore.getState().setCustomer(mockCustomer as any);
      
      expect(useEcommerceStore.getState().customer).toEqual(mockCustomer);
    });

    it('should set authentication status', () => {
      useEcommerceStore.getState().setIsAuthenticated(true);
      
      expect(useEcommerceStore.getState().isAuthenticated).toBe(true);
    });

    it('should update customer data', () => {
      const initialCustomer = {
        id: 'cust-1',
        email: 'test@example.com',
        firstName: 'Test',
        lastName: 'User',
        phone: '1234567890',
      };

      useEcommerceStore.getState().setCustomer(initialCustomer as any);
      useEcommerceStore.getState().updateCustomer({ phone: '0987654321' });
      
      expect(useEcommerceStore.getState().customer?.phone).toBe('0987654321');
      expect(useEcommerceStore.getState().customer?.email).toBe('test@example.com');
    });
  });

  describe('wishlist actions', () => {
    it('should set wishlist', () => {
      const mockWishlist = [
        { id: '1', productId: 'prod-1', productName: 'Product 1' },
        { id: '2', productId: 'prod-2', productName: 'Product 2' },
      ];

      useEcommerceStore.getState().setWishlist(mockWishlist as any);
      
      expect(useEcommerceStore.getState().wishlist).toEqual(mockWishlist);
    });

    it('should add item to wishlist', () => {
      const newItem = { id: '1', productId: 'prod-1', productName: 'Product 1' };

      useEcommerceStore.getState().addToWishlist(newItem as any);
      
      expect(useEcommerceStore.getState().wishlist).toContainEqual(newItem);
    });

    it('should not add duplicate item to wishlist', () => {
      const item = { id: '1', productId: 'prod-1', productName: 'Product 1' };

      useEcommerceStore.getState().addToWishlist(item as any);
      useEcommerceStore.getState().addToWishlist(item as any);
      
      expect(useEcommerceStore.getState().wishlist.length).toBe(1);
    });

    it('should remove item from wishlist', () => {
      const item1 = { id: '1', productId: 'prod-1', productName: 'Product 1' };
      const item2 = { id: '2', productId: 'prod-2', productName: 'Product 2' };

      useEcommerceStore.getState().setWishlist([item1, item2] as any);
      useEcommerceStore.getState().removeFromWishlist('1');
      
      expect(useEcommerceStore.getState().wishlist.length).toBe(1);
      expect(useEcommerceStore.getState().wishlist[0].id).toBe('2');
    });

    it('should check if product is in wishlist', () => {
      const item = { id: '1', productId: 'prod-1', productName: 'Product 1' };

      useEcommerceStore.getState().setWishlist([item] as any);
      
      expect(useEcommerceStore.getState().isInWishlist('prod-1')).toBe(true);
      expect(useEcommerceStore.getState().isInWishlist('prod-2')).toBe(false);
    });
  });

  describe('search actions', () => {
    it('should set search query', () => {
      useEcommerceStore.getState().setSearchQuery('test product');
      
      expect(useEcommerceStore.getState().searchQuery).toBe('test product');
    });

    it('should set search filters', () => {
      useEcommerceStore.getState().setSearchFilters({ priceMin: 10, priceMax: 100 });
      
      expect(useEcommerceStore.getState().searchFilters.priceMin).toBe(10);
      expect(useEcommerceStore.getState().searchFilters.priceMax).toBe(100);
    });

    it('should set search results', () => {
      const mockResults = [{ id: '1', name: 'Search Result' }];

      useEcommerceStore.getState().setSearchResults(mockResults as any);
      
      expect(useEcommerceStore.getState().searchResults).toEqual(mockResults);
    });

    it('should reset search', () => {
      useEcommerceStore.getState().setSearchQuery('test');
      useEcommerceStore.getState().setSearchFilters({ priceMin: 10 });
      useEcommerceStore.getState().setSearchResults([{ id: '1' }] as any);

      useEcommerceStore.getState().resetSearch();
      
      expect(useEcommerceStore.getState().searchQuery).toBe('');
      expect(useEcommerceStore.getState().searchFilters).toEqual({ sortBy: 'relevance' });
      expect(useEcommerceStore.getState().searchResults).toEqual([]);
    });
  });

  describe('UI state actions', () => {
    it('should set loading state', () => {
      useEcommerceStore.getState().setIsLoading(true);
      
      expect(useEcommerceStore.getState().isLoading).toBe(true);
    });

    it('should set error', () => {
      useEcommerceStore.getState().setError('An error occurred');
      
      expect(useEcommerceStore.getState().error).toBe('An error occurred');
    });

    it('should clear error', () => {
      useEcommerceStore.getState().setError('An error occurred');
      useEcommerceStore.getState().setError(null);
      
      expect(useEcommerceStore.getState().error).toBeNull();
    });

    it('should toggle cart modal', () => {
      useEcommerceStore.getState().setShowCartModal(true);
      
      expect(useEcommerceStore.getState().showCartModal).toBe(true);
    });

    it('should toggle checkout modal', () => {
      useEcommerceStore.getState().setShowCheckoutModal(true);
      
      expect(useEcommerceStore.getState().showCheckoutModal).toBe(true);
    });
  });
});
