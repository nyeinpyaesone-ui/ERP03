import React from 'react';
import { View, StyleSheet, Modal, ScrollView } from 'react-native';
import { Card, Text, Button, TextInput, Chip, Divider, IconButton, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { usePOSStore } from '../../store/posStore';
import { posSaleAPI } from '../../services/api/posApi';
import { PaymentMethod, Payment } from '../../types/pos';

const PAYMENT_METHODS: { method: PaymentMethod; label: string; icon: string }[] = [
  { method: 'cash', label: 'Cash', icon: 'cash' },
  { method: 'card', label: 'Card', icon: 'credit-card' },
  { method: 'bank_transfer', label: 'Bank Transfer', icon: 'bank' },
  { method: 'mobile_money', label: 'Mobile Money', icon: 'cellphone' },
  { method: 'credit', label: 'Credit', icon: 'account-clock' },
];

export const PaymentModal: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const { cart, showPaymentModal, setShowPaymentModal, clearCart, currentShift, currentRegister } = usePOSStore();

  const [selectedMethod, setSelectedMethod] = React.useState<PaymentMethod>('cash');
  const [receivedAmount, setReceivedAmount] = React.useState('');
  const [reference, setReference] = React.useState('');
  const [payments, setPayments] = React.useState<Payment[]>([]);

  const remainingAmount = React.useMemo(() => {
    const paid = payments.reduce((sum, p) => sum + p.amount, 0);
    return Math.max(0, cart.total - paid);
  }, [cart.total, payments]);

  const changeAmount = React.useMemo(() => {
    const paid = payments.reduce((sum, p) => sum + p.amount, 0);
    return Math.max(0, paid - cart.total);
  }, [cart.total, payments]);

  const saleMutation = useMutation({
    mutationFn: () =>
      posSaleAPI.create({
        cart,
        registerId: currentRegister!.id,
        shiftId: currentShift!.id,
        customerId: cart.customerId,
      }),
    onSuccess: () => {
      clearCart();
      setPayments([]);
      setShowPaymentModal(false);
      setReceivedAmount('');
      setReference('');
    },
  });

  const addPayment = () => {
    const amount = parseFloat(receivedAmount) || remainingAmount;
    if (amount <= 0) return;

    const newPayment: Payment = {
      id: `payment-${Date.now()}`,
      method: selectedMethod,
      amount: Math.min(amount, remainingAmount),
      receivedAmount: amount,
      changeAmount: selectedMethod === 'cash' ? Math.max(0, amount - remainingAmount) : 0,
      reference: reference || undefined,
      status: 'completed',
      processedAt: new Date().toISOString(),
    };

    setPayments([...payments, newPayment]);
    setReceivedAmount('');
    setReference('');
  };

  const removePayment = (paymentId: string) => {
    setPayments(payments.filter((p) => p.id !== paymentId));
  };

  const handleCompleteSale = () => {
    if (remainingAmount > 0.01) return;
    saleMutation.mutate();
  };

  return (
    <Modal
      visible={showPaymentModal}
      animationType="slide"
      transparent
      onRequestClose={() => setShowPaymentModal(false)}
    >
      <View style={styles.modalOverlay}>
        <Card style={styles.modalCard}>
          <Card.Title
            title="Payment"
            right={(props) => (
              <IconButton
                {...props}
                icon="close"
                onPress={() => setShowPaymentModal(false)}
              />
            )}
          />
          <Card.Content>
            <View style={styles.amountSection}>
              <Text variant="headlineMedium" style={styles.totalAmount}>
                {cart.total.toLocaleString()} MMK
              </Text>
              <Text variant="bodyMedium" style={styles.remainingAmount}>
                {remainingAmount > 0.01
                  ? `Remaining: ${remainingAmount.toLocaleString()} MMK`
                  : 'Fully Paid'}
              </Text>
            </View>

            <Divider style={styles.divider} />

            <Text variant="titleSmall" style={styles.sectionTitle}>
              Payment Method
            </Text>
            <View style={styles.methodsRow}>
              {PAYMENT_METHODS.map((pm) => (
                <Chip
                  key={pm.method}
                  selected={selectedMethod === pm.method}
                  onPress={() => setSelectedMethod(pm.method)}
                  style={styles.methodChip}
                  icon={pm.icon}
                  showSelectedCheck={false}
                >
                  {pm.label}
                </Chip>
              ))}
            </View>

            <TextInput
              mode="outlined"
              label="Amount Received"
              value={receivedAmount}
              onChangeText={setReceivedAmount}
              keyboardType="numeric"
              placeholder={remainingAmount.toString()}
              style={styles.input}
            />

            {selectedMethod !== 'cash' && (
              <TextInput
                mode="outlined"
                label="Reference Number"
                value={reference}
                onChangeText={setReference}
                style={styles.input}
              />
            )}

            <Button
              mode="outlined"
              onPress={addPayment}
              disabled={!receivedAmount && remainingAmount <= 0}
              style={styles.addPaymentButton}
            >
              Add Payment
            </Button>

            {payments.length > 0 && (
              <View style={styles.paymentsList}>
                <Text variant="titleSmall" style={styles.sectionTitle}>
                  Payments
                </Text>
                {payments.map((payment) => (
                  <View key={payment.id} style={styles.paymentItem}>
                    <View style={styles.paymentInfo}>
                      <Text variant="bodyMedium">
                        {PAYMENT_METHODS.find((m) => m.method === payment.method)?.label}
                      </Text>
                      {payment.reference && (
                        <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                          Ref: {payment.reference}
                        </Text>
                      )}
                    </View>
                    <View style={styles.paymentAmount}>
                      <Text variant="bodyMedium" style={{ fontWeight: 'bold' }}>
                        {payment.amount.toLocaleString()} MMK
                      </Text>
                      {payment.changeAmount > 0 && (
                        <Text variant="bodySmall" style={{ color: theme.colors.primary }}>
                          Change: {payment.changeAmount.toLocaleString()} MMK
                        </Text>
                      )}
                    </View>
                    <IconButton
                      icon="delete"
                      size={20}
                      onPress={() => removePayment(payment.id)}
                      iconColor={theme.colors.error}
                    />
                  </View>
                ))}
              </View>
            )}

            {changeAmount > 0 && (
              <View style={styles.changeSection}>
                <Text variant="titleMedium" style={{ color: theme.colors.primary }}>
                  Change: {changeAmount.toLocaleString()} MMK
                </Text>
              </View>
            )}

            <Divider style={styles.divider} />

            <Button
              mode="contained"
              onPress={handleCompleteSale}
              loading={saleMutation.isPending}
              disabled={remainingAmount > 0.01 || cart.items.length === 0}
              style={styles.completeButton}
              contentStyle={styles.completeButtonContent}
              icon="check-circle"
            >
              Complete Sale
            </Button>
          </Card.Content>
        </Card>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalCard: {
    width: '100%',
    maxWidth: 500,
    maxHeight: '90%',
  },
  amountSection: {
    alignItems: 'center',
    marginVertical: 16,
  },
  totalAmount: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  remainingAmount: {
    marginTop: 4,
    opacity: 0.7,
  },
  divider: {
    marginVertical: 16,
  },
  sectionTitle: {
    marginBottom: 12,
    fontWeight: '500',
  },
  methodsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  methodChip: {
    marginBottom: 8,
  },
  input: {
    marginBottom: 12,
  },
  addPaymentButton: {
    marginBottom: 16,
  },
  paymentsList: {
    marginBottom: 16,
  },
  paymentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  paymentInfo: {
    flex: 1,
  },
  paymentAmount: {
    alignItems: 'flex-end',
    marginRight: 8,
  },
  changeSection: {
    alignItems: 'center',
    paddingVertical: 12,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    marginBottom: 16,
  },
  completeButton: {
    marginTop: 8,
  },
  completeButtonContent: {
    paddingVertical: 8,
  },
});

