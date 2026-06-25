import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Appbar, Card, Text, DataTable, Chip, ProgressBar, Button } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { PieChartCard } from '../components/charts/PieChartCard';
import { BarChartCard } from '../components/charts/BarChartCard';
import { useInventoryStats, useInventoryChart } from '../hooks/useDashboard';
import { useAnomalyDetection } from '../hooks/useDashboard';
import { formatCurrency, formatNumber } from '../utils/dashboard';
import { CHART_COLORS } from '../constants/dashboard';

export const InventoryDetailScreen: React.FC = () => {
  const { t } = useTranslation();
  const { data: stats, loading: statsLoading } = useInventoryStats();
  const { data: chart, loading: chartLoading } = useInventoryChart();
  const { data: anomalies, loading: anomaliesLoading } = useAnomalyDetection();

  const pieData = stats ? [
    { name: 'Active', value: stats.totalProducts - stats.lowStockCount - stats.outOfStockCount, color: CHART_COLORS.success },
    { name: 'Low Stock', value: stats.lowStockCount, color: CHART_COLORS.warning },
    { name: 'Out of Stock', value: stats.outOfStockCount, color: CHART_COLORS.error },
  ] : [];

  return (
    <SafeAreaView style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => {}} />
        <Appbar.Content title={t('inventory.analytics', 'Inventory Analytics')} />
      </Appbar.Header>

      <ScrollView>
        {/* Summary Cards */}
        <View style={styles.summaryRow}>
          <Card style={styles.summaryCard}>
            <Card.Content>
              <Text variant="bodySmall" style={styles.summaryLabel}>Total Products</Text>
              <Text variant="headlineSmall" style={styles.summaryValue}>
                {stats ? formatNumber(stats.totalProducts) : '--'}
              </Text>
            </Card.Content>
          </Card>
          <Card style={styles.summaryCard}>
            <Card.Content>
              <Text variant="bodySmall" style={styles.summaryLabel}>Stock Value</Text>
              <Text variant="headlineSmall" style={styles.summaryValue}>
                {stats ? formatCurrency(stats.totalStockValue) : '--'}
              </Text>
            </Card.Content>
          </Card>
          <Card style={styles.summaryCard}>
            <Card.Content>
              <Text variant="bodySmall" style={styles.summaryLabel}>Low Stock</Text>
              <Text variant="headlineSmall" style={[styles.summaryValue, { color: CHART_COLORS.warning }]}>
                {stats ? formatNumber(stats.lowStockCount) : '--'}
              </Text>
            </Card.Content>
          </Card>
        </View>

        {/* Alerts */}
        {anomalies && anomalies.length > 0 && (
          <Card style={styles.alertCard}>
            <Card.Content>
              <Text variant="titleMedium" style={styles.alertTitle}>⚠️ Anomalies Detected</Text>
              {anomalies.map(anomaly => (
                <View key={anomaly.id} style={styles.alertItem}>
                  <Chip
                    compact
                    style={[
                      styles.severityChip,
                      { backgroundColor: anomaly.severity === 'high' ? '#FFEBEE' : '#FFF3E0' },
                    ]}
                    textStyle={{
                      color: anomaly.severity === 'high' ? CHART_COLORS.error : CHART_COLORS.warning,
                    }}
                  >
                    {anomaly.severity}
                  </Chip>
                  <Text variant="bodyMedium" style={styles.alertText}>
                    {anomaly.description}
                  </Text>
                </View>
              ))}
            </Card.Content>
          </Card>
        )}

        {/* Charts */}
        <View style={styles.chartsRow}>
          <View style={styles.chartHalf}>
            <PieChartCard
              title="Stock Distribution"
              data={pieData}
              loading={statsLoading}
              height={200}
            />
          </View>
          <View style={styles.chartHalf}>
            <BarChartCard
              title="Value by Category"
              data={chart}
              loading={chartLoading}
              height={200}
            />
          </View>
        </View>

        {/* Category Breakdown */}
        <Card style={styles.tableCard}>
          <Card.Content>
            <Text variant="titleMedium" style={styles.tableTitle}>Category Breakdown</Text>
            <DataTable>
              <DataTable.Header>
                <DataTable.Title>Category</DataTable.Title>
                <DataTable.Title numeric>Products</DataTable.Title>
                <DataTable.Title numeric>Stock Value</DataTable.Title>
                <DataTable.Title numeric>% of Total</DataTable.Title>
              </DataTable.Header>
              {stats?.topCategories.map((cat, index) => (
                <DataTable.Row key={index}>
                  <DataTable.Cell>{cat.category}</DataTable.Cell>
                  <DataTable.Cell numeric>{cat.productCount}</DataTable.Cell>
                  <DataTable.Cell numeric>{formatCurrency(cat.stockValue)}</DataTable.Cell>
                  <DataTable.Cell numeric>
                    <ProgressBar
                      progress={cat.stockValue / (stats?.totalStockValue || 1)}
                      color={CHART_COLORS.primary}
                      style={styles.progressBar}
                    />
                  </DataTable.Cell>
                </DataTable.Row>
              ))}
            </DataTable>
          </Card.Content>
        </Card>

        {/* Actions */}
        <View style={styles.actionsRow}>
          <Button
            mode="contained"
            icon="alert-circle"
            onPress={() => {}}
            style={styles.actionButton}
          >
            View Low Stock
          </Button>
          <Button
            mode="outlined"
            icon="file-export"
            onPress={() => {}}
            style={styles.actionButton}
          >
            Export Report
          </Button>
        </View>
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
  alertCard: {
    margin: 8,
    backgroundColor: '#FFF8E1',
  },
  alertTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
    color: CHART_COLORS.warning,
  },
  alertItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginVertical: 4,
  },
  severityChip: {
    height: 24,
  },
  alertText: {
    flex: 1,
  },
  chartsRow: {
    flexDirection: 'row',
    padding: 4,
  },
  chartHalf: {
    flex: 1,
  },
  tableCard: {
    margin: 8,
  },
  tableTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  progressBar: {
    width: 60,
    height: 6,
  },
  actionsRow: {
    flexDirection: 'row',
    padding: 8,
    gap: 8,
    marginBottom: 16,
  },
  actionButton: {
    flex: 1,
  },
});

