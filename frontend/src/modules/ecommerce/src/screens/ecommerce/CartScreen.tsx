import React from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity, Image } from 'react-native';
import { Card, Text, Button, IconButton, useTheme, Divider, TextInput, Chip } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ecommerceCartAPI, ecommerceCouponAPI } from '../../services/api/ecommerceApi';
import { useEcommerceStore } from '../../store/ecommerceStore';
import { StoreCartItem } from '../../types/ecommerce';

export const CartScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const {
    cart,
    setCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    applyCoupon,
    removeCoupon,
  } = useEcommerceStore();

  const [couponCode, setCouponCode] = React.useState('');
  const [couponError, setCouponError] = React.useState('');

  const updateItemMutation = useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: string; quantity: number }) =>
      ecommerceCartAPI.updateItem(cart?.sessionId || '', itemId, quantity),
    onSuccess: (data) => setCart(data),
  });

  const removeItemMutation = useMutation({
    mutationFn: (itemId: string) =>
      ecommerceCartAPI.removeItem(cart?.sessionId || '', itemId),
    onSuccess: (data) => setCart(data),
  });

  const applyCouponMutation = useMutation({
    mutationFn: () =>
      ecommerceCartAPI.applyCoupon(cart?.sessionId || '', couponCode),
    onSuccess: (data) => {
      setCart(data);
      setCouponCode('');
      setCouponError('');
    },
    onError: () => {
      setCouponError('Invalid or expired coupon code');
    },
  });

  const removeCouponMutation = useMutation({
    mutationFn: () => ecommerceCartAPI.removeCoupon(cart?.sessionId || ''),
    onSuccess: (data) => setCart(data),
  });

  const handleQuantityChange = (itemId: string, newQuantity: number) => {
    if (newQuantity <= 0) {
      removeItemMutation.mutate(itemId);
      return;
    }
    updateItemMutation.mutate({ itemId, quantity: newQuantity });
  };

  const handleApplyCoupon = () => {
    if (!couponCode.trim()) return;
    applyCouponMutation.mutate();
  };

  const renderCartItem = ({ item }: { item: StoreCartItem }) => (
    <Card style={styles.cartItem}>
      <Card.Content>
        <View style={styles.itemRow}>
          {item.productImage ? (
            <Image source={{ uri: item.productImage }} style={styles.itemImage} />
          ) : (
            <View style={[styles.itemImage, styles.imagePlaceholder]}>
              <MaterialCommunityIcons name="package-variant" size={30} color={theme.colors.primary} />
            </View>
          )}
          <View style={styles.itemDetails}>
            <Text variant="titleSmall" style={styles.itemName} numberOfLines={2}>
              {item.productName}
            </Text>
            {item.variantName && (
              <Text variant="bodySmall" style={styles.variantName}>
                {item.variantName}
              </Text>
            )}
            <Text variant="bodySmall" style={styles.itemSku}>
              SKU: {item.sku}
            </Text>
            <View style={styles.itemPriceRow}>
              <Text variant="bodyMedium" style={styles.itemPrice}>
                {item.unitPrice.toLocaleString()} MMK
              </Text>
              {item.discountAmount > 0 && (
                <Text variant="bodySmall" style={styles.itemDiscount}>
                  -{item.discountAmount.toLocaleString()} MMK
                </Text>
              )}
            </View>
          </View>
          <View style={styles.itemActions}>
            <IconButton
              icon="delete"
              size={20}
              iconColor={theme.colors.error}
              onPress={() => removeItemMutation.mutate(item.id)}
              style={styles.deleteButton}
            />
            <View style={styles.quantityControl}>
              <IconButton
                icon="minus"
                size={16}
                onPress={() => handleQuantityChange(item.id, item.quantity - 1)}
                disabled={item.quantity <= 1}
              />
              <Text variant="bodyMedium" style={styles.quantityText}>
                {item.quantity}
              </Text>
              <IconButton
                icon="plus"
                size={16}
                onPress={() => handleQuantityChange(item.id, item.quantity + 1)}
                disabled={item.quantity >= item.maxQuantity}
              />
            </View>
          </View>
        </View>
        <View style={styles.itemTotalRow}>
          <Text variant="bodySmall" style={{ opacity: 0.6 }}>
            Subtotal
          </Text>
          <Text variant="titleSmall" style={styles.itemTotal}>
            {item.total.toLocaleString()} MMK
          </Text>
        </View>
      </Card.Content>
    </Card>
  );

  if (!cart || cart.items.length === 0) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <MaterialCommunityIcons name="cart-off" size={80} color={theme.colors.outline} />
        <Text variant="headlineSmall" style={styles.emptyTitle}>
          Your Cart is Empty
        </Text>
        <Text variant="bodyMedium" style={styles.emptySubtitle}>
          Browse our products and add items to your cart
        </Text>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('ProductCatalog' as never)}
          style={styles.browseButton}
          icon="shopping"
        >
          Browse Products
        </Button>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={cart.items}
        renderItem={renderCartItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View style={styles.header}>
            <View style={styles.headerRow}>
              <Text variant="headlineSmall" style={styles.title}>
                Shopping Cart
              </Text>
              <Button
                mode="text"
                compact
                icon="delete-sweep"
                onPress={() => clearCart()}
                textColor={theme.colors.error}
              >
                Clear
              </Button>
            </View>
            <Text variant="bodyMedium" style={styles.itemCount}>
              {cart.totalQuantity} item(s) in cart
            </Text>
          </View>
        }
        ListFooterComponent={
          <View style={styles.footer}>
            {/* Coupon Section */}
            {!cart.couponCode ? (
              <View style={styles.couponSection}>
                <Text variant="titleSmall" style={styles.sectionTitle}>
                  Apply Coupon
                </Text>
                <View style={styles.couponRow}>
                  <TextInput
                    mode="outlined"
                    placeholder="Enter coupon code"
                    value={couponCode}
                    onChangeText={(text) => {
                      setCouponCode(text);
                      setCouponError('');
                    }}
                    style={styles.couponInput}
                    error={!!couponError}
                  />
                  <Button
                    mode="contained"
                    onPress={handleApplyCoupon}
                    loading={applyCouponMutation.isPending}
                    disabled={!couponCode.trim()}
                    style={styles.applyButton}
                  >
                    Apply
                  </Button>
                </View>
                {couponError ? (
                  <Text variant="bodySmall" style={{ color: theme.colors.error, marginTop: 4 }}>
                    {couponError}
                  </Text>
                ) : null}
              </View>
            ) : (
              <View style={styles.appliedCoupon}>
                <Chip
                  icon="ticket-percent"
                  onClose={() => removeCouponMutation.mutate()}
                  style={styles.couponChip}
                >
                  Coupon: {cart.couponCode}
                </Chip>
              </View>
            )}

            <Divider style={styles.divider} />

            {/* Order Summary */}
            <Text variant="titleSmall" style={styles.sectionTitle}>
              Order Summary
            </Text>
            <View style={styles.summaryRow}>
              <Text variant="bodyMedium">Subtotal</Text>
              <Text variant="bodyMedium">{cart.subtotal.toLocaleString()} MMK</Text>
            </View>
            {cart.totalDiscount > 0 && (
              <View style={styles.summaryRow}>
                <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
                  Discount
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
                  -{cart.totalDiscount.toLocaleString()} MMK
                </Text>
              </View>
            )}
            {cart.couponDiscount && cart.couponDiscount > 0 && (
              <View style={styles.summaryRow}>
                <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
                  Coupon Discount
                </Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
                  -{cart.couponDiscount.toLocaleString()} MMK
                </Text>
              </View>
            )}
            <View style={styles.summaryRow}>
              <Text variant="bodyMedium">Tax</Text>
              <Text variant="bodyMedium">{cart.totalTax.toLocaleString()} MMK</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text variant="bodyMedium">Shipping</Text>
              <Text variant="bodyMedium">
                {cart.shippingCost > 0 ? `${cart.shippingCost.toLocaleString()} MMK` : 'Free'}
              </Text>
            </View>
            <Divider style={styles.divider} />
            <View style={styles.totalRow}>
              <Text variant="headlineSmall" style={styles.totalLabel}>
                Total
              </Text>
              <Text variant="headlineSmall" style={styles.totalValue}>
                {cart.total.toLocaleString()} MMK
              </Text>
            </View>

            <Button
              mode="contained"
              onPress={() => navigation.navigate('Checkout' as never)}
              style={styles.checkoutButton}
              contentStyle={styles.checkoutButtonContent}
              icon="arrow-right"
            >
              Proceed to Checkout
            </Button>

            <Button
              mode="text"
              onPress={() => navigation.navigate('ProductCatalog' as never)}
              style={styles.continueButton}
            >
              Continue Shopping
            </Button>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  emptyTitle: {
    marginTop: 16,
    fontWeight: 'bold',
  },
  emptySubtitle: {
    opacity: 0.6,
    marginTop: 8,
    marginBottom: 24,
    textAlign: 'center',
  },
  browseButton: {
    paddingHorizontal: 32,
  },
  listContent: {
    padding: 16,
    paddingBottom: 24,
  },
  header: {
    marginBottom: 16,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontWeight: 'bold',
  },
  itemCount: {
    opacity: 0.6,
    marginTop: 4,
  },
  cartItem: {
    marginBottom: 12,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  itemImage: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 12,
  },
  imagePlaceholder: {
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemDetails: {
    flex: 1,
  },
  itemName: {
    fontWeight: '500',
  },
  variantName: {
    opacity: 0.7,
    marginTop: 2,
  },
  itemSku: {
    opacity: 0.5,
    marginTop: 2,
  },
  itemPriceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 4,
  },
  itemPrice: {
    fontWeight: '500',
  },
  itemDiscount: {
    color: '#f44336',
  },
  itemActions: {
    alignItems: 'flex-end',
  },
  deleteButton: {
    margin: 0,
  },
  quantityControl: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
  },
  quantityText: {
    minWidth: 28,
    textAlign: 'center',
  },
  itemTotalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  itemTotal: {
    fontWeight: 'bold',
  },
  footer: {
    marginTop: 16,
  },
  couponSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  couponRow: {
    flexDirection: 'row',
    gap: 8,
  },
  couponInput: {
    flex: 1,
  },
  applyButton: {
    justifyContent: 'center',
  },
  appliedCoupon: {
    marginBottom: 16,
  },
  couponChip: {
    alignSelf: 'flex-start',
  },
  divider: {
    marginVertical: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
  },
  totalLabel: {
    fontWeight: 'bold',
  },
  totalValue: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  checkoutButton: {
    marginTop: 16,
  },
  checkoutButtonContent: {
    paddingVertical: 8,
  },
  continueButton: {
    marginTop: 8,
  },
});

