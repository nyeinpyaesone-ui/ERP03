import React from 'react';
import { View, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Card, Text, Button, Chip, useTheme, Divider, DataTable, ProgressBar } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { posKPIAPI } from '../../services/api/posApi';
import { usePOSStore } from '../../store/posStore';
import { POSKPI, PaymentMethod } from '../../types/pos';

export const POSReportsScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const { currentRegister, currentShift } = usePOSStore();
  const [period, setPeriod] = React.useState<'today' | 'week' | 'month'>('today');

  const { data: kpi } = useQuery<POSKPI>({
    queryKey: ['posKPI', period, currentRegister?.id, currentShift?.id],
    queryFn: () => posKPIAPI.getDashboard(currentRegister?.id, currentShift?.id),
  });

  const paymentMethodIcons: Record<PaymentMethod, string> = {
    cash: 'cash',
    card: 'credit-card',
    bank_transfer: 'bank',
    mobile_money: 'cellphone',
    credit: 'account-clock',
    gift_card: 'gift',
    coupon: 'ticket-percent',
  };

  const maxHourlySales = Math.max(...(kpi?.hourlySales.map((h) => h.sales) ?? [1]));

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text variant="headlineMedium" style={styles.title}>
            POS Reports
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

        {/* Summary Cards */}
        <View style={styles.kpiGrid}>
          <Card style={styles.kpiCard}>
            <Card.Content>
              <MaterialCommunityIcons name="cash-register" size={32} color={theme.colors.primary} />
              <Text variant="headlineSmall" style={styles.kpiValue}>
                {(kpi?.todaySales ?? 0).toLocaleString()} MMK
              </Text>
              <Text variant="bodySmall">Total Sales</Text>
            </Card.Content>
          </Card>
          <Card style={styles.kpiCard}>
            <Card.Content>
              <MaterialCommunityIcons name="receipt" size={32} color={theme.colors.secondary} />
              <Text variant="headlineSmall" style={styles.kpiValue}>
                {kpi?.todayTransactions ?? 0}
              </Text>
              <Text variant="bodySmall">Transactions</Text>
            </Card.Content>
          </Card>
          <Card style={styles.kpiCard}>
            <Card.Content>
              <MaterialCommunityIcons name="basket" size={32} color="#4caf50" />
              <Text variant="headlineSmall" style={styles.kpiValue}>
                {kpi?.todayItemsSold ?? 0}
              </Text>
              <Text variant="bodySmall">Items Sold</Text>
            </Card.Content>
          </Card>
          <Card style={styles.kpiCard}>
            <Card.Content>
              <MaterialCommunityIcons name="chart-line" size={32} color="#ff9800" />
              <Text variant="headlineSmall" style={styles.kpiValue}>
                {(kpi?.todayAverageTicket ?? 0).toLocaleString()} MMK
              </Text>
              <Text variant="bodySmall">Avg Ticket</Text>
            </Card.Content>
          </Card>
        </View>

        {/* Payment Breakdown */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Payment Methods" />
          <Card.Content>
            {kpi?.paymentMethodBreakdown.map((pm) => (
              <View key={pm.method} style={styles.paymentRow}>
                <View style={styles.paymentInfo}>
                  <MaterialCommunityIcons
                    name={paymentMethodIcons[pm.method] as any}
                    size={24}
                    color={theme.colors.primary}
                  />
                  <View style={styles.paymentText}>
                    <Text variant="bodyMedium" style={{ textTransform: 'capitalize' }}>
                      {pm.method.replace('_', ' ')}
                    </Text>
                    <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                      {pm.count} transactions
                    </Text>
                  </View>
                </View>
                <View style={styles.paymentAmount}>
                  <Text variant="bodyMedium" style={{ fontWeight: 'bold' }}>
                    {pm.amount.toLocaleString()} MMK
                  </Text>
                  <Text variant="bodySmall" style={{ opacity: 0.6 }}>
                    {pm.percentage}%
                  </Text>
                </View>
              </View>
            ))}
          </Card.Content>
        </Card>

        {/* Hourly Sales */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Hourly Sales" />
          <Card.Content>
            {kpi?.hourlySales.map((hour) => (
              <View key={hour.hour} style={styles.hourlyRow}>
                <Text variant="bodySmall" style={styles.hourLabel}>
                  {hour.hour.toString().padStart(2, '0')}:00
                </Text>
                <View style={styles.hourBarContainer}>
                  <ProgressBar
                    progress={maxHourlySales > 0 ? hour.sales / maxHourlySales : 0}
                    color={theme.colors.primary}
                    style={styles.hourBar}
                  />
                </View>
                <Text variant="bodySmall" style={styles.hourValue}>
                  {hour.sales.toLocaleString()}
                </Text>
              </View>
            ))}
          </Card.Content>
        </Card>

        {/* Top Products */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Top Products" />
          <Card.Content>
            <DataTable>
              <DataTable.Header>
                <DataTable.Title>Product</DataTable.Title>
                <DataTable.Title numeric>Qty</DataTable.Title>
                <DataTable.Title numeric>Revenue</DataTable.Title>
              </DataTable.Header>
              {kpi?.topProducts.map((product, index) => (
                <DataTable.Row key={product.productId}>
                  <DataTable.Cell>
                    <Text variant="bodyMedium">
                      {index + 1}. {product.productName}
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
  sectionCard: {
    marginBottom: 16,
  },
  paymentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  paymentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  paymentText: {
    marginLeft: 12,
  },
  paymentAmount: {
    alignItems: 'flex-end',
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
  hourValue: {
    width: 80,
    textAlign: 'right',
  },
});

