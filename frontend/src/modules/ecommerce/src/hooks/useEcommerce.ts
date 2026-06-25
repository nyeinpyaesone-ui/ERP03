import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ecommerceProductAPI,
  ecommerceCategoryAPI,
  ecommerceCartAPI,
  ecommerceOrderAPI,
  ecommerceCustomerAPI,
  ecommerceWishlistAPI,
  ecommerceCouponAPI,
  ecommerceShippingAPI,
  ecommerceSearchAPI,
  ecommerceKPIAPI,
} from '../services/api/ecommerceApi';
import {
  StoreProduct,
  StoreCategory,
  StoreCart,
  StoreOrder,
  Customer,
  ProductReview,
  WishlistItem,
  StoreCoupon,
  ShippingMethod,
  EcommerceKPI,
  SearchFilters,
} from '../types/ecommerce';

// Product Hooks
export const useStoreProducts = (params?: Parameters<typeof ecommerceProductAPI.getAll>[0]) =>
  useQuery<{ products: StoreProduct[]; total: number; page: number; totalPages: number }>({
    queryKey: ['storeProducts', params],
    queryFn: () => ecommerceProductAPI.getAll(params),
  });

export const useStoreProduct = (slug: string) =>
  useQuery<StoreProduct>({
    queryKey: ['storeProduct', slug],
    queryFn: () => ecommerceProductAPI.getBySlug(slug),
    enabled: !!slug,
  });

export const useRelatedProducts = (productId: string, limit?: number) =>
  useQuery<StoreProduct[]>({
    queryKey: ['relatedProducts', productId, limit],
    queryFn: () => ecommerceProductAPI.getRelated(productId, limit),
    enabled: !!productId,
  });

export const useProductReviews = (productId: string, params?: Parameters<typeof ecommerceProductAPI.getReviews>[1]) =>
  useQuery<{ reviews: ProductReview[]; total: number; averageRating: number }>({
    queryKey: ['productReviews', productId, params],
    queryFn: () => ecommerceProductAPI.getReviews(productId, params),
    enabled: !!productId,
  });

export const useAddReview = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, data }: { productId: string; data: Parameters<typeof ecommerceProductAPI.addReview>[1] }) =>
      ecommerceProductAPI.addReview(productId, data),
    onSuccess: (_, { productId }) => {
      queryClient.invalidateQueries({ queryKey: ['productReviews', productId] });
    },
  });
};

// Category Hooks
export const useStoreCategories = () =>
  useQuery<StoreCategory[]>({
    queryKey: ['storeCategories'],
    queryFn: () => ecommerceCategoryAPI.getAll(),
  });

export const useStoreCategory = (slug: string) =>
  useQuery<StoreCategory>({
    queryKey: ['storeCategory', slug],
    queryFn: () => ecommerceCategoryAPI.getBySlug(slug),
    enabled: !!slug,
  });

// Cart Hooks
export const useCart = (sessionId: string) =>
  useQuery<StoreCart>({
    queryKey: ['cart', sessionId],
    queryFn: () => ecommerceCartAPI.get(sessionId),
    enabled: !!sessionId,
  });

export const useAddToCart = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: Parameters<typeof ecommerceCartAPI.addItem>[1] }) =>
      ecommerceCartAPI.addItem(sessionId, data),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['cart', sessionId] });
    },
  });
};

export const useUpdateCartItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, itemId, quantity }: { sessionId: string; itemId: string; quantity: number }) =>
      ecommerceCartAPI.updateItem(sessionId, itemId, quantity),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['cart', sessionId] });
    },
  });
};

export const useRemoveFromCart = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, itemId }: { sessionId: string; itemId: string }) =>
      ecommerceCartAPI.removeItem(sessionId, itemId),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['cart', sessionId] });
    },
  });
};

export const useApplyCoupon = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, code }: { sessionId: string; code: string }) =>
      ecommerceCartAPI.applyCoupon(sessionId, code),
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({ queryKey: ['cart', sessionId] });
    },
  });
};

// Order Hooks
export const usePlaceOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: string; data: Parameters<typeof ecommerceOrderAPI.create>[1] }) =>
      ecommerceOrderAPI.create(sessionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['ecommerceKPI'] });
    },
  });
};

export const useOrders = (params?: Parameters<typeof ecommerceOrderAPI.getAll>[0]) =>
  useQuery<{ orders: StoreOrder[]; total: number; page: number }>({
    queryKey: ['orders', params],
    queryFn: () => ecommerceOrderAPI.getAll(params),
  });

export const useOrder = (id: string) =>
  useQuery<StoreOrder>({
    queryKey: ['order', id],
    queryFn: () => ecommerceOrderAPI.getById(id),
    enabled: !!id,
  });

export const useCancelOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      ecommerceOrderAPI.cancel(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
  });
};

// Customer Hooks
export const useCustomerProfile = () =>
  useQuery<Customer>({
    queryKey: ['customerProfile'],
    queryFn: () => ecommerceCustomerAPI.getProfile(),
  });

export const useCustomerOrders = (params?: Parameters<typeof ecommerceCustomerAPI.getOrders>[0]) =>
  useQuery<{ orders: StoreOrder[]; total: number; page: number }>({
    queryKey: ['customerOrders', params],
    queryFn: () => ecommerceCustomerAPI.getOrders(params),
  });

export const useCustomerAddresses = () =>
  useQuery<Customer['addresses']>({
    queryKey: ['customerAddresses'],
    queryFn: () => ecommerceCustomerAPI.getAddresses(),
  });

export const useAddAddress = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ecommerceCustomerAPI.addAddress,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customerAddresses'] });
    },
  });
};

// Wishlist Hooks
export const useWishlist = () =>
  useQuery<WishlistItem[]>({
    queryKey: ['wishlist'],
    queryFn: () => ecommerceWishlistAPI.get(),
  });

export const useAddToWishlist = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ecommerceWishlistAPI.add,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
    },
  });
};

export const useRemoveFromWishlist = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ecommerceWishlistAPI.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wishlist'] });
    },
  });
};

// Coupon Hooks
export const useValidateCoupon = () =>
  useMutation({
    mutationFn: ({ code, cartTotal }: { code: string; cartTotal: number }) =>
      ecommerceCouponAPI.validate(code, cartTotal),
  });

// Shipping Hooks
export const useShippingMethods = (params?: Parameters<typeof ecommerceShippingAPI.getMethods>[0]) =>
  useQuery<ShippingMethod[]>({
    queryKey: ['shippingMethods', params],
    queryFn: () => ecommerceShippingAPI.getMethods(params),
  });

// Search Hooks
export const useProductSearch = (query: string, filters?: SearchFilters, page?: number, limit?: number) =>
  useQuery<{ products: StoreProduct[]; total: number; page: number; facets: any }>({
    queryKey: ['productSearch', query, filters, page, limit],
    queryFn: () => ecommerceSearchAPI.search(query, filters, page, limit),
    enabled: query.length > 0,
  });

// KPI Hooks
export const useEcommerceKPI = (period?: 'today' | 'week' | 'month') =>
  useQuery<EcommerceKPI>({
    queryKey: ['ecommerceKPI', period],
    queryFn: () => ecommerceKPIAPI.getDashboard(period),
  });

