import React, { useState } from 'react';
import { View, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { Text, Card, Avatar, Chip, useTheme, SegmentedButtons, FAB } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const MOCK_INVOICES = [
  { id: '1', number: 'INV-2024-156', customer: 'Acme Corp', amount: 124500, status: 'paid', date: '2024-06-10', days: 5 },
  { id: '2', number: 'INV-2024-155', customer: 'TechLabs', amount: 85000, status: 'pending', date: '2024-06-08', days: 7 },
  { id: '3', number: 'INV-2024-154', customer: 'Startup.io', amount: 45000, status: 'overdue', date: '2024-05-20', days: 26 },
  { id: '4', number: 'INV-2024-153', customer: 'Design Co', amount: 230000, status: 'paid', date: '2024-06-05', days: 10 },
  { id: '5', number: 'INV-2024-152', customer: 'MM Logistics', amount: 67000, status: 'pending', date: '2024-06-12', days: 3 },
];

export default function InvoicesScreen() {
  const theme = useTheme();
  const [filter, setFilter] = useState('all');

  const filteredInvoices = filter === 'all'
    ? MOCK_INVOICES
    : MOCK_INVOICES.filter(i => i.status === filter);

  const totalAmount = filteredInvoices.reduce((sum, i) => sum + i.amount, 0);

  const renderInvoice = ({ item }: { item: typeof MOCK_INVOICES[0] }) => (
    <TouchableOpacity>
      <Card style={styles.invoiceCard}>
        <Card.Content>
          <View style={styles.invoiceHeader}>
            <View>
              <Text variant="titleMedium" style={{ fontWeight: '600' }}>{item.number}</Text>
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{item.customer}</Text>
            </View>
            <View style={[styles.statusChip, {
              backgroundColor: item.status === 'paid' ? '#D1FAE5' : item.status === 'pending' ? '#FEF3C7' : '#FEE2E2'
            }]}>
              <Text variant="bodySmall" style={{
                color: item.status === 'paid' ? '#10B981' : item.status === 'pending' ? '#F59E0B' : '#EF4444',
                fontWeight: '600',
                fontSize: 11
              }}>
                {item.status.toUpperCase()}
              </Text>
            </View>
          </View>

          <View style={styles.invoiceFooter}>
            <Text variant="titleLarge" style={{ fontWeight: '700', color: theme.colors.primary }}>
              {item.amount.toLocaleString()} MMK
            </Text>
            <View style={styles.invoiceMeta}>
              <Icon name="calendar" size={14} color={theme.colors.onSurfaceVariant} />
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginLeft: 4 }}>
                {item.date}
              </Text>
              {item.status === 'overdue' && (
                <Text variant="bodySmall" style={{ color: '#EF4444', marginLeft: 8, fontWeight: '600' }}>
                  {item.days} days overdue
                </Text>
              )}
            </View>
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="headlineSmall" style={{ fontWeight: '700' }}>Invoices</Text>
        <Text variant="titleMedium" style={{ color: theme.colors.primary, fontWeight: '600' }}>
          {totalAmount.toLocaleString()} MMK
        </Text>
      </View>

      <SegmentedButtons
        value={filter}
        onValueChange={setFilter}
        buttons={[
          { value: 'all', label: 'All' },
          { value: 'paid', label: 'Paid' },
          { value: 'pending', label: 'Pending' },
          { value: 'overdue', label: 'Overdue' },
        ]}
        style={styles.segmented}
      />

      <FlatList
        data={filteredInvoices}
        renderItem={renderInvoice}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        onPress={() => {}}
        color="#fff"
      />
    </View>
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
  segmented: {
    margin: 16,
    marginTop: 0,
  },
  list: {
    padding: 16,
    paddingTop: 0,
  },
  invoiceCard: {
    marginBottom: 8,
    elevation: 1,
  },
  invoiceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  statusChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  invoiceFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  invoiceMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});

