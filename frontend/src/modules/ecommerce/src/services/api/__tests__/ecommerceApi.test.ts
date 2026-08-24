import {
  ecommerceProductAPI,
  ecommerceCategoryAPI,
  ecommerceCartAPI,
  ecommerceOrderAPI,
} from '../ecommerceApi';

// Mock axios
jest.mock('axios', () => {
  const mockAxios = jest.fn();
  mockAxios.create = jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  }));
  return mockAxios;
});

const axios = require('axios');

describe('Ecommerce API', () => {
  let mockApiInstance: any;

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiInstance = axios.create();
  });

  describe('Product API', () => {
    describe('getAll', () => {
      it('should fetch all products with pagination', async () => {
        const mockResponse = {
          data: {
            products: [{ id: '1', name: 'Product 1' }],
            total: 10,
            page: 1,
            totalPages: 2,
          },
        };
        mockApiInstance.get.mockResolvedValue(mockResponse);

        const result = await ecommerceProductAPI.getAll({ page: 1, limit: 10 });

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products', {
          params: { page: 1, limit: 10 },
        });
        expect(result).toEqual(mockResponse.data);
      });

      it('should fetch products with category filter', async () => {
        const mockResponse = { data: { products: [], total: 0, page: 1, totalPages: 0 } };
        mockApiInstance.get.mockResolvedValue(mockResponse);

        await ecommerceProductAPI.getAll({ category: 'electronics' });

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products', {
          params: { category: 'electronics' },
        });
      });

      it('should fetch featured products', async () => {
        const mockResponse = { data: { products: [], total: 0, page: 1, totalPages: 0 } };
        mockApiInstance.get.mockResolvedValue(mockResponse);

        await ecommerceProductAPI.getAll({ featured: true });

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products', {
          params: { featured: true },
        });
      });
    });

    describe('getBySlug', () => {
      it('should fetch product by slug', async () => {
        const mockProduct = { id: '1', name: 'Product 1', slug: 'product-1' };
        mockApiInstance.get.mockResolvedValue({ data: mockProduct });

        const result = await ecommerceProductAPI.getBySlug('product-1');

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products/slug/product-1');
        expect(result).toEqual(mockProduct);
      });
    });

    describe('getById', () => {
      it('should fetch product by ID', async () => {
        const mockProduct = { id: 'prod-123', name: 'Product' };
        mockApiInstance.get.mockResolvedValue({ data: mockProduct });

        const result = await ecommerceProductAPI.getById('prod-123');

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products/prod-123');
        expect(result).toEqual(mockProduct);
      });
    });

    describe('getRelated', () => {
      it('should fetch related products', async () => {
        const mockProducts = [{ id: '2', name: 'Related Product' }];
        mockApiInstance.get.mockResolvedValue({ data: mockProducts });

        const result = await ecommerceProductAPI.getRelated('prod-123', 5);

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products/prod-123/related', {
          params: { limit: 5 },
        });
        expect(result).toEqual(mockProducts);
      });
    });

    describe('getReviews', () => {
      it('should fetch product reviews', async () => {
        const mockResponse = {
          data: {
            reviews: [{ id: '1', rating: 5, content: 'Great!' }],
            total: 10,
            averageRating: 4.5,
          },
        };
        mockApiInstance.get.mockResolvedValue(mockResponse);

        const result = await ecommerceProductAPI.getReviews('prod-123');

        expect(mockApiInstance.get).toHaveBeenCalledWith('/products/prod-123/reviews', {
          params: undefined,
        });
        expect(result).toEqual(mockResponse.data);
      });
    });

    describe('addReview', () => {
      it('should add a product review', async () => {
        const mockReview = { id: 'review-1', rating: 5, content: 'Excellent' };
        mockApiInstance.post.mockResolvedValue({ data: mockReview });

        const result = await ecommerceProductAPI.addReview('prod-123', {
          customerId: 'cust-1',
          customerName: 'John',
          rating: 5,
          title: 'Great product',
          content: 'Excellent quality',
        });

        expect(mockApiInstance.post).toHaveBeenCalledWith(
          '/products/prod-123/reviews',
          {
            customerId: 'cust-1',
            customerName: 'John',
            rating: 5,
            title: 'Great product',
            content: 'Excellent quality',
          }
        );
        expect(result).toEqual(mockReview);
      });
    });
  });

  describe('Category API', () => {
    describe('getAll', () => {
      it('should fetch all categories', async () => {
        const mockCategories = [
          { id: '1', name: 'Electronics', slug: 'electronics' },
          { id: '2', name: 'Clothing', slug: 'clothing' },
        ];
        mockApiInstance.get.mockResolvedValue({ data: mockCategories });

        const result = await ecommerceCategoryAPI.getAll();

        expect(mockApiInstance.get).toHaveBeenCalledWith('/categories');
        expect(result).toEqual(mockCategories);
      });
    });

    describe('getBySlug', () => {
      it('should fetch category by slug', async () => {
        const mockCategory = { id: '1', name: 'Electronics', slug: 'electronics' };
        mockApiInstance.get.mockResolvedValue({ data: mockCategory });

        const result = await ecommerceCategoryAPI.getBySlug('electronics');

        expect(mockApiInstance.get).toHaveBeenCalledWith('/categories/slug/electronics');
        expect(result).toEqual(mockCategory);
      });
    });

    describe('getProducts', () => {
      it('should fetch products for a category', async () => {
        const mockResponse = {
          data: { products: [{ id: '1', name: 'Product' }], total: 10, page: 1 },
        };
        mockApiInstance.get.mockResolvedValue(mockResponse);

        const result = await ecommerceCategoryAPI.getProducts('cat-123', {
          page: 1,
          limit: 20,
        });

        expect(mockApiInstance.get).toHaveBeenCalledWith('/categories/cat-123/products', {
          params: { page: 1, limit: 20 },
        });
        expect(result).toEqual(mockResponse.data);
      });
    });
  });

  describe('Cart API', () => {
    const sessionId = 'session-123';

    describe('get', () => {
      it('should fetch cart by session ID', async () => {
        const mockCart = { id: 'cart-1', items: [], total: 0 };
        mockApiInstance.get.mockResolvedValue({ data: mockCart });

        const result = await ecommerceCartAPI.get(sessionId);

        expect(mockApiInstance.get).toHaveBeenCalledWith('/cart', {
          headers: { 'X-Session-Id': sessionId },
        });
        expect(result).toEqual(mockCart);
      });
    });

    describe('addItem', () => {
      it('should add item to cart', async () => {
        const mockCart = { id: 'cart-1', items: [{ productId: 'prod-1', quantity: 1 }] };
        mockApiInstance.post.mockResolvedValue({ data: mockCart });

        const result = await ecommerceCartAPI.addItem(sessionId, {
          productId: 'prod-1',
          quantity: 1,
        });

        expect(mockApiInstance.post).toHaveBeenCalledWith(
          '/cart/items',
          { productId: 'prod-1', quantity: 1 },
          { headers: { 'X-Session-Id': sessionId } }
        );
        expect(result).toEqual(mockCart);
      });
    });

    describe('updateItem', () => {
      it('should update cart item quantity', async () => {
        const mockCart = { id: 'cart-1', items: [{ productId: 'prod-1', quantity: 3 }] };
        mockApiInstance.put.mockResolvedValue({ data: mockCart });

        const result = await ecommerceCartAPI.updateItem(sessionId, 'item-1', 3);

        expect(mockApiInstance.put).toHaveBeenCalledWith(
          '/cart/items/item-1',
          { quantity: 3 },
          { headers: { 'X-Session-Id': sessionId } }
        );
        expect(result).toEqual(mockCart);
      });
    });

    describe('removeItem', () => {
      it('should remove item from cart', async () => {
        mockApiInstance.delete.mockResolvedValue({ data: { items: [] } });

        await ecommerceCartAPI.removeItem(sessionId, 'item-1');

        expect(mockApiInstance.delete).toHaveBeenCalledWith('/cart/items/item-1', {
          headers: { 'X-Session-Id': sessionId },
        });
      });
    });

    describe('applyCoupon', () => {
      it('should apply coupon to cart', async () => {
        const mockCart = { id: 'cart-1', couponCode: 'SAVE10', total: 90 };
        mockApiInstance.post.mockResolvedValue({ data: mockCart });

        const result = await ecommerceCartAPI.applyCoupon(sessionId, 'SAVE10');

        expect(mockApiInstance.post).toHaveBeenCalledWith(
          '/cart/coupon',
          { code: 'SAVE10' },
          { headers: { 'X-Session-Id': sessionId } }
        );
        expect(result).toEqual(mockCart);
      });
    });
  });

  describe('Order API', () => {
    const sessionId = 'session-123';

    describe('create', () => {
      it('should create a new order', async () => {
        const mockOrder = { id: 'order-1', orderNumber: 'ORD-001', status: 'pending' };
        const orderData = {
          shippingAddress: { address1: '123 Main St', city: 'City', postalCode: '12345' },
          billingAddress: { address1: '123 Main St', city: 'City', postalCode: '12345' },
          shippingMethodId: 'ship-1',
          paymentMethod: 'credit_card',
        };
        mockApiInstance.post.mockResolvedValue({ data: mockOrder });

        const result = await ecommerceOrderAPI.create(sessionId, orderData as any);

        expect(mockApiInstance.post).toHaveBeenCalledWith(
          '/orders',
          orderData,
          { headers: { 'X-Session-Id': sessionId } }
        );
        expect(result).toEqual(mockOrder);
      });
    });

    describe('getById', () => {
      it('should fetch order by ID', async () => {
        const mockOrder = { id: 'order-1', orderNumber: 'ORD-001', status: 'delivered' };
        mockApiInstance.get.mockResolvedValue({ data: mockOrder });

        const result = await ecommerceOrderAPI.getById('order-1');

        expect(mockApiInstance.get).toHaveBeenCalledWith('/orders/order-1');
        expect(result).toEqual(mockOrder);
      });
    });

    describe('cancel', () => {
      it('should cancel an order', async () => {
        const mockOrder = { id: 'order-1', status: 'cancelled' };
        mockApiInstance.patch.mockResolvedValue({ data: mockOrder });

        const result = await ecommerceOrderAPI.cancel('order-1', 'Customer request');

        expect(mockApiInstance.patch).toHaveBeenCalledWith(
          '/orders/order-1/cancel',
          { reason: 'Customer request' }
        );
        expect(result).toEqual(mockOrder);
      });
    });
  });
});
