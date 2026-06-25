import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Appbar, Card, Text, DataTable, Chip } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { LineChartCard } from '../components/charts/LineChartCard';
import { BarChartCard } from '../components/charts/BarChartCard';
import { useRevenueAnalytics, useSalesChart } from '../hooks/useDashboard';
import { formatCurrency, formatDate } from '../utils/dashboard';
import { CHART_COLORS } from '../constants/dashboard';

export const RevenueDetailScreen: React.FC<{ route?: any }> = ({ route }) => {
  const { t } = useTranslation();
  const period = route?.params?.period || 'this_month';
  const groupBy = route?.params?.groupBy || 'daily';

  const { data: revenue, loading: revenueLoading } = useRevenueAnalytics(period);
  const { data: salesChart, loading: salesChartLoading } = useSalesChart('90d');

  return (
    <SafeAreaView style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => {}} />
        <Appbar.Content title={t('revenue.title', 'Revenue Analytics')} />
      </Appbar.Header>

      <ScrollView>
        {/* Summary Cards */}
        <View style={styles.summaryRow}>
          <Card style={styles.summaryCard}>
            <Card.Content>
              <Text variant="bodySmall" style={styles.summaryLabel}>Total Revenue</Text>
              <Text variant="headlineSmall" style={styles.summaryValue}>
                {revenue ? formatCurrency(revenue.total) : '--'}
              </Text>
              <Chip compact style={styles.chip}>
                {revenue ? `${revenue.growth > 0 ? '+' : ''}${revenue.growth.toFixed(1)}%` : '--'}
              </Chip>
            </Card.Content>
          </Card>
          <Card style={styles.summaryCard}>
            <Card.Content>
              <Text variant="bodySmall" style={styles.summaryLabel}>Average Daily</Text>
              <Text variant="headlineSmall" style={styles.summaryValue}>
                {revenue ? formatCurrency(revenue.average) : '--'}
              </Text>
            </Card.Content>
          </Card>
        </View>

        {/* Revenue Trend */}
        <LineChartCard
          title="Revenue Trend"
          subtitle={`Period: ${period}`}
          data={salesChart}
          loading={salesChartLoading}
          height={280}
          yAxisPrefix="$"
        />

        {/* Revenue by Category */}
        <BarChartCard
          title="Revenue by Category"
          data={salesChart}
          loading={salesChartLoading}
          height={250}
        />

        {/* Detailed Table */}
        <Card style={styles.tableCard}>
          <Card.Content>
            <Text variant="titleMedium" style={styles.tableTitle}>Daily Breakdown</Text>
            <DataTable>
              <DataTable.Header>
                <DataTable.Title>Date</DataTable.Title>
                <DataTable.Title numeric>Revenue</DataTable.Title>
                <DataTable.Title numeric>Invoices</DataTable.Title>
                <DataTable.Title numeric>Orders</DataTable.Title>
              </DataTable.Header>
              {revenue?.data.map((row, index) => (
                <DataTable.Row key={index}>
                  <DataTable.Cell>{formatDate(row.date)}</DataTable.Cell>
                  <DataTable.Cell numeric>{formatCurrency(row.revenue)}</DataTable.Cell>
                  <DataTable.Cell numeric>{row.invoices}</DataTable.Cell>
                  <DataTable.Cell numeric>{row.orders}</DataTable.Cell>
                </DataTable.Row>
              ))}
            </DataTable>
          </Card.Content>
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  summaryRow: {
    flexDirection: 'row',
    padding: 8,
    gap: 8,
  },
  summaryCard: {
    flex: 1,
  },
  summaryLabel: {
    color: '#666',
  },
  summaryValue: {
    fontWeight: 'bold',
    marginVertical: 8,
  },
  chip: {
    alignSelf: 'flex-start',
    backgroundColor: '#E8F5E9',
  },
  tableCard: {
    margin: 8,
  },
  tableTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
});

