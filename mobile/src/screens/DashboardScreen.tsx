import React from 'react';
import { View, ScrollView, StyleSheet, Dimensions } from 'react-native';
import { Text, Card, Avatar, ProgressBar, useTheme } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { LineChart, BarChart } from 'react-native-chart-kit';

const { width } = Dimensions.get('window');

const MOCK_KPI = [
  { label: 'Revenue', value: '3.2M MMK', change: '+12.5%', icon: 'cash-multiple', color: '#10B981' },
  { label: 'Invoices', value: '156', change: '+8', icon: 'file-document', color: '#3B82F6' },
  { label: 'Contacts', value: '2,847', change: '+45', icon: 'account-group', color: '#8B5CF6' },
  { label: 'Pipeline', value: '5.1M MMK', change: '+15%', icon: 'chart-line', color: '#F59E0B' },
];

const MOCK_CHART = {
  labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
  datasets: [
    { data: [45000, 52000, 48000, 61000, 58000, 72000] },
  ],
};

const MOCK_ACTIVITIES = [
  { user: 'Sarah Chen', action: 'created invoice', target: 'INV-2024-156', time: '5m ago', icon: 'file-plus' },
  { user: 'Mike Ross', action: 'updated contact', target: 'Acme Corp', time: '15m ago', icon: 'account-edit' },
  { user: 'AI Copilot', action: 'generated report', target: 'Q2 Analytics', time: '30m ago', icon: 'robot' },
  { user: 'Emma Wilson', action: 'completed project', target: 'Website Redesign', time: '45m ago', icon: 'check-circle' },
];

export default function DashboardScreen() {
  const theme = useTheme();

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text variant="headlineSmall" style={{ fontWeight: '700' }}>Dashboard</Text>
          <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
          </Text>
        </View>
        <Avatar.Text size={40} label="AJ" style={{ backgroundColor: theme.colors.primaryContainer }} />
      </View>

      {/* KPI Cards */}
      <View style={styles.kpiGrid}>
        {MOCK_KPI.map((kpi, index) => (
          <Card key={index} style={styles.kpiCard}>
            <Card.Content style={styles.kpiContent}>
              <View style={[styles.kpiIcon, { backgroundColor: kpi.color + '20' }]}>
                <Icon name={kpi.icon} size={20} color={kpi.color} />
              </View>
              <Text variant="titleLarge" style={{ fontWeight: '700', marginTop: 8 }}>
                {kpi.value}
              </Text>
              <View style={styles.kpiFooter}>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {kpi.label}
                </Text>
                <Text variant="bodySmall" style={{ color: kpi.color, fontWeight: '600' }}>
                  {kpi.change}
                </Text>
              </View>
            </Card.Content>
          </Card>
        ))}
      </View>

      {/* Revenue Chart */}
      <Card style={styles.chartCard}>
        <Card.Content>
          <Text variant="titleMedium" style={{ fontWeight: '600', marginBottom: 12 }}>
            Revenue Trend
          </Text>
          <BarChart
            data={MOCK_CHART}
            width={width - 64}
            height={180}
            chartConfig={{
              backgroundColor: theme.colors.surface,
              backgroundGradientFrom: theme.colors.surface,
              backgroundGradientTo: theme.colors.surface,
              decimalPlaces: 0,
              color: () => theme.colors.primary,
              labelColor: () => theme.colors.onSurfaceVariant,
              barPercentage: 0.6,
            }}
            style={{ borderRadius: 10 }}
            showValuesOnTopOfBars
            fromZero
          />
        </Card.Content>
      </Card>

      {/* Pipeline Progress */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <Text variant="titleMedium" style={{ fontWeight: '600', marginBottom: 12 }}>
            Sales Pipeline
          </Text>
          {[
            { stage: 'Lead', value: 12, total: 28, color: '#94A3B8' },
            { stage: 'Qualified', value: 8, total: 28, color: '#3B82F6' },
            { stage: 'Proposal', value: 5, total: 28, color: '#F59E0B' },
            { stage: 'Negotiation', value: 3, total: 28, color: '#8B5CF6' },
          ].map((item, i) => (
            <View key={i} style={{ marginBottom: 12 }}>
              <View style={styles.progressHeader}>
                <Text variant="bodyMedium">{item.stage}</Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {item.value} deals
                </Text>
              </View>
              <ProgressBar
                progress={item.value / item.total}
                color={item.color}
                style={styles.progressBar}
              />
            </View>
          ))}
        </Card.Content>
      </Card>

      {/* Recent Activity */}
      <Card style={styles.sectionCard}>
        <Card.Content>
          <Text variant="titleMedium" style={{ fontWeight: '600', marginBottom: 12 }}>
            Recent Activity
          </Text>
          {MOCK_ACTIVITIES.map((activity, i) => (
            <View key={i} style={styles.activityItem}>
              <View style={[styles.activityIcon, { backgroundColor: theme.colors.primaryContainer }]}>
                <Icon name={activity.icon} size={16} color={theme.colors.primary} />
              </View>
              <View style={styles.activityContent}>
                <Text variant="bodyMedium" style={{ fontWeight: '500' }}>
                  {activity.user} <Text style={{ color: theme.colors.onSurfaceVariant }}>{activity.action}</Text>{' '}
                  <Text style={{ color: theme.colors.primary }}>{activity.target}</Text>
                </Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {activity.time}
                </Text>
              </View>
            </View>
          ))}
        </Card.Content>
      </Card>

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 24,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 8,
    gap: 8,
  },
  kpiCard: {
    flex: 1,
    minWidth: width / 2 - 24,
    margin: 4,
  },
  kpiContent: {
    padding: 12,
  },
  kpiIcon: {
    width: 36,
    height: 36,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  kpiFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 4,
  },
  chartCard: {
    margin: 16,
    marginTop: 8,
  },
  sectionCard: {
    margin: 16,
    marginTop: 8,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
  },
  activityIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  activityContent: {
    flex: 1,
  },
});

