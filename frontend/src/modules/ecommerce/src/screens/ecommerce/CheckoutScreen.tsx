import React from 'react';
import { View, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Card, Text, Button, TextInput, Chip, useTheme, Divider, RadioButton, HelperText, ProgressBar } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ecommerceOrderAPI, ecommerceShippingAPI, ecommerceCustomerAPI } from '../../services/api/ecommerceApi';
import { useEcommerceStore } from '../../store/ecommerceStore';
import { ShippingMethod, CustomerAddress, PaymentMethod } from '../../types/ecommerce';

const PAYMENT_METHODS: { method: PaymentMethod; label: string; icon: string; description: string }[] = [
  { method: 'cash_on_delivery', label: 'Cash on Delivery', icon: 'cash', description: 'Pay when you receive' },
  { method: 'bank_transfer', label: 'Bank Transfer', icon: 'bank', description: 'Transfer to our bank account' },
  { method: 'mobile_money', label: 'Mobile Money', icon: 'cellphone', description: 'Wave, KBZPay, CB Pay' },
  { method: 'credit_card', label: 'Credit/Debit Card', icon: 'credit-card', description: 'Visa, Mastercard, MPU' },
];

export const CheckoutScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const { cart, setCart, customer, setSelectedOrder } = useEcommerceStore();

  const [shippingAddress, setShippingAddress] = React.useState<Partial<CustomerAddress>>({
    firstName: customer?.firstName || '',
    lastName: customer?.lastName || '',
    phone: customer?.phone || '',
    address1: '',
    address2: '',
    city: '',
    state: '',
    postalCode: '',
    country: 'Myanmar',
    countryCode: 'MM',
  });
  const [useSameAddress, setUseSameAddress] = React.useState(true);
  const [selectedShippingMethod, setSelectedShippingMethod] = React.useState<string>('');
  const [selectedPaymentMethod, setSelectedPaymentMethod] = React.useState<PaymentMethod>('cash_on_delivery');
  const [customerNotes, setCustomerNotes] = React.useState('');
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [orderPlaced, setOrderPlaced] = React.useState(false);
  const [placedOrder, setPlacedOrder] = React.useState<any>(null);

  const { data: shippingMethods } = useQuery<ShippingMethod[]>({
    queryKey: ['shippingMethods'],
    queryFn: () => ecommerceShippingAPI.getMethods(),
  });

  const { data: customerAddresses } = useQuery({
    queryKey: ['customerAddresses'],
    queryFn: () => ecommerceCustomerAPI.getAddresses(),
    enabled: !!customer,
  });

  const placeOrderMutation = useMutation({
    mutationFn: () =>
      ecommerceOrderAPI.create(cart?.sessionId || '', {
        shippingAddress: shippingAddress as CustomerAddress,
        billingAddress: useSameAddress
          ? (shippingAddress as CustomerAddress)
          : (shippingAddress as CustomerAddress),
        shippingMethodId: selectedShippingMethod,
        paymentMethod: selectedPaymentMethod,
        customerNotes: customerNotes || undefined,
        customerId: customer?.id,
      }),
    onSuccess: (order) => {
      setPlacedOrder(order);
      setOrderPlaced(true);
      setCart(null);
      setSelectedOrder(order);
    },
  });

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!shippingAddress.firstName?.trim()) newErrors.firstName = 'First name is required';
    if (!shippingAddress.lastName?.trim()) newErrors.lastName = 'Last name is required';
    if (!shippingAddress.phone?.trim()) newErrors.phone = 'Phone is required';
    if (!shippingAddress.address1?.trim()) newErrors.address1 = 'Address is required';
    if (!shippingAddress.city?.trim()) newErrors.city = 'City is required';
    if (!shippingAddress.state?.trim()) newErrors.state = 'State/Region is required';
    if (!selectedShippingMethod) newErrors.shipping = 'Please select a shipping method';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handlePlaceOrder = () => {
    if (!validateForm()) return;
    placeOrderMutation.mutate();
  };

  if (orderPlaced && placedOrder) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <MaterialCommunityIcons name="check-circle" size={80} color="#4caf50" />
        <Text variant="headlineSmall" style={styles.successTitle}>
          Order Placed Successfully!
        </Text>
        <Text variant="bodyMedium" style={styles.successSubtitle}>
          Order #{placedOrder.orderNumber}
        </Text>
        <Text variant="bodyMedium" style={styles.successDetails}>
          Total: {placedOrder.total.toLocaleString()} MMK
        </Text>
        <View style={styles.successButtons}>
          <Button
            mode="contained"
            onPress={() => navigation.navigate('OrderDetail', { id: placedOrder.id } as never)}
            style={styles.successButton}
          >
            View Order
          </Button>
          <Button
            mode="outlined"
            onPress={() => navigation.navigate('ProductCatalog' as never)}
            style={styles.successButton}
          >
            Continue Shopping
          </Button>
        </View>
      </View>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <MaterialCommunityIcons name="cart-off" size={64} color={theme.colors.outline} />
        <Text variant="headlineSmall" style={{ marginTop: 16 }}>
          Your cart is empty
        </Text>
        <Button
          mode="contained"
          onPress={() => navigation.navigate('ProductCatalog' as never)}
          style={{ marginTop: 16 }}
        >
          Browse Products
        </Button>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        <Text variant="headlineSmall" style={styles.title}>
          Checkout
        </Text>

        {/* Order Summary */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Order Summary" />
          <Card.Content>
            {cart.items.map((item) => (
              <View key={item.id} style={styles.orderItem}>
                <View style={styles.orderItemInfo}>
                  <Text variant="bodyMedium" style={styles.orderItemName} numberOfLines={1}>
                    {item.productName}
                  </Text>
                  {item.variantName && (
                    <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                      {item.variantName}
                    </Text>
                  )}
                  <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                    Qty: {item.quantity}
                  </Text>
                </View>
                <Text variant="bodyMedium" style={styles.orderItemPrice}>
                  {item.total.toLocaleString()} MMK
                </Text>
              </View>
            ))}
            <Divider style={styles.divider} />
            <View style={styles.summaryRow}>
              <Text variant="bodyMedium">Subtotal</Text>
              <Text variant="bodyMedium">{cart.subtotal.toLocaleString()} MMK</Text>
            </View>
            {cart.totalDiscount > 0 && (
              <View style={styles.summaryRow}>
                <Text variant="bodyMedium" style={{ color: theme.colors.error }}>Discount</Text>
                <Text variant="bodyMedium" style={{ color: theme.colors.error }}>
                  -{cart.totalDiscount.toLocaleString()} MMK
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
              <Text variant="titleMedium" style={styles.totalLabel}>Total</Text>
              <Text variant="titleLarge" style={styles.totalValue}>
                {cart.total.toLocaleString()} MMK
              </Text>
            </View>
          </Card.Content>
        </Card>

        {/* Shipping Address */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Shipping Address" />
          <Card.Content>
            {customerAddresses && customerAddresses.length > 0 && (
              <View style={styles.savedAddresses}>
                <Text variant="bodySmall" style={{ marginBottom: 8, opacity: 0.7 }}>
                  Saved Addresses
                </Text>
                {customerAddresses.map((addr) => (
                  <TouchableOpacity
                    key={addr.id}
                    onPress={() => setShippingAddress(addr)}
                  >
                    <Card style={styles.addressCard}>
                      <Card.Content>
                        <Text variant="bodyMedium" style={{ fontWeight: '500' }}>
                          {addr.firstName} {addr.lastName}
                        </Text>
                        <Text variant="bodySmall">{addr.address1}</Text>
                        <Text variant="bodySmall">
                          {addr.city}, {addr.state} {addr.postalCode}
                        </Text>
                        <Text variant="bodySmall">{addr.phone}</Text>
                      </Card.Content>
                    </Card>
                  </TouchableOpacity>
                ))}
                <Divider style={styles.divider} />
              </View>
            )}

            <TextInput
              mode="outlined"
              label="First Name *"
              value={shippingAddress.firstName}
              onChangeText={(text) => setShippingAddress({ ...shippingAddress, firstName: text })}
              error={!!errors.firstName}
              style={styles.input}
            />
            <HelperText type="error" visible={!!errors.firstName}>
              {errors.firstName}
            </HelperText>

            <TextInput
              mode="outlined"
              label="Last Name *"
              value={shippingAddress.lastName}
              onChangeText={(text) => setShippingAddress({ ...shippingAddress, lastName: text })}
              error={!!errors.lastName}
              style={styles.input}
            />
            <HelperText type="error" visible={!!errors.lastName}>
              {errors.lastName}
            </HelperText>

            <TextInput
              mode="outlined"
              label="Phone *"
              value={shippingAddress.phone}
              onChangeText={(text) => setShippingAddress({ ...shippingAddress, phone: text })}
              error={!!errors.phone}
              keyboardType="phone-pad"
              style={styles.input}
            />
            <HelperText type="error" visible={!!errors.phone}>
              {errors.phone}
            </HelperText>

            <TextInput
              mode="outlined"
              label="Address Line 1 *"
              value={shippingAddress.address1}
              onChangeText={(text) => setShippingAddress({ ...shippingAddress, address1: text })}
              error={!!errors.address1}
              style={styles.input}
            />
            <HelperText type="error" visible={!!errors.address1}>
              {errors.address1}
            </HelperText>

            <TextInput
              mode="outlined"
              label="Address Line 2"
              value={shippingAddress.address2}
              onChangeText={(text) => setShippingAddress({ ...shippingAddress, address2: text })}
              style={styles.input}
            />

            <View style={styles.rowInputs}>
              <TextInput
                mode="outlined"
                label="City *"
                value={shippingAddress.city}
                onChangeText={(text) => setShippingAddress({ ...shippingAddress, city: text })}
                error={!!errors.city}
                style={[styles.input, styles.halfInput]}
              />
              <TextInput
                mode="outlined"
                label="State/Region *"
                value={shippingAddress.state}
                onChangeText={(text) => setShippingAddress({ ...shippingAddress, state: text })}
                error={!!errors.state}
                style={[styles.input, styles.halfInput]}
              />
            </View>
            <HelperText type="error" visible={!!errors.city || !!errors.state}>
              {errors.city || errors.state}
            </HelperText>

            <TextInput
              mode="outlined"
              label="Postal Code"
              value={shippingAddress.postalCode}
              onChangeText={(text) => setShippingAddress({ ...shippingAddress, postalCode: text })}
              style={styles.input}
            />
          </Card.Content>
        </Card>

        {/* Shipping Method */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Shipping Method" />
          <Card.Content>
            <RadioButton.Group
              onValueChange={setSelectedShippingMethod}
              value={selectedShippingMethod}
            >
              {shippingMethods?.map((method) => (
                <View key={method.id} style={styles.shippingOption}>
                  <RadioButton value={method.id} />
                  <View style={styles.shippingInfo}>
                    <Text variant="bodyMedium" style={{ fontWeight: '500' }}>
                      {method.name}
                    </Text>
                    <Text variant="bodySmall" style={{ opacity: 0.7 }}>
                      {method.description}
                    </Text>
                    <Text variant="bodySmall" style={{ color: theme.colors.primary }}>
                      Estimated: {method.estimatedDays}
                    </Text>
                  </View>
                  <Text variant="bodyMedium" style={styles.shippingPrice}>
                    {method.price === 0 ? 'Free' : `${method.price.toLocaleString()} MMK`}
                  </Text>
                </View>
              ))}
            </RadioButton.Group>
            {errors.shipping && (
              <HelperText type="error" visible={!!errors.shipping}>
                {errors.shipping}
              </HelperText>
            )}
          </Card.Content>
        </Card>

        {/* Payment Method */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Payment Method" />
          <Card.Content>
            <RadioButton.Group
              onValueChange={(value) => setSelectedPaymentMethod(value as PaymentMethod)}
              value={selectedPaymentMethod}
            >
              {PAYMENT_METHODS.map((method) => (
                <View key={method.method} style={styles.paymentOption}>
                  <RadioButton value={method.method} />
                  <View style={styles.paymentIcon}>
                    <MaterialCommunityIcons name={method.icon as any} size={24} color={theme.colors.primary} />
                  </View>
                  <View style={styles.paymentInfo}>
                    <Text variant="bodyMedium" style={{ fontWeight: '500' }}>
                      {method.label}
                    </Text>
                    <Text variant="bodySmall" style={{ opacity: 0.7 }}>
                      {method.description}
                    </Text>
                  </View>
                </View>
              ))}
            </RadioButton.Group>
          </Card.Content>
        </Card>

        {/* Notes */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Order Notes (Optional)" />
          <Card.Content>
            <TextInput
              mode="outlined"
              placeholder="Any special instructions for delivery..."
              value={customerNotes}
              onChangeText={setCustomerNotes}
              multiline
              numberOfLines={3}
              style={styles.input}
            />
          </Card.Content>
        </Card>

        {/* Place Order Button */}
        <View style={styles.bottomSection}>
          <View style={styles.totalRow}>
            <Text variant="titleLarge" style={styles.totalLabel}>Total</Text>
            <Text variant="headlineSmall" style={styles.totalValue}>
              {cart.total.toLocaleString()} MMK
            </Text>
          </View>
          <Button
            mode="contained"
            onPress={handlePlaceOrder}
            loading={placeOrderMutation.isPending}
            disabled={placeOrderMutation.isPending}
            style={styles.placeOrderButton}
            contentStyle={styles.placeOrderButtonContent}
            icon="check-circle"
          >
            Place Order
          </Button>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 24,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 16,
  },
  sectionCard: {
    marginBottom: 16,
  },
  orderItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  orderItemInfo: {
    flex: 1,
    marginRight: 12,
  },
  orderItemName: {
    fontWeight: '500',
  },
  orderItemPrice: {
    fontWeight: 'bold',
    minWidth: 80,
    textAlign: 'right',
  },
  divider: {
    marginVertical: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  totalLabel: {
    fontWeight: 'bold',
  },
  totalValue: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  savedAddresses: {
    marginBottom: 16,
  },
  addressCard: {
    marginBottom: 8,
  },
  input: {
    marginBottom: 4,
  },
  rowInputs: {
    flexDirection: 'row',
    gap: 12,
  },
  halfInput: {
    flex: 1,
  },
  shippingOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  shippingInfo: {
    flex: 1,
    marginLeft: 8,
  },
  shippingPrice: {
    fontWeight: 'bold',
    minWidth: 80,
    textAlign: 'right',
  },
  paymentOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  paymentIcon: {
    marginHorizontal: 8,
  },
  paymentInfo: {
    flex: 1,
  },
  bottomSection: {
    marginTop: 8,
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  placeOrderButton: {
    marginTop: 16,
  },
  placeOrderButtonContent: {
    paddingVertical: 8,
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  successTitle: {
    marginTop: 16,
    fontWeight: 'bold',
    color: '#4caf50',
  },
  successSubtitle: {
    marginTop: 8,
    opacity: 0.7,
  },
  successDetails: {
    marginTop: 8,
    fontWeight: 'bold',
    color: '#6200ee',
  },
  successButtons: {
    marginTop: 24,
    gap: 12,
    width: '100%',
  },
  successButton: {
    width: '100%',
  },
});

