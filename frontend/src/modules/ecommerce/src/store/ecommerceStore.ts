/**
 * Enterprise E-commerce Store
 * Uses standardized store factory with async action tracking
 * 
 * @module modules/ecommerce/store/ecommerceStore
 */

import { createStore, createSlice } from '../../../core/store';
import {
  StoreProduct,
  StoreCategory,
  StoreCart,
  StoreCartItem,
  StoreOrder,
  Customer,
  WishlistItem,
  StoreCoupon,
  SearchFilters,
} from '../types/ecommerce';

interface EcommerceState {
  // Products
  products: StoreProduct[];
  featuredProducts: StoreProduct[];
  newProducts: StoreProduct[];
  selectedProduct: StoreProduct | null;

  // Categories
  categories: StoreCategory[];
  selectedCategory: StoreCategory | null;

  // Cart
  cart: StoreCart | null;

  // Orders
  orders: StoreOrder[];
  selectedOrder: StoreOrder | null;

  // Customer
  customer: Customer | null;
  isAuthenticated: boolean;

  // Wishlist
  wishlist: WishlistItem[];

  // Search & Filters
  searchQuery: string;
  searchFilters: SearchFilters;
  searchResults: StoreProduct[];

  // UI State
  showCartModal: boolean;
  showCheckoutModal: boolean;

  // Required base state for async tracking
  _actions: Record<string, 'idle' | 'loading' | 'success' | 'error'>;
  _errors: Record<string, string | null>;
}

interface EcommerceActions {
  // Product actions
  setProducts: (products: StoreProduct[]) => void;
  setFeaturedProducts: (products: StoreProduct[]) => void;
  setNewProducts: (products: StoreProduct[]) => void;
  setSelectedProduct: (product: StoreProduct | null) => void;

  // Category actions
  setCategories: (categories: StoreCategory[]) => void;
  setSelectedCategory: (category: StoreCategory | null) => void;

  // Cart actions
  setCart: (cart: StoreCart | null) => void;
  addToCart: (item: StoreCartItem) => void;
  updateCartItem: (itemId: string, quantity: number) => void;
  removeFromCart: (itemId: string) => void;
  clearCart: () => void;
  applyCoupon: (coupon: StoreCoupon) => void;
  removeCoupon: () => void;
  recalculateCart: (items: StoreCartItem[]) => void;

  // Order actions
  setOrders: (orders: StoreOrder[]) => void;
  setSelectedOrder: (order: StoreOrder | null) => void;
  addOrder: (order: StoreOrder) => void;

