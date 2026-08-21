import React from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Card, Text, Chip, useTheme, SegmentedButtons, Badge, Button, IconButton } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ecommerceOrderAPI } from '../../services/api/ecommerceApi';
import { useEcommerceStore } from '../../store/ecommerceStore';
import { StoreOrder, OrderStatus, PaymentStatus, FulfillmentStatus } from '../../types/ecommerce';

const STATUS_CONFIG: Record<OrderStatus, { label: string; color: string; icon: string }> = {
  pending: { label: 'Pending', color: '#ff9800', icon: 'clock' },
  confirmed: { label: 'Confirmed', color: '#2196f3', icon: 'check' },
  processing: { label: 'Processing', color: '#9c27b0', icon: 'cog' },
  shipped: { label: 'Shipped', color: '#03a9f4', icon: 'truck' },
  delivered: { label: 'Delivered', color: '#4caf50', icon: 'package-variant-delivered' },
  cancelled: { label: 'Cancelled', color: '#f44336', icon: 'close-circle' },
  refunded: { label: 'Refunded', color: '#9e9e9e', icon: 'cash-refund' },
  partially_refunded: { label: 'Partially Refunded', color: '#ff9800', icon: 'cash-refund' },
};

export const OrdersScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const { setSelectedOrder } = useEcommerceStore();
  const [statusFilter, setStatusFilter] = React.useState<string>('all');
  const [page, setPage] = React.useState(1);

  const { data: ordersData } = useQuery({
    queryKey: ['orders', statusFilter, page],
    queryFn: () =>
      ecommerceOrderAPI.getAll(
        statusFilter !== 'all' ? { status: statusFilter, page, limit: 10 } : { page, limit: 10 }
      ),
  });

  const renderOrder = ({ item }: { item: StoreOrder }) => {
    const status = STATUS_CONFIG[item.status];
    const isCancelled = item.status === 'cancelled' || item.status === 'refunded';

    return (
      <TouchableOpacity
        onPress={() => {
          setSelectedOrder(item);
          navigation.navigate('OrderDetail', { id: item.id } as never);
        }}
      >
        <Card style={[styles.orderCard, isCancelled && styles.cancelledCard]}>
          <Card.Content>
            <View style={styles.orderHeader}>
              <View>
                <Text variant="titleMedium" style={styles.orderNumber}>
                  #{item.orderNumber}
                </Text>
                <Text variant="bodySmall" style={styles.orderDate}>
                  {new Date(item.createdAt).toLocaleDateString()} • {item.items.length} item(s)
                </Text>
              </View>
              <Chip
                style={[styles.statusChip, { backgroundColor: status.color + '20' }]}
                textStyle={{ color: status.color }}
                icon={status.icon}
              >
                {status.label}
              </Chip>
            </View>

            <View style={styles.itemsPreview}>
              {item.items.slice(0, 3).map((orderItem, index) => (
                <View key={orderItem.id} style={styles.itemPreview}>
                  <Text variant="bodySmall" numberOfLines={1}>
                    {orderItem.productName} x{orderItem.quantity}
                  </Text>
                </View>
              ))}
              {item.items.length > 3 && (
                <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                  +{item.items.length - 3} more items
                </Text>
              )}
            </View>

            <View style={styles.orderFooter}>
              <View style={styles.paymentInfo}>
                <MaterialCommunityIcons
                  name={item.paymentStatus === 'paid' ? 'check-circle' : 'clock'}
                  size={16}
                  color={item.paymentStatus === 'paid' ? '#4caf50' : '#ff9800'}
                />
                <Text variant="bodySmall" style={{ marginLeft: 4, opacity: 0.7 }}>
                  {item.paymentStatus === 'paid' ? 'Paid' : 'Payment Pending'}
                </Text>
              </View>
              <Text variant="titleMedium" style={styles.orderTotal}>
                {item.total.toLocaleString()} MMK
              </Text>
            </View>

            {item.fulfillmentStatus === 'fulfilled' && item.shippedAt && (
              <View style={styles.trackingInfo}>
                <MaterialCommunityIcons name="truck" size={16} color="#03a9f4" />
                <Text variant="bodySmall" style={{ marginLeft: 4, color: '#03a9f4' }}>
                  Shipped on {new Date(item.shippedAt).toLocaleDateString()}
                </Text>
              </View>
            )}
          </Card.Content>
        </Card>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text variant="headlineSmall" style={styles.title}>
          My Orders
        </Text>
      </View>

      <SegmentedButtons
        value={statusFilter}
        onValueChange={setStatusFilter}
        buttons={[
          { value: 'all', label: 'All' },
          { value: 'pending', label: 'Pending' },
          { value: 'shipped', label: 'Shipped' },
          { value: 'delivered', label: 'Delivered' },
        ]}
        style={styles.segmentedButtons}
      />

      <FlatList
        data={ordersData?.orders}
        renderItem={renderOrder}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <MaterialCommunityIcons name="package-variant" size={64} color={theme.colors.outline} />
            <Text variant="bodyLarge" style={{ opacity: 0.5, marginTop: 16 }}>
              No orders found
            </Text>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('ProductCatalog' as never)}
              style={{ marginTop: 16 }}
            >
              Start Shopping
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
  header: {
    padding: 16,
    paddingBottom: 8,
  },
  title: {
    fontWeight: 'bold',
  },
  segmentedButtons: {
    marginHorizontal: 16,
    marginBottom: 8,
  },
  listContent: {
    padding: 16,
    paddingTop: 0,
  },
  orderCard: {
    marginBottom: 12,
  },
  cancelledCard: {
    opacity: 0.7,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  orderNumber: {
    fontWeight: 'bold',
  },
  orderDate: {
    opacity: 0.6,
    marginTop: 2,
  },
  statusChip: {
    marginLeft: 8,
  },
  itemsPreview: {
    marginBottom: 12,
  },
  itemPreview: {
    paddingVertical: 4,
  },
  orderFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    paddingTop: 12,
  },
  paymentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  orderTotal: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  trackingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
});

