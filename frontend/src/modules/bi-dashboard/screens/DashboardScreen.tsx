import React from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, Dimensions } from 'react-native';
import { Appbar, Text, FAB, Snackbar } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { PeriodFilter } from '../components/filters/PeriodFilter';
import { SummaryCards } from '../components/kpi/SummaryCards';
import { KPICard, KPICardSkeleton } from '../components/kpi/KPICard';
import { LineChartCard } from '../components/charts/LineChartCard';
import { BarChartCard } from '../components/charts/BarChartCard';
import { PieChartCard } from '../components/charts/PieChartCard';
import { ActivityFeed } from '../components/ActivityFeed';
import { TopProductsList, TopCustomersList } from '../components/TopLists';
import { AIInsightsPanel } from '../components/AIInsightsPanel';

import {
  useDashboardSummary,
  useRevenueAnalytics,
  useKPIMetrics,
  useSalesChart,
  useInventoryChart,
  useCustomerChart,
  useActivities,
  useTopProducts,
  useTopCustomers,
  useAIInsights,
  useSalesForecast,
  usePeriodFilter,
  useDashboardRefresh,
} from '../hooks/useDashboard';

import { KPI_ICONS, CHART_COLORS } from '../constants/dashboard';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export const DashboardScreen: React.FC = () => {
  const { t } = useTranslation();
  const { filter, setPeriod, setCompareWith } = usePeriodFilter();
  const lastRefresh = useDashboardRefresh(300000); // 5 minutes

  const {
    data: summary,
    loading: summaryLoading,
    refetch: refetchSummary,
  } = useDashboardSummary(filter);

  const { data: revenue, loading: revenueLoading } = useRevenueAnalytics(filter.period);
  const { data: kpis, loading: kpisLoading } = useKPIMetrics(filter.period);
  const { data: salesChart, loading: salesChartLoading } = useSalesChart('30d');
  const { data: inventoryChart, loading: inventoryChartLoading } = useInventoryChart();
  const { data: customerChart, loading: customerChartLoading } = useCustomerChart('30d');
  const { data: activities, loading: activitiesLoading } = useActivities(20, 'all');
  const { data: topProducts, loading: topProductsLoading } = useTopProducts(filter.period, 5);
  const { data: topCustomers, loading: topCustomersLoading } = useTopCustomers(filter.period, 5);
  const { data: insights, loading: insightsLoading } = useAIInsights(5);
  const { data: forecast, loading: forecastLoading } = useSalesForecast('30d');

  const [refreshing, setRefreshing] = React.useState(false);
  const [snackbarVisible, setSnackbarVisible] = React.useState(false);
  const [snackbarMessage, setSnackbarMessage] = React.useState('');

  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await Promise.all([
      refetchSummary(),
    ]);
    setRefreshing(false);
    setSnackbarMessage('Dashboard refreshed');
    setSnackbarVisible(true);
  }, [refetchSummary]);

  // Mock pie chart data for inventory distribution
  const inventoryPieData = summary ? [
    { name: 'Active', value: summary.products.total - summary.products.lowStock - summary.products.outOfStock, color: CHART_COLORS.success },
    { name: 'Low Stock', value: summary.products.lowStock, color: CHART_COLORS.warning },
    { name: 'Out of Stock', value: summary.products.outOfStock, color: CHART_COLORS.error },
  ] : [];

  return (
    <SafeAreaView style={styles.container}>
      <Appbar.Header>
        <Appbar.Content title={t('dashboard.title', 'Business Intelligence')} />
        <Appbar.Action
          icon="refresh"
          onPress={onRefresh}
          disabled={refreshing}
        />
        <Appbar.Action
          icon="filter-variant"
          onPress={() => {
            // Open advanced filter modal
          }}
        />
      </Appbar.Header>

      <PeriodFilter
        filter={filter}
        onPeriodChange={setPeriod}
        onCompareChange={setCompareWith}
      />

      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.scrollContent}
      >
        {/* Summary Cards */}
        <SummaryCards summary={summary} loading={summaryLoading} />

        {/* KPI Metrics */}
        <View style={styles.kpiRow}>
          {kpisLoading ? (
            <>
              <KPICardSkeleton />
              <KPICardSkeleton />
            </>
          ) : kpis ? (
            <>
              <KPICard
                title={t('dashboard.kpi.revenue', 'Revenue')}
                metric={kpis.revenue}
                type="currency"
                icon={KPI_ICONS.revenue}
                color={CHART_COLORS.revenue}
              />
              <KPICard
                title={t('dashboard.kpi.profitMargin', 'Profit Margin')}
                metric={kpis.profitMargin}
                type="percentage"
                icon={KPI_ICONS.profitMargin}
                color={CHART_COLORS.profit}
              />
              <KPICard
                title={t('dashboard.kpi.customerAcquisition', 'New Customers')}
                metric={kpis.customerAcquisition}
                type="number"
                icon={KPI_ICONS.customerAcquisition}
                color={CHART_COLORS.customers}
              />
              <KPICard
                title={t('dashboard.kpi.inventoryTurnover', 'Inventory Turnover')}
                metric={kpis.inventoryTurnover}
                type="number"
                icon={KPI_ICONS.inventoryTurnover}
                color={CHART_COLORS.inventory}
              />
              <KPICard
                title={t('dashboard.kpi.averageOrderValue', 'Avg Order Value')}
                metric={kpis.averageOrderValue}
                type="currency"
                icon={KPI_ICONS.averageOrderValue}
                color={CHART_COLORS.orders}
              />
              <KPICard
                title={t('dashboard.kpi.collectionPeriod', 'Collection Period')}
                metric={kpis.collectionPeriod}
                type="days"
                icon={KPI_ICONS.collectionPeriod}
                color={CHART_COLORS.info}
              />
            </>
          ) : null}
        </View>

        {/* Revenue Chart */}
        <LineChartCard
          title={t('dashboard.charts.revenue', 'Revenue Trend')}
          subtitle={filter.period.replace('_', ' ')}
          data={salesChart}
          loading={salesChartLoading}
          yAxisPrefix="$"
        />

        {/* Forecast Chart */}
        {forecast && (
          <LineChartCard
            title={t('dashboard.charts.forecast', 'Sales Forecast (AI)')}
            subtitle={`Accuracy: ${(forecast.accuracy * 100).toFixed(1)}% | Trend: ${forecast.trend}`}
            data={{
              labels: forecast.data.map(d => d.date.slice(5)),
              datasets: [
                {
                  label: 'Predicted',
                  data: forecast.data.map(d => d.predicted),
                  color: CHART_COLORS.primary,
                },
                {
                  label: 'Upper Bound',
                  data: forecast.data.map(d => d.upperBound),
                  color: `${CHART_COLORS.primary}50`,
                },
                {
                  label: 'Lower Bound',
                  data: forecast.data.map(d => d.lowerBound),
                  color: `${CHART_COLORS.primary}30`,
                },
              ],
            }}
            loading={forecastLoading}
            yAxisPrefix="$"
          />
        )}

        {/* Charts Row */}
        <View style={styles.chartsRow}>
          <View style={styles.chartHalf}>
            <BarChartCard
              title={t('dashboard.charts.inventory', 'Inventory Value')}
              data={inventoryChart}
              loading={inventoryChartLoading}
              height={180}
            />
          </View>
          <View style={styles.chartHalf}>
            <PieChartCard
              title={t('dashboard.charts.inventoryDist', 'Stock Status')}
              data={inventoryPieData}
              loading={summaryLoading}
              height={180}
            />
          </View>
        </View>

        {/* Customer Chart */}
        <LineChartCard
          title={t('dashboard.charts.customers', 'Customer Acquisition')}
          data={customerChart}
          loading={customerChartLoading}
        />

        {/* AI Insights */}
        <AIInsightsPanel
          insights={insights}
          loading={insightsLoading}
          maxItems={5}
        />

        {/* Top Lists Row */}
        <View style={styles.listsRow}>
          <View style={styles.listHalf}>
            <TopProductsList
              products={topProducts}
              loading={topProductsLoading}
              maxItems={5}
            />
          </View>
          <View style={styles.listHalf}>
            <TopCustomersList
              customers={topCustomers}
              loading={topCustomersLoading}
              maxItems={5}
            />
          </View>
        </View>

        {/* Activity Feed */}
        <ActivityFeed
          activities={activities}
          loading={activitiesLoading}
          maxItems={10}
        />

        <View style={styles.footer}>
          <Text variant="bodySmall" style={styles.footerText}>
            Last updated: {lastRefresh.toLocaleTimeString()}
          </Text>
        </View>
      </ScrollView>

      <FAB
        icon="chat"
        style={styles.fab}
        onPress={() => {
          // Open AI Copilot chat
        }}
        label={t('dashboard.askAI', 'Ask AI')}
      />

      <Snackbar
        visible={snackbarVisible}
        onDismiss={() => setSnackbarVisible(false)}
        duration={2000}
        action={{ label: 'OK', onPress: () => setSnackbarVisible(false) }}
      >
        {snackbarMessage}
      </Snackbar>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollContent: {
    paddingBottom: 80,
  },
  kpiRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 4,
  },
  chartsRow: {
    flexDirection: 'row',
    padding: 4,
  },
  chartHalf: {
    flex: 1,
    minWidth: SCREEN_WIDTH / 2 - 24,
  },
  listsRow: {
    flexDirection: 'row',
    padding: 4,
  },
  listHalf: {
    flex: 1,
    minWidth: SCREEN_WIDTH / 2 - 24,
  },
  footer: {
    padding: 16,
    alignItems: 'center',
  },
  footerText: {
    color: '#888',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
});

