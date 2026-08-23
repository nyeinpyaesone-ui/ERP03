import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Text, ProgressBar, Chip, FAB, useTheme } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { manufacturingKPIAPI } from '../../services/api/mrpApi';
import { useMRPStore } from '../../store/mrpStore';
import { ManufacturingKPI } from '../../types/mrp';

export const MRPDashboardScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const { isLoading, setIsLoading } = useMRPStore();

  const { data: kpi } = useQuery<ManufacturingKPI>({
    queryKey: ['manufacturingKPI'],
    queryFn: () => manufacturingKPIAPI.getDashboard(),
  });

  const getStatusColor = (value: number, threshold: number) => {
    if (value >= threshold) return theme.colors.primary;
    if (value >= threshold * 0.7) return theme.colors.secondary;
    return theme.colors.error;
  };

  const kpiCards = [
    {
      title: 'Total Work Orders',
      value: kpi?.totalWorkOrders ?? 0,
      subtitle: `${kpi?.inProgressOrders ?? 0} in progress`,
      icon: 'clipboard-list',
    },
    {
      title: 'Completed',
      value: kpi?.completedOrders ?? 0,
      subtitle: `${kpi?.overdueOrders ?? 0} overdue`,
      icon: 'check-circle',
      color: kpi && kpi.overdueOrders > 0 ? theme.colors.error : undefined,
    },
    {
      title: 'Efficiency',
      value: `${kpi?.productionEfficiency ?? 0}%`,
      subtitle: 'Production efficiency',
      icon: 'chart-line',
      progress: (kpi?.productionEfficiency ?? 0) / 100,
    },
    {
      title: 'Material Variance',
      value: `${kpi?.materialVariance ?? 0}%`,
      subtitle: 'Cost variance',
      icon: 'scale-unbalanced',
      progress: Math.abs(kpi?.materialVariance ?? 0) / 100,
      color: kpi && Math.abs(kpi.materialVariance) > 5 ? theme.colors.error : undefined,
    },
  ];

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text variant="headlineMedium" style={styles.title}>
          Manufacturing Dashboard
        </Text>

        <View style={styles.kpiGrid}>
          {kpiCards.map((card, index) => (
            <Card key={index} style={styles.kpiCard}>
              <Card.Content>
                <View style={styles.kpiHeader}>
                  <Text variant="titleMedium" style={styles.kpiTitle}>
                    {card.title}
                  </Text>
                </View>
                <Text
                  variant="headlineLarge"
                  style={[styles.kpiValue, card.color && { color: card.color }]}
                >
                  {card.value}
                </Text>
                <Text variant="bodySmall" style={styles.kpiSubtitle}>
                  {card.subtitle}
                </Text>
                {card.progress !== undefined && (
                  <ProgressBar
                    progress={card.progress}
                    color={getStatusColor(card.progress * 100, 80)}
                    style={styles.progressBar}
                  />
                )}
              </Card.Content>
            </Card>
          ))}
        </View>

        <Card style={styles.sectionCard}>
          <Card.Title title="Quick Actions" />
          <Card.Content>
            <View style={styles.chipRow}>
              <Chip icon="plus" onPress={() => {}} style={styles.chip}>
                New Work Order
              </Chip>
              <Chip icon="file-document" onPress={() => {}} style={styles.chip}>
                Create BOM
              </Chip>
              <Chip icon="calculator" onPress={() => {}} style={styles.chip}>
                Run MRP
              </Chip>
            </View>
          </Card.Content>
        </Card>

        <Card style={styles.sectionCard}>
          <Card.Title
            title="Overdue Alerts"
            left={(props) => <Text {...props} style={{ color: theme.colors.error }}>⚠️</Text>}
          />
          <Card.Content>
            {kpi && kpi.overdueOrders > 0 ? (
              <Text style={{ color: theme.colors.error }}>
                {kpi.overdueOrders} work orders are overdue. Review and prioritize.
              </Text>
            ) : (
              <Text>All work orders are on schedule.</Text>
            )}
          </Card.Content>
        </Card>
      </ScrollView>

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        onPress={() => {}}
        label="New Work Order"
      />
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
  title: {
    marginBottom: 16,
    fontWeight: 'bold',
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
    marginBottom: 8,
  },
  kpiHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  kpiTitle: {
    opacity: 0.7,
  },
  kpiValue: {
    marginVertical: 8,
    fontWeight: 'bold',
  },
  kpiSubtitle: {
    opacity: 0.6,
  },
  progressBar: {
    marginTop: 8,
    height: 6,
    borderRadius: 3,
  },
  sectionCard: {
    marginBottom: 16,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    marginBottom: 8,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});

