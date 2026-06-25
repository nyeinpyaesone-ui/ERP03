import React from 'react';
import { View, StyleSheet, FlatList, ScrollView } from 'react-native';
import { Card, Text, Button, useTheme, Chip, DataTable, Divider } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import { mrpAPI } from '../../services/api/mrpApi';
import { useMRPStore } from '../../store/mrpStore';
import { MRPCalculation } from '../../types/mrp';

export const MRPCalculationScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const { mrpCalculations, setMRPCalculations } = useMRPStore();
  const [selectedPeriod, setSelectedPeriod] = React.useState('2024-01');

  const calculateMutation = useMutation({
    mutationFn: (params: { period: string; horizon: number }) =>
      mrpAPI.calculate(params),
    onSuccess: (data) => {
      setMRPCalculations(data);
    },
  });

  const handleCalculate = () => {
    calculateMutation.mutate({ period: selectedPeriod, horizon: 12 });
  };

  const renderMRPItem = ({ item }: { item: MRPCalculation }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.cardHeader}>
          <View>
            <Text variant="titleMedium" style={styles.productName}>
              {item.productName}
            </Text>
            <Text variant="bodySmall" style={styles.sku}>
              SKU: {item.sku}
            </Text>
          </View>
          <Chip
            style={[
              styles.statusChip,
              {
                backgroundColor:
                  item.netRequirements > 0
                    ? theme.colors.errorContainer
                    : theme.colors.primaryContainer,
              },
            ]}
            textStyle={{
              color:
                item.netRequirements > 0
                  ? theme.colors.error
                  : theme.colors.primary,
            }}
          >
            {item.netRequirements > 0 ? 'Action Required' : 'OK'}
          </Chip>
        </View>

        <DataTable>
          <DataTable.Header>
            <DataTable.Title>Metric</DataTable.Title>
            <DataTable.Title numeric>Quantity</DataTable.Title>
          </DataTable.Header>

          <DataTable.Row>
            <DataTable.Cell>Current Stock</DataTable.Cell>
            <DataTable.Cell numeric>{item.currentStock}</DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>Reserved</DataTable.Cell>
            <DataTable.Cell numeric>{item.reservedStock}</DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>Available</DataTable.Cell>
            <DataTable.Cell numeric>{item.availableStock}</DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>Gross Requirements</DataTable.Cell>
            <DataTable.Cell numeric>{item.grossRequirements}</DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>Scheduled Receipts</DataTable.Cell>
            <DataTable.Cell numeric>{item.scheduledReceipts}</DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>
              <Text style={{ fontWeight: 'bold' }}>Net Requirements</Text>
            </DataTable.Cell>
            <DataTable.Cell numeric>
              <Text
                style={{
                  fontWeight: 'bold',
                  color:
                    item.netRequirements > 0 ? theme.colors.error : undefined,
                }}
              >
                {item.netRequirements}
              </Text>
            </DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>Planned Order Receipts</DataTable.Cell>
            <DataTable.Cell numeric>{item.plannedOrderReceipts}</DataTable.Cell>
          </DataTable.Row>
          <DataTable.Row>
            <DataTable.Cell>Planned Order Releases</DataTable.Cell>
            <DataTable.Cell numeric>{item.plannedOrderReleases}</DataTable.Cell>
          </DataTable.Row>
        </DataTable>

        <Divider style={styles.divider} />

        <View style={styles.footer}>
          <Text variant="bodySmall" style={styles.footerText}>
            Lead Time: {item.leadTime} days | Reorder Point: {item.reorderPoint}
          </Text>
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text variant="headlineMedium" style={styles.title}>
          MRP Calculation
        </Text>
        <Text variant="bodyMedium" style={styles.subtitle}>
          Material Requirements Planning
        </Text>
      </View>

      <View style={styles.actionBar}>
        <Button
          mode="contained"
          onPress={handleCalculate}
          loading={calculateMutation.isPending}
          icon="calculator"
          style={styles.calculateButton}
        >
          Run MRP Calculation
        </Button>
      </View>

      {calculateMutation.isError && (
        <Card style={[styles.errorCard, { backgroundColor: theme.colors.errorContainer }]}>
          <Card.Content>
            <Text style={{ color: theme.colors.error }}>
              Error running MRP calculation. Please try again.
            </Text>
          </Card.Content>
        </Card>
      )}

      <FlatList
        data={mrpCalculations}
        renderItem={renderMRPItem}
        keyExtractor={(item) => item.productId}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <View style={styles.emptyState}>
            <Text variant="bodyLarge" style={styles.emptyText}>
              Run MRP calculation to see material requirements
            </Text>
          </View>
        }
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
  subtitle: {
    opacity: 0.7,
    marginTop: 4,
  },
  actionBar: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  calculateButton: {
    width: '100%',
  },
  errorCard: {
    marginHorizontal: 16,
    marginBottom: 16,
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
    marginBottom: 12,
  },
  productName: {
    fontWeight: 'bold',
  },
  sku: {
    opacity: 0.6,
    marginTop: 2,
  },
  statusChip: {
    marginLeft: 8,
  },
  divider: {
    marginVertical: 12,
  },
  footer: {
    marginTop: 8,
  },
  footerText: {
    opacity: 0.6,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
  },
  emptyText: {
    opacity: 0.5,
    textAlign: 'center',
  },
});

