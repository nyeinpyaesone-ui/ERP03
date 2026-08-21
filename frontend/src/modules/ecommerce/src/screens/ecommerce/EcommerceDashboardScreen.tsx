import React from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Card, Text, Chip, useTheme, ProgressBar, Button, DataTable, Divider } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ecommerceKPIAPI } from '../../services/api/ecommerceApi';
import { EcommerceKPI } from '../../types/ecommerce';

export const EcommerceDashboardScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const [period, setPeriod] = React.useState<'today' | 'week' | 'month'>('today');

  const { data: kpi } = useQuery<EcommerceKPI>({
    queryKey: ['ecommerceKPI', period],
    queryFn: () => ecommerceKPIAPI.getDashboard(period),
  });

  const kpiCards = [
    {
      title: 'Orders',
      value: kpi?.todayOrders ?? 0,
      icon: 'receipt',
      color: theme.colors.primary,
    },
    {
      title: 'Revenue',
      value: `${(kpi?.todayRevenue ?? 0).toLocaleString()} MMK`,
      icon: 'cash',
      color: '#4caf50',
    },
    {
      title: 'Visitors',
      value: kpi?.todayVisitors ?? 0,
      icon: 'account-group',
      color: '#2196f3',
    },
    {
      title: 'Conversion',
      value: `${kpi?.todayConversionRate ?? 0}%`,
      icon: 'chart-line',
      color: '#ff9800',
    },
  ];

  const maxHourlySales = Math.max(...(kpi?.salesByHour.map((h) => h.revenue) ?? [1]));

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text variant="headlineMedium" style={styles.title}>
            E-commerce Dashboard
          </Text>
          <View style={styles.periodRow}>
            {(['today', 'week', 'month'] as const).map((p) => (
              <Chip
                key={p}
                selected={period === p}
                onPress={() => setPeriod(p)}
                style={styles.periodChip}
                showSelectedCheck={false}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </Chip>
            ))}
          </View>
        </View>

        {/* KPI Cards */}
        <View style={styles.kpiGrid}>
          {kpiCards.map((card, index) => (
            <Card key={index} style={styles.kpiCard}>
              <Card.Content>
                <MaterialCommunityIcons name={card.icon as any} size={32} color={card.color} />
                <Text variant="headlineSmall" style={[styles.kpiValue, { color: card.color }]}>
                  {card.value}
                </Text>
                <Text variant="bodySmall" style={styles.kpiLabel}>
                  {card.title}
                </Text>
              </Card.Content>
            </Card>
          ))}
        </View>

        {/* Quick Actions */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Quick Actions" />
          <Card.Content>
            <View style={styles.actionsRow}>
              <Button
                mode="outlined"
                icon="plus"
                onPress={() => navigation.navigate('ProductCreate' as never)}
                style={styles.actionButton}
              >
                Add Product
              </Button>
              <Button
                mode="outlined"
                icon="tag"
                onPress={() => navigation.navigate('CouponCreate' as never)}
                style={styles.actionButton}
              >
                Create Coupon
              </Button>
              <Button
                mode="outlined"
                icon="truck"
                onPress={() => navigation.navigate('ShippingSettings' as never)}
                style={styles.actionButton}
              >
                Shipping
              </Button>
            </View>
          </Card.Content>
        </Card>

        {/* Top Products */}
        <Card style={styles.sectionCard}>
          <Card.Title
            title="Top Selling Products"
            right={(props) => (
              <Button {...props} mode="text" compact onPress={() => {}}>
                View All
              </Button>
            )}
          />
          <Card.Content>
            <DataTable>
              <DataTable.Header>
                <DataTable.Title>Product</DataTable.Title>
                <DataTable.Title numeric>Qty</DataTable.Title>
                <DataTable.Title numeric>Revenue</DataTable.Title>
              </DataTable.Header>
              {kpi?.topProducts.map((product) => (
                <DataTable.Row key={product.productId}>
                  <DataTable.Cell>
                    <Text variant="bodyMedium" numberOfLines={1}>
                      {product.productName}
                    </Text>
                  </DataTable.Cell>
                  <DataTable.Cell numeric>{product.quantity}</DataTable.Cell>
                  <DataTable.Cell numeric>
                    {product.revenue.toLocaleString()} MMK
                  </DataTable.Cell>
                </DataTable.Row>
              ))}
            </DataTable>
          </Card.Content>
        </Card>

        {/* Top Categories */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Top Categories" />
          <Card.Content>
            {kpi?.topCategories.map((category) => (
              <View key={category.categoryId} style={styles.categoryRow}>
                <View style={styles.categoryInfo}>
                  <Text variant="bodyMedium" style={styles.categoryName}>
                    {category.categoryName}
                  </Text>
                  <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                    {category.orderCount} orders
                  </Text>
                </View>
                <Text variant="bodyMedium" style={styles.categoryRevenue}>
                  {category.revenue.toLocaleString()} MMK
                </Text>
              </View>
            ))}
          </Card.Content>
        </Card>

        {/* Hourly Sales */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Hourly Sales" />
          <Card.Content>
            {kpi?.salesByHour.map((hour) => (
              <View key={hour.hour} style={styles.hourlyRow}>
                <Text variant="bodySmall" style={styles.hourLabel}>
                  {hour.hour.toString().padStart(2, '0')}:00
                </Text>
                <View style={styles.hourBarContainer}>
                  <ProgressBar
                    progress={maxHourlySales > 0 ? hour.revenue / maxHourlySales : 0}
                    color={theme.colors.primary}
                    style={styles.hourBar}
                  />
                </View>
                <View style={styles.hourStats}>
                  <Text variant="bodySmall" style={styles.hourRevenue}>
                    {hour.revenue.toLocaleString()} MMK
                  </Text>
                  <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                    {hour.orders} orders
                  </Text>
                </View>
              </View>
            ))}
          </Card.Content>
        </Card>

        {/* Abandoned Carts */}
        <Card style={[styles.sectionCard, { backgroundColor: theme.colors.errorContainer }]}>
          <Card.Title
            title="Abandoned Carts"
            left={(props) => <MaterialCommunityIcons {...props} name="cart-off" size={24} color={theme.colors.error} />}
          />
          <Card.Content>
            <View style={styles.abandonedRow}>
              <View>
                <Text variant="titleLarge" style={{ color: theme.colors.error, fontWeight: 'bold' }}>
                  {kpi?.abandonedCarts ?? 0}
                </Text>
                <Text variant="bodySmall">Abandoned carts</Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <Text variant="titleLarge" style={{ color: theme.colors.error, fontWeight: 'bold' }}>
                  {(kpi?.abandonedCartValue ?? 0).toLocaleString()} MMK
                </Text>
                <Text variant="bodySmall">Potential revenue lost</Text>
              </View>
            </View>
          </Card.Content>
        </Card>
      </ScrollView>
    </View>
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
  header: {
    marginBottom: 16,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  periodRow: {
    flexDirection: 'row',
    gap: 8,
  },
  periodChip: {
    marginBottom: 8,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  kpiCard: {
    flex: 1,
    minWidth: '45%',
  },
  kpiValue: {
    marginTop: 8,
    fontWeight: 'bold',
  },
  kpiLabel: {
    opacity: 0.6,
    marginTop: 4,
  },
  sectionCard: {
    marginBottom: 16,
  },
  actionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  actionButton: {
    marginBottom: 8,
  },
  categoryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontWeight: '500',
  },
  categoryRevenue: {
    fontWeight: 'bold',
    color: '#6200ee',
  },
  hourlyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  hourLabel: {
    width: 50,
  },
  hourBarContainer: {
    flex: 1,
    marginHorizontal: 12,
  },
  hourBar: {
    height: 8,
    borderRadius: 4,
  },
  hourStats: {
    alignItems: 'flex-end',
    minWidth: 80,
  },
  hourRevenue: {
    fontWeight: '500',
  },
  abandonedRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
});

