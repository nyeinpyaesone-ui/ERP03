import React from 'react';
import { View, ScrollView, StyleSheet } from 'react-native';
import { Text, Card, ProgressBar, useTheme, Badge } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const MOCK_INVENTORY = [
  { product: 'ERP Pro License', sku: 'ERP-PRO', warehouse: 'Yangon Main', onHand: 150, reserved: 45, available: 105, reorder: 50, status: 'ok' },
  { product: 'ERP Basic License', sku: 'ERP-BAS', warehouse: 'Yangon Main', onHand: 320, reserved: 120, available: 200, reorder: 100, status: 'ok' },
  { product: 'Hardware Server', sku: 'SRV-001', warehouse: 'Mandalay Hub', onHand: 12, reserved: 8, available: 4, reorder: 10, status: 'reorder' },
  { product: 'Network Switch', sku: 'NET-48P', warehouse: 'Yangon Main', onHand: 28, reserved: 20, available: 8, reorder: 15, status: 'low' },
];

export default function InventoryScreen() {
  const theme = useTheme();

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="headlineSmall" style={{ fontWeight: '700' }}>Inventory</Text>
      </View>

      {MOCK_INVENTORY.map((item, i) => (
        <Card key={i} style={styles.card}>
          <Card.Content>
            <View style={styles.row}>
              <View style={styles.productInfo}>
                <Text variant="titleMedium" style={{ fontWeight: '600' }}>{item.product}</Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
                  {item.sku} • {item.warehouse}
                </Text>
              </View>
              <Badge
                style={{
                  backgroundColor: item.status === 'ok' ? '#D1FAE5' : item.status === 'low' ? '#FEF3C7' : '#FEE2E2',
                }}
              >
                <Text style={{
                  color: item.status === 'ok' ? '#10B981' : item.status === 'low' ? '#F59E0B' : '#EF4444',
                  fontSize: 11,
                  fontWeight: '600',
                }}>
                  {item.status.toUpperCase()}
                </Text>
              </Badge>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.stat}>
                <Text variant="titleMedium" style={{ fontWeight: '700' }}>{item.onHand}</Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>On Hand</Text>
              </View>
              <View style={styles.stat}>
                <Text variant="titleMedium" style={{ fontWeight: '700', color: theme.colors.onSurfaceVariant }}>{item.reserved}</Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>Reserved</Text>
              </View>
              <View style={styles.stat}>
                <Text variant="titleMedium" style={{ fontWeight: '700', color: item.available <= item.reorder ? theme.colors.error : theme.colors.primary }}>
                  {item.available}
                </Text>
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>Available</Text>
              </View>
            </View>

            <ProgressBar
              progress={item.available / (item.reorder * 2)}
              color={item.available <= item.reorder ? theme.colors.error : item.available <= item.reorder * 1.5 ? theme.colors.warning : theme.colors.success}
              style={styles.progress}
            />
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>
              Reorder point: {item.reorder}
            </Text>
          </Card.Content>
        </Card>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    paddingTop: 24,
  },
  card: {
    margin: 16,
    marginTop: 0,
    marginBottom: 8,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  productInfo: {
    flex: 1,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  stat: {
    alignItems: 'center',
  },
  progress: {
    height: 6,
    borderRadius: 3,
    marginBottom: 4,
  },
});