  // Customer actions
  setCustomer: (customer: Customer | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  updateCustomer: (customer: Partial<Customer>) => void;

  // Wishlist actions
  setWishlist: (items: WishlistItem[]) => void;
  addToWishlist: (item: WishlistItem) => void;
  removeFromWishlist: (itemId: string) => void;
  isInWishlist: (productId: string) => boolean;

  // Search & Filter actions
  setSearchQuery: (query: string) => void;
  setSearchFilters: (filters: Partial<SearchFilters>) => void;
  setSearchResults: (results: StoreProduct[]) => void;
  resetSearch: () => void;

  // UI actions
  setShowCartModal: (show: boolean) => void;
  setShowCheckoutModal: (show: boolean) => void;
}

const ecommerceSlice = createSlice<EcommerceState, EcommerceActions>({
  name: 'ecommerce',
  initialState: {
    // Products
    products: [],
    featuredProducts: [],
    newProducts: [],
    selectedProduct: null,

    // Categories
    categories: [],
    selectedCategory: null,

    // Cart
    cart: null,

    // Orders
    orders: [],
    selectedOrder: null,

    // Customer
    customer: null,
    isAuthenticated: false,

    // Wishlist
    wishlist: [],

    // Search & Filters
    searchQuery: '',
    searchFilters: {
      sortBy: 'relevance',
    },
    searchResults: [],

    // UI State
    showCartModal: false,
    showCheckoutModal: false,

    // Required base state
    _actions: {},
    _errors: {},
  },
  actions: (set, get) => ({
    // Product actions
    setProducts: (products) => set({ products }),
    setFeaturedProducts: (featuredProducts) => set({ featuredProducts }),
    setNewProducts: (newProducts) => set({ newProducts }),
    setSelectedProduct: (selectedProduct) => set({ selectedProduct }),

    // Category actions
    setCategories: (categories) => set({ categories }),
    setSelectedCategory: (selectedCategory) => set({ selectedCategory }),

    // Cart actions
    setCart: (cart) => set({ cart }),
    addToCart: (item) => {
      const state = get();
      if (!state.cart) return;
      const existingItem = state.cart.items.find((i) => i.id === item.id);
      if (existingItem) {
        state.updateCartItem(item.id, existingItem.quantity + item.quantity);
        return;
      }
      const newItems = [...state.cart.items, item];
      state.recalculateCart(newItems);
    },
    updateCartItem: (itemId, quantity) => {
      const state = get();
      if (!state.cart) return;
      if (quantity <= 0) {
        state.removeFromCart(itemId);
        return;
      }
      const newItems = state.cart.items.map((item) =>
        item.id === itemId ? { ...item, quantity } : item
      );
      state.recalculateCart(newItems);
    },
    removeFromCart: (itemId) => {
      const state = get();
      if (!state.cart) return;
      const newItems = state.cart.items.filter((item) => item.id !== itemId);
      state.recalculateCart(newItems);
    },
    clearCart: () => set({ cart: null }),
    applyCoupon: (coupon) => {
      const state = get();
      if (!state.cart) return;
      set({ cart: { ...state.cart, couponCode: coupon.code } });
    },
    removeCoupon: () => {
      const state = get();
      if (!state.cart) return;
      set({ cart: { ...state.cart, couponCode: undefined, couponDiscount: undefined } });
    },
    recalculateCart: (items) => {
      const state = get();
      if (!state.cart) return;
      const subtotal = items.reduce((sum, item) => sum + item.subtotal, 0);
      const totalDiscount = items.reduce((sum, item) => sum + item.discountAmount, 0);
      const totalTax = items.reduce((sum, item) => sum + item.taxAmount, 0);
      const total = subtotal + totalTax - totalDiscount + (state.cart.shippingCost || 0);
      const itemCount = items.length;
      const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);

      set({
        cart: {
          ...state.cart,
          items,
          subtotal,
          totalDiscount,
          totalTax,
          total,
          itemCount,
          totalQuantity,
        },
      });
    },

    // Order actions
    setOrders: (orders) => set({ orders }),
    setSelectedOrder: (selectedOrder) => set({ selectedOrder }),
    addOrder: (order) =>
      set((state) => ({ orders: [order, ...state.orders] })),

    // Customer actions
    setCustomer: (customer) => set({ customer }),
    setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
    updateCustomer: (customerData) =>
      set((state) => ({
        customer: state.customer ? { ...state.customer, ...customerData } : null,
      })),

    // Wishlist actions
    setWishlist: (wishlist) => set({ wishlist }),
    addToWishlist: (item) =>
      set((state) => {
        if (state.wishlist.find((w) => w.productId === item.productId)) return state;
        return { wishlist: [...state.wishlist, item] };
      }),
    removeFromWishlist: (itemId) =>
      set((state) => ({
        wishlist: state.wishlist.filter((item) => item.id !== itemId),
      })),
    isInWishlist: (productId) => {
      return get().wishlist.some((item) => item.productId === productId);
    },

    // Search & Filter actions
    setSearchQuery: (searchQuery) => set({ searchQuery }),
    setSearchFilters: (filters) =>
      set((state) => ({
        searchFilters: { ...state.searchFilters, ...filters },
      })),
    setSearchResults: (searchResults) => set({ searchResults }),
    resetSearch: () =>
      set({
        searchQuery: '',
        searchFilters: { sortBy: 'relevance' },
        searchResults: [],
      }),

    // UI actions
    setShowCartModal: (showCartModal) => set({ showCartModal }),
    setShowCheckoutModal: (showCheckoutModal) => set({ showCheckoutModal }),
  }),
});

export const useEcommerceStore = createStore({
  name: 'ecommerce',
  initialState: ecommerceSlice.initialState,
  actions: ecommerceSlice.actions,
  persist: {
    enabled: true,
    key: 'ecommerce-storage',
    partialize: (state) => ({
      cart: state.cart,
      wishlist: state.wishlist,
      customer: state.customer,
      isAuthenticated: state.isAuthenticated,
      searchFilters: state.searchFilters,
    }),
  },
});

