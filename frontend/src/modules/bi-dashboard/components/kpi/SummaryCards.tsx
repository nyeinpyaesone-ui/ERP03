import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Text, Divider } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { DashboardSummary } from '../types/dashboard';
import { formatCurrency, formatNumber, formatPercentage, getTrendColor, getTrendIcon } from '../utils/dashboard';
import { CHART_COLORS } from '../constants/dashboard';

interface SummaryCardsProps {
  summary: DashboardSummary | null;
  loading: boolean;
}

interface SummaryItemProps {
  icon: string;
  label: string;
  value: string;
  subValue: string;
  color: string;
  trend: number;
}

const SummaryItem: React.FC<SummaryItemProps> = ({ icon, label, value, subValue, color, trend }) => (
  <View style={styles.item}>
    <View style={[styles.iconContainer, { backgroundColor: `${color}15` }]}>
      <MaterialCommunityIcons name={icon as any} size={20} color={color} />
    </View>
    <View style={styles.itemContent}>
      <Text variant="titleMedium" style={styles.itemValue}>{value}</Text>
      <Text variant="bodySmall" style={styles.itemLabel}>{label}</Text>
      <View style={styles.trendRow}>
        <MaterialCommunityIcons
          name={getTrendIcon(trend) as any}
          size={12}
          color={getTrendColor(trend)}
        />
        <Text variant="bodySmall" style={{ color: getTrendColor(trend) }}>
          {formatPercentage(trend)} {subValue}
        </Text>
      </View>
    </View>
  </View>
);

export const SummaryCards: React.FC<SummaryCardsProps> = ({ summary, loading }) => {
  if (loading || !summary) {
    return (
      <Card style={styles.container}>
        <Card.Content>
          <View style={styles.skeletonRow}>
            {[1, 2, 3, 4].map(i => (
              <View key={i} style={styles.skeletonItem}>
                <View style={[styles.iconContainer, { backgroundColor: '#E0E0E0' }]} />
                <View style={{ height: 20, backgroundColor: '#E0E0E0', borderRadius: 4, width: '60%', marginTop: 8 }} />
                <View style={{ height: 14, backgroundColor: '#E0E0E0', borderRadius: 4, width: '40%', marginTop: 4 }} />
              </View>
            ))}
          </View>
        </Card.Content>
      </Card>
    );
  }

  const revenueTrend = summary.revenue.changePercent;
  const customerTrend = ((summary.customers.new - (summary.customers.total - summary.customers.new)) /
    (summary.customers.total - summary.customers.new || 1)) * 100;

  return (
    <Card style={styles.container}>
      <Card.Content>
        <View style={styles.row}>
          <SummaryItem
            icon="cash-multiple"
            label="Revenue"
            value={formatCurrency(summary.revenue.current)}
            subValue="vs last period"
            color={CHART_COLORS.revenue}
            trend={revenueTrend}
          />
          <Divider style={styles.divider} />
          <SummaryItem
            icon="file-document-outline"
            label="Invoices"
            value={formatNumber(summary.invoices.total)}
            subValue={`${summary.invoices.paid} paid`}
            color={CHART_COLORS.info}
            trend={summary.invoices.paid - summary.invoices.overdue}
          />
          <Divider style={styles.divider} />
          <SummaryItem
            icon="account-group"
            label="Customers"
            value={formatNumber(summary.customers.total)}
            subValue={`${summary.customers.new} new`}
            color={CHART_COLORS.customers}
            trend={customerTrend}
          />
          <Divider style={styles.divider} />
          <SummaryItem
            icon="package-variant-closed"
            label="Products"
            value={formatNumber(summary.products.total)}
            subValue={`${summary.products.lowStock} low stock`}
            color={CHART_COLORS.inventory}
            trend={-summary.products.lowStock}
          />
        </View>
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  container: {
    margin: 8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  item: {
    flex: 1,
    minWidth: 140,
    alignItems: 'center',
    padding: 8,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  itemContent: {
    alignItems: 'center',
    marginTop: 8,
  },
  itemValue: {
    fontWeight: 'bold',
  },
  itemLabel: {
    color: '#666',
    marginTop: 2,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  divider: {
    width: 1,
    marginVertical: 8,
  },
  skeletonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  skeletonItem: {
    flex: 1,
    alignItems: 'center',
    padding: 8,
  },
});

