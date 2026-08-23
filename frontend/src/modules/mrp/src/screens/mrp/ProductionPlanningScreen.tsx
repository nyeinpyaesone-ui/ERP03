import React from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Card, Text, FAB, useTheme, Chip, ProgressBar, IconButton } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { productionPlanAPI } from '../../services/api/mrpApi';
import { useMRPStore } from '../../store/mrpStore';
import { ProductionPlan, PlanStatus } from '../../types/mrp';

const STATUS_CONFIG: Record<PlanStatus, { label: string; color: string; icon: string }> = {
  draft: { label: 'Draft', color: '#9e9e9e', icon: 'pencil' },
  approved: { label: 'Approved', color: '#2196f3', icon: 'check' },
  active: { label: 'Active', color: '#4caf50', icon: 'play' },
  completed: { label: 'Completed', color: '#8bc34a', icon: 'check-circle' },
  cancelled: { label: 'Cancelled', color: '#f44336', icon: 'close' },
};

export const ProductionPlanningScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const { setSelectedPlan } = useMRPStore();

  const { data: plans, isLoading } = useQuery<ProductionPlan[]>({
    queryKey: ['productionPlans'],
    queryFn: () => productionPlanAPI.getAll(),
  });

  const renderPlan = ({ item }: { item: ProductionPlan }) => {
    const status = STATUS_CONFIG[item.status];
    const periodStart = new Date(item.period.startDate).toLocaleDateString();
    const periodEnd = new Date(item.period.endDate).toLocaleDateString();

    return (
      <TouchableOpacity
        onPress={() => {
          setSelectedPlan(item);
          navigation.navigate('ProductionPlanDetail' as never);
        }}
      >
        <Card style={styles.card}>
          <Card.Content>
            <View style={styles.cardHeader}>
              <View style={styles.headerLeft}>
                <Text variant="titleMedium" style={styles.planNumber}>
                  {item.planNumber}
                </Text>
                <Text variant="bodyMedium" style={styles.planName}>
                  {item.name}
                </Text>
              </View>
              <Chip
                style={[
                  styles.statusChip,
                  { backgroundColor: status.color + '20' },
                ]}
                textStyle={{ color: status.color }}
                icon={status.icon}
              >
                {status.label}
              </Chip>
            </View>

            <Text variant="bodySmall" style={styles.period}>
              {periodStart} → {periodEnd}
            </Text>

            <View style={styles.progressSection}>
              <View style={styles.progressHeader}>
                <Text variant="bodySmall">
                  {item.completedQuantity} / {item.totalQuantity} completed
                </Text>
                <Text variant="bodySmall" style={styles.progressText}>
                  {item.progress}%
                </Text>
              </View>
              <ProgressBar
                progress={item.progress / 100}
                color={status.color}
                style={styles.progressBar}
              />
            </View>

            <View style={styles.footer}>
              <View style={styles.footerItem}>
                <Text variant="bodySmall" style={styles.footerLabel}>
                  Work Orders
                </Text>
                <Text variant="titleSmall">{item.workOrders.length}</Text>
              </View>
              <View style={styles.footerItem}>
                <Text variant="bodySmall" style={styles.footerLabel}>
                  Remaining
                </Text>
                <Text variant="titleSmall">
                  {item.totalQuantity - item.completedQuantity}
                </Text>
              </View>
            </View>

            {item.status === 'draft' && (
              <View style={styles.actions}>
                <IconButton
                  icon="check"
                  mode="contained"
                  size={20}
                  onPress={() => productionPlanAPI.approve(item.id)}
                  style={styles.actionButton}
                />
                <IconButton
                  icon="delete"
                  mode="contained"
                  size={20}
                  containerColor={theme.colors.errorContainer}
                  iconColor={theme.colors.error}
                  onPress={() => productionPlanAPI.delete(item.id)}
                  style={styles.actionButton}
                />
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
        <Text variant="headlineMedium" style={styles.title}>
          Production Plans
        </Text>
      </View>

      <FlatList
        data={plans}
        renderItem={renderPlan}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        onPress={() => navigation.navigate('ProductionPlanCreate' as never)}
        label="New Plan"
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
  listContent: {
    padding: 16,
    paddingTop: 0,
  },
  card: {
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  headerLeft: {
    flex: 1,
  },
  planNumber: {
    fontWeight: 'bold',
  },
  planName: {
    opacity: 0.8,
    marginTop: 2,
  },
  statusChip: {
    marginLeft: 8,
  },
  period: {
    opacity: 0.6,
    marginBottom: 12,
  },
  progressSection: {
    marginBottom: 12,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  progressText: {
    fontWeight: '600',
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
  },
  footer: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingTop: 12,
  },
  footerItem: {
    flex: 1,
    alignItems: 'center',
  },
  footerLabel: {
    opacity: 0.5,
    marginBottom: 2,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    paddingTop: 8,
  },
  actionButton: {
    marginHorizontal: 4,
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});

