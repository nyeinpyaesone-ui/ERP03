import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
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
  setProducts: (products: StoreProduct[]) => void;
  setFeaturedProducts: (products: StoreProduct[]) => void;
  setNewProducts: (products: StoreProduct[]) => void;
  setSelectedProduct: (product: StoreProduct | null) => void;

  // Categories
  categories: StoreCategory[];
  selectedCategory: StoreCategory | null;
  setCategories: (categories: StoreCategory[]) => void;
  setSelectedCategory: (category: StoreCategory | null) => void;

  // Cart
  cart: StoreCart | null;
  setCart: (cart: StoreCart | null) => void;
  addToCart: (item: StoreCartItem) => void;
  updateCartItem: (itemId: string, quantity: number) => void;
  removeFromCart: (itemId: string) => void;
  clearCart: () => void;
  applyCoupon: (coupon: StoreCoupon) => void;
  removeCoupon: () => void;

  // Orders
  orders: StoreOrder[];
  selectedOrder: StoreOrder | null;
  setOrders: (orders: StoreOrder[]) => void;
  setSelectedOrder: (order: StoreOrder | null) => void;
  addOrder: (order: StoreOrder) => void;

  // Customer
  customer: Customer | null;
  isAuthenticated: boolean;
  setCustomer: (customer: Customer | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  updateCustomer: (customer: Partial<Customer>) => void;

  // Wishlist
  wishlist: WishlistItem[];
  setWishlist: (items: WishlistItem[]) => void;
  addToWishlist: (item: WishlistItem) => void;
  removeFromWishlist: (itemId: string) => void;
  isInWishlist: (productId: string) => boolean;

  // Search & Filters
  searchQuery: string;
  searchFilters: SearchFilters;
  searchResults: StoreProduct[];
  setSearchQuery: (query: string) => void;
  setSearchFilters: (filters: Partial<SearchFilters>) => void;
  setSearchResults: (results: StoreProduct[]) => void;
  resetSearch: () => void;

  // UI State
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  showCartModal: boolean;
  setShowCartModal: (show: boolean) => void;
  showCheckoutModal: boolean;
  setShowCheckoutModal: (show: boolean) => void;
}

export const useEcommerceStore = create<EcommerceState>()(
  persist(
    (set, get) => ({
      // Products
      products: [],
      featuredProducts: [],
      newProducts: [],
      selectedProduct: null,
      setProducts: (products) => set({ products }),
      setFeaturedProducts: (featuredProducts) => set({ featuredProducts }),
      setNewProducts: (newProducts) => set({ newProducts }),
      setSelectedProduct: (selectedProduct) => set({ selectedProduct }),

      // Categories
      categories: [],
      selectedCategory: null,
      setCategories: (categories) => set({ categories }),
      setSelectedCategory: (selectedCategory) => set({ selectedCategory }),

      // Cart
      cart: null,
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
        // Apply coupon logic here
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

      // Orders
      orders: [],
      selectedOrder: null,
      setOrders: (orders) => set({ orders }),
      setSelectedOrder: (selectedOrder) => set({ selectedOrder }),
      addOrder: (order) =>
        set((state) => ({ orders: [order, ...state.orders] })),

      // Customer
      customer: null,
      isAuthenticated: false,
      setCustomer: (customer) => set({ customer }),
      setIsAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
      updateCustomer: (customerData) =>
        set((state) => ({
          customer: state.customer ? { ...state.customer, ...customerData } : null,
        })),

      // Wishlist
      wishlist: [],
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

      // Search & Filters
      searchQuery: '',
      searchFilters: {
        sortBy: 'relevance',
      },
      searchResults: [],
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

      // UI State
      isLoading: false,
      setIsLoading: (isLoading) => set({ isLoading }),
      error: null,
      setError: (error) => set({ error }),
      showCartModal: false,
      setShowCartModal: (showCartModal) => set({ showCartModal }),
      showCheckoutModal: false,
      setShowCheckoutModal: (showCheckoutModal) => set({ showCheckoutModal }),
    }),
    {
      name: 'ecommerce-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        cart: state.cart,
        wishlist: state.wishlist,
        customer: state.customer,
        isAuthenticated: state.isAuthenticated,
        searchFilters: state.searchFilters,
      }),
    }
  )
);

