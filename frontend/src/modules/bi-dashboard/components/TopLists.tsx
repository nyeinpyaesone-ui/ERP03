import React from 'react';
import { View, StyleSheet, ScrollView, Image } from 'react-native';
import { Card, Text, Divider, Avatar } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { TopProduct, TopCustomer } from '../types/dashboard';
import { formatCurrency, formatNumber, formatDate } from '../utils/dashboard';
import { CHART_COLORS } from '../constants/dashboard';

interface TopProductsListProps {
  products: TopProduct[] | null;
  loading: boolean;
  maxItems?: number;
}

export const TopProductsList: React.FC<TopProductsListProps> = ({
  products,
  loading,
  maxItems = 5,
}) => {
  if (loading) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.title}>Top Products</Text>
          {[1, 2, 3, 4, 5].map(i => (
            <View key={i} style={styles.skeletonItem}>
              <View style={[styles.skeletonImage, { backgroundColor: '#E0E0E0' }]} />
              <View style={styles.skeletonContent}>
                <View style={{ height: 16, backgroundColor: '#E0E0E0', borderRadius: 4, width: '60%' }} />
                <View style={{ height: 12, backgroundColor: '#E0E0E0', borderRadius: 4, width: '40%', marginTop: 4 }} />
              </View>
            </View>
          ))}
        </Card.Content>
      </Card>
    );
  }

  if (!products || !products.length) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.title}>Top Products</Text>
          <Text variant="bodyMedium" style={styles.emptyText}>No sales data available</Text>
        </Card.Content>
      </Card>
    );
  }

  const displayProducts = products.slice(0, maxItems);

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.title}>Top Products</Text>
        <ScrollView nestedScrollEnabled>
          {displayProducts.map((product, index) => (
            <View key={product.productId}>
              <View style={styles.productItem}>
                <View style={styles.rankContainer}>
                  <Text variant="titleMedium" style={styles.rankText}>#{index + 1}</Text>
                </View>
                {product.image ? (
                  <Image source={{ uri: product.image }} style={styles.productImage} />
                ) : (
                  <View style={[styles.productImage, styles.productImagePlaceholder]}>
                    <MaterialCommunityIcons name="package-variant" size={20} color="#888" />
                  </View>
                )}
                <View style={styles.productContent}>
                  <Text variant="bodyMedium" style={styles.productName} numberOfLines={1}>
                    {product.productName}
                  </Text>
                  <Text variant="bodySmall" style={styles.productSku}>
                    {product.sku}
                  </Text>
                  <View style={styles.productMeta}>
                    <Text variant="bodySmall" style={styles.productQuantity}>
                      {formatNumber(product.quantitySold)} sold
                    </Text>
                    <Text variant="bodySmall" style={styles.productRevenue}>
                      {formatCurrency(product.revenue)}
                    </Text>
                  </View>
                </View>
              </View>
              {index < displayProducts.length - 1 && <Divider />}
            </View>
          ))}
        </ScrollView>
      </Card.Content>
    </Card>
  );
};

interface TopCustomersListProps {
  customers: TopCustomer[] | null;
  loading: boolean;
  maxItems?: number;
}

export const TopCustomersList: React.FC<TopCustomersListProps> = ({
  customers,
  loading,
  maxItems = 5,
}) => {
  if (loading) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.title}>Top Customers</Text>
          {[1, 2, 3, 4, 5].map(i => (
            <View key={i} style={styles.skeletonItem}>
              <View style={[styles.skeletonAvatar, { backgroundColor: '#E0E0E0' }]} />
              <View style={styles.skeletonContent}>
                <View style={{ height: 16, backgroundColor: '#E0E0E0', borderRadius: 4, width: '60%' }} />
                <View style={{ height: 12, backgroundColor: '#E0E0E0', borderRadius: 4, width: '40%', marginTop: 4 }} />
              </View>
            </View>
          ))}
        </Card.Content>
      </Card>
    );
  }

  if (!customers || !customers.length) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.title}>Top Customers</Text>
          <Text variant="bodyMedium" style={styles.emptyText}>No customer data available</Text>
        </Card.Content>
      </Card>
    );
  }

  const displayCustomers = customers.slice(0, maxItems);

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.title}>Top Customers</Text>
        <ScrollView nestedScrollEnabled>
          {displayCustomers.map((customer, index) => (
            <View key={customer.contactId}>
              <View style={styles.customerItem}>
                <View style={styles.rankContainer}>
                  <Text variant="titleMedium" style={styles.rankText}>#{index + 1}</Text>
                </View>
                <Avatar.Text
                  size={40}
                  label={customer.contactName.charAt(0).toUpperCase()}
                  style={{ backgroundColor: CHART_COLORS.customers }}
                />
                <View style={styles.customerContent}>
                  <Text variant="bodyMedium" style={styles.customerName} numberOfLines={1}>
                    {customer.contactName}
                  </Text>
                  <Text variant="bodySmall" style={styles.customerEmail}>
                    {customer.email}
                  </Text>
                  <View style={styles.customerMeta}>
                    <Text variant="bodySmall" style={styles.customerInvoices}>
                      {customer.invoiceCount} invoices
                    </Text>
                    <Text variant="bodySmall" style={styles.customerRevenue}>
                      {formatCurrency(customer.totalRevenue)}
                    </Text>
                  </View>
                </View>
              </View>
              {index < displayCustomers.length - 1 && <Divider />}
            </View>
          ))}
        </ScrollView>
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    margin: 8,
    flex: 1,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  productItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  customerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  rankContainer: {
    width: 30,
    alignItems: 'center',
  },
  rankText: {
    color: '#888',
    fontWeight: 'bold',
  },
  productImage: {
    width: 40,
    height: 40,
    borderRadius: 4,
    marginRight: 12,
  },
  productImagePlaceholder: {
    backgroundColor: '#F5F5F5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  productContent: {
    flex: 1,
  },
  productName: {
    fontWeight: '500',
  },
  productSku: {
    color: '#888',
  },
  productMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  productQuantity: {
    color: '#666',
  },
  productRevenue: {
    color: CHART_COLORS.success,
    fontWeight: 'bold',
  },
  customerContent: {
    flex: 1,
    marginLeft: 12,
  },
  customerName: {
    fontWeight: '500',
  },
  customerEmail: {
    color: '#888',
  },
  customerMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  customerInvoices: {
    color: '#666',
  },
  customerRevenue: {
    color: CHART_COLORS.success,
    fontWeight: 'bold',
  },
  emptyText: {
    color: '#888',
    textAlign: 'center',
    paddingVertical: 20,
  },
  skeletonItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
  skeletonImage: {
    width: 40,
    height: 40,
    borderRadius: 4,
    marginRight: 12,
  },
  skeletonAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    marginRight: 12,
  },
  skeletonContent: {
    flex: 1,
  },
});

