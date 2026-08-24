import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  Cart,
  CartItem,
  POSSale,
  POSShift,
  POSRegister,
  POSProduct,
  POSCategory,
  AppliedDiscount,
} from '../types/pos';

interface POSState {
  // Cart
  cart: Cart;
  addToCart: (product: POSProduct, quantity?: number, variantId?: string) => void;
  updateCartItemQuantity: (itemId: string, quantity: number) => void;
  removeFromCart: (itemId: string) => void;
  clearCart: () => void;
  applyDiscount: (discount: AppliedDiscount) => void;
  removeDiscount: (discountId: string) => void;
  setCustomer: (customerId: string | undefined, customerName: string | undefined) => void;
  setCartNotes: (notes: string) => void;
  recalculateCart: () => void;

  // Current Sale
  currentSale: POSSale | null;
  setCurrentSale: (sale: POSSale | null) => void;
  suspendedSales: POSSale[];
  suspendSale: (sale: POSSale) => void;
  resumeSale: (saleId: string) => void;
  removeSuspendedSale: (saleId: string) => void;

  // Shift
  currentShift: POSShift | null;
  setCurrentShift: (shift: POSShift | null) => void;
  shiftHistory: POSShift[];
  addShiftToHistory: (shift: POSShift) => void;

  // Register
  currentRegister: POSRegister | null;
  setCurrentRegister: (register: POSRegister | null) => void;
  availableRegisters: POSRegister[];
  setAvailableRegisters: (registers: POSRegister[]) => void;

  // Products & Categories
  products: POSProduct[];
  setProducts: (products: POSProduct[]) => void;
  categories: POSCategory[];
  setCategories: (categories: POSCategory[]) => void;
  selectedCategory: string | null;
  setSelectedCategory: (categoryId: string | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;

  // UI State
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
  showPaymentModal: boolean;
  setShowPaymentModal: (show: boolean) => void;
  showShiftModal: boolean;
  setShowShiftModal: (show: boolean) => void;
}

const initialCart: Cart = {
  items: [],
  subtotal: 0,
  totalDiscount: 0,
  totalTax: 0,
  total: 0,
  itemCount: 0,
  totalQuantity: 0,
  appliedDiscounts: [],
};

// Extracted cart reducer functions for better testability and reusability
const cartReducers = {
  addToCart: (state: POSState, product: POSProduct, quantity: number, variantId?: string) => {
    const existingItem = state.cart.items.find(
      (item) => item.productId === product.id && item.variantId === variantId
    );

    if (existingItem) {
      return { cart: { ...state.cart } }; // Will be handled by updateCartItemQuantity
    }

    const variant = variantId ? product.variants?.find((v) => v.id === variantId) : undefined;
    const unitPrice = variant?.price ?? product.price;
    const taxAmount = product.taxInclusive ? 0 : unitPrice * quantity * (product.taxRate / 100);
    const subtotal = unitPrice * quantity;
    const total = product.taxInclusive ? subtotal : subtotal + taxAmount;

    const newItem: CartItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      productId: product.id,
      productName: product.name,
      sku: variant?.sku ?? product.sku,
      barcode: variant?.barcode ?? product.barcode,
      variantId: variant?.id,
      variantName: variant?.name,
      quantity,
      unitPrice,
      originalPrice: unitPrice,
      discountAmount: 0,
      discountPercentage: 0,
      taxAmount,
      taxRate: product.taxRate,
      subtotal,
      total,
      imageUrl: product.imageUrl,
    };

    return { cart: { ...state.cart, items: [...state.cart.items, newItem] } };
  },

  updateCartItemQuantity: (state: POSState, itemId: string, quantity: number) => {
    if (quantity <= 0) {
      return { cart: { ...state.cart, items: state.cart.items.filter((item) => item.id !== itemId) } };
    }
    
    const newItems = state.cart.items.map((item) => {
      if (item.id !== itemId) return item;
      const subtotal = item.unitPrice * quantity;
      const taxAmount = item.taxRate > 0 && !item.taxAmount
        ? subtotal * (item.taxRate / 100)
        : item.taxAmount * (quantity / item.quantity);
      return {
        ...item,
        quantity,
        subtotal,
        taxAmount,
        total: subtotal + taxAmount - item.discountAmount,
      };
    });

    return { cart: { ...state.cart, items: newItems } };
  },

  removeFromCart: (state: POSState, itemId: string) => ({
    cart: { ...state.cart, items: state.cart.items.filter((item) => item.id !== itemId) },
  }),

  clearCart: () => ({ cart: initialCart }),

  recalculateCart: (state: POSState) => {
    const items = state.cart.items;
    const subtotal = items.reduce((sum, item) => sum + item.subtotal, 0);
    const totalTax = items.reduce((sum, item) => sum + item.taxAmount, 0);
    const itemDiscounts = items.reduce((sum, item) => sum + item.discountAmount, 0);
    const cartDiscounts = state.cart.appliedDiscounts.reduce((sum, d) => sum + d.amount, 0);
    const totalDiscount = itemDiscounts + cartDiscounts;
    const total = subtotal + totalTax - totalDiscount;
    const itemCount = items.length;
    const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);

    return {
      cart: {
        ...state.cart,
        items,
        subtotal,
        totalTax,
        totalDiscount,
        total: Math.max(0, total),
        itemCount,
        totalQuantity,
      },
    };
  },
};

export const usePOSStore = create<POSState>()(
  persist(
    (set, get) => ({
      // Cart
      cart: initialCart,
      addToCart: (product, quantity = 1, variantId) => {
        set((state) => cartReducers.addToCart(state, product, quantity, variantId));
      },
      updateCartItemQuantity: (itemId, quantity) => {
        set((state) => cartReducers.updateCartItemQuantity(state, itemId, quantity));
      },
      removeFromCart: (itemId) => {
        set((state) => cartReducers.removeFromCart(state, itemId));
      },
      clearCart: () => set(cartReducers.clearCart()),
      recalculateCart: () => {
        set((state) => cartReducers.recalculateCart(state));
      },
      applyDiscount: (discount) => {
        set((state) => ({ cart: { ...state.cart, appliedDiscounts: [...state.cart.appliedDiscounts, discount] } }));
        set((state) => cartReducers.recalculateCart(state));
      },
      removeDiscount: (discountId) => {
        set((state) => ({ cart: { ...state.cart, appliedDiscounts: state.cart.appliedDiscounts.filter((d) => d.id !== discountId) } }));
        set((state) => cartReducers.recalculateCart(state));
      },
      setCustomer: (customerId, customerName) =>
        set((state) => ({ cart: { ...state.cart, customerId, customerName } })),
      setCartNotes: (notes) =>
        set((state) => ({ cart: { ...state.cart, notes } })),

      // Current Sale
      currentSale: null,
      setCurrentSale: (currentSale) => set({ currentSale }),
      suspendedSales: [],
      suspendSale: (sale) =>
        set((state) => ({ suspendedSales: [...state.suspendedSales, sale] })),
      resumeSale: (saleId) => {
        const state = get();
        const sale = state.suspendedSales.find((s) => s.id === saleId);
        if (sale) {
          set({
            cart: sale.cart,
            currentSale: sale,
            suspendedSales: state.suspendedSales.filter((s) => s.id !== saleId),
          });
        }
      },
      removeSuspendedSale: (saleId) =>
        set((state) => ({
          suspendedSales: state.suspendedSales.filter((s) => s.id !== saleId),
        })),

      // Shift
      currentShift: null,
      setCurrentShift: (currentShift) => set({ currentShift }),
      shiftHistory: [],
      addShiftToHistory: (shift) =>
        set((state) => ({ shiftHistory: [shift, ...state.shiftHistory] })),

      // Register
      currentRegister: null,
      setCurrentRegister: (currentRegister) => set({ currentRegister }),
      availableRegisters: [],
      setAvailableRegisters: (availableRegisters) => set({ availableRegisters }),

      // Products & Categories
      products: [],
      setProducts: (products) => set({ products }),
      categories: [],
      setCategories: (categories) => set({ categories }),
      selectedCategory: null,
      setSelectedCategory: (selectedCategory) => set({ selectedCategory }),
      searchQuery: '',
      setSearchQuery: (searchQuery) => set({ searchQuery }),

      // UI State
      isLoading: false,
      setIsLoading: (isLoading) => set({ isLoading }),
      error: null,
      setError: (error) => set({ error }),
      showPaymentModal: false,
      setShowPaymentModal: (showPaymentModal) => set({ showPaymentModal }),
      showShiftModal: false,
      setShowShiftModal: (showShiftModal) => set({ showShiftModal }),
    }),
    {
      name: 'pos-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        currentShift: state.currentShift,
        currentRegister: state.currentRegister,
        suspendedSales: state.suspendedSales,
      }),
    }
  )
);

---

