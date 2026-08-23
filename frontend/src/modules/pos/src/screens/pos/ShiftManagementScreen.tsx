import React from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Card, Text, Button, TextInput, Chip, FAB, useTheme, Divider, DataTable, IconButton } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { posShiftAPI, posRegisterAPI } from '../../services/api/posApi';
import { usePOSStore } from '../../store/posStore';
import { POSShift, POSRegister, ShiftStatus } from '../../types/pos';

const STATUS_CONFIG: Record<ShiftStatus, { label: string; color: string; icon: string }> = {
  open: { label: 'Open', color: '#4caf50', icon: 'store' },
  closed: { label: 'Closed', color: '#f44336', icon: 'store-off' },
  counted: { label: 'Counted', color: '#2196f3', icon: 'calculator' },
};

export const ShiftManagementScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const { currentShift, setCurrentShift, currentRegister, setCurrentRegister } = usePOSStore();

  const [selectedRegister, setSelectedRegister] = React.useState<string | null>(null);
  const [openingAmount, setOpeningAmount] = React.useState('');
  const [closingAmount, setClosingAmount] = React.useState('');
  const [notes, setNotes] = React.useState('');
  const [showCloseForm, setShowCloseForm] = React.useState(false);

  const { data: registers } = useQuery<POSRegister[]>({
    queryKey: ['posRegisters'],
    queryFn: () => posRegisterAPI.getAll(),
  });

  const { data: shiftHistory } = useQuery<POSShift[]>({
    queryKey: ['shiftHistory'],
    queryFn: () => posShiftAPI.getHistory(),
  });

  const openMutation = useMutation({
    mutationFn: () =>
      posShiftAPI.open({
        registerId: selectedRegister!,
        cashierId: 'current-user',
        openingAmount: parseFloat(openingAmount) || 0,
        notes: notes || undefined,
      }),
    onSuccess: (shift) => {
      setCurrentShift(shift);
      const register = registers?.find((r) => r.id === selectedRegister);
      if (register) setCurrentRegister(register);
      setOpeningAmount('');
      setNotes('');
      setSelectedRegister(null);
    },
  });

  const closeMutation = useMutation({
    mutationFn: () =>
      posShiftAPI.close(currentShift!.id, {
        closingAmount: parseFloat(closingAmount) || 0,
        countedAmount: parseFloat(closingAmount) || 0,
        notes: notes || undefined,
      }),
    onSuccess: (shift) => {
      setCurrentShift(null);
      setClosingAmount('');
      setNotes('');
      setShowCloseForm(false);
    },
  });

  const renderShift = ({ item }: { item: POSShift }) => {
    const status = STATUS_CONFIG[item.status];
    const isCurrent = currentShift?.id === item.id;

    return (
      <Card style={[styles.shiftCard, isCurrent && styles.currentShiftCard]}>
        <Card.Content>
          <View style={styles.shiftHeader}>
            <View style={styles.shiftInfo}>
              <Text variant="titleMedium" style={styles.shiftNumber}>
                Shift #{item.shiftNumber}
              </Text>
              <Text variant="bodySmall" style={styles.shiftMeta}>
                {item.registerName} • {item.cashierName}
              </Text>
            </View>
            <Chip
              style={[styles.statusChip, { backgroundColor: status.color + '20' }]}
              textStyle={{ color: status.color }}
              icon={status.icon}
            >
              {status.label}
            </Chip>
          </View>

          <DataTable>
            <DataTable.Row>
              <DataTable.Cell>Opened</DataTable.Cell>
              <DataTable.Cell numeric>
                {new Date(item.openedAt).toLocaleString()}
              </DataTable.Cell>
            </DataTable.Row>
            {item.closedAt && (
              <DataTable.Row>
                <DataTable.Cell>Closed</DataTable.Cell>
                <DataTable.Cell numeric>
                  {new Date(item.closedAt).toLocaleString()}
                </DataTable.Cell>
              </DataTable.Row>
            )}
            <DataTable.Row>
              <DataTable.Cell>Opening Amount</DataTable.Cell>
              <DataTable.Cell numeric>
                {item.openingAmount.toLocaleString()} MMK
              </DataTable.Cell>
            </DataTable.Row>
            {item.closingAmount !== undefined && (
              <DataTable.Row>
                <DataTable.Cell>Closing Amount</DataTable.Cell>
                <DataTable.Cell numeric>
                  {item.closingAmount.toLocaleString()} MMK
                </DataTable.Cell>
              </DataTable.Row>
            )}
            {item.difference !== undefined && (
              <DataTable.Row>
                <DataTable.Cell>Difference</DataTable.Cell>
                <DataTable.Cell numeric>
                  <Text style={{ color: item.difference !== 0 ? theme.colors.error : theme.colors.primary }}>
                    {item.difference.toLocaleString()} MMK
                  </Text>
                </DataTable.Cell>
              </DataTable.Row>
            )}
            <DataTable.Row>
              <DataTable.Cell>Sales</DataTable.Cell>
              <DataTable.Cell numeric>
                {item.salesCount} transactions • {item.totalSales.toLocaleString()} MMK
              </DataTable.Cell>
            </DataTable.Row>
            {item.refundsCount > 0 && (
              <DataTable.Row>
                <DataTable.Cell>Refunds</DataTable.Cell>
                <DataTable.Cell numeric style={{ color: theme.colors.error }}>
                  {item.refundsCount} • {item.totalRefunds.toLocaleString()} MMK
                </DataTable.Cell>
              </DataTable.Row>
            )}
          </DataTable>

          {isCurrent && item.status === 'open' && (
            <Button
              mode="contained"
              onPress={() => setShowCloseForm(true)}
              style={styles.closeButton}
              icon="store-off"
              buttonColor={theme.colors.error}
            >
              Close Shift
            </Button>
          )}
        </Card.Content>
      </Card>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text variant="headlineMedium" style={styles.title}>
          Shift Management
        </Text>
      </View>

      {currentShift ? (
        <View style={styles.currentShiftBanner}>
          <MaterialCommunityIcons name="store" size={24} color="#4caf50" />
          <View style={styles.bannerInfo}>
            <Text variant="titleMedium" style={{ fontWeight: 'bold' }}>
              Active Shift #{currentShift.shiftNumber}
            </Text>
            <Text variant="bodySmall">
              {currentShift.registerName} • Started {new Date(currentShift.openedAt).toLocaleTimeString()}
            </Text>
          </View>
          <Button
            mode="contained"
            onPress={() => navigation.navigate('POS' as never)}
            compact
          >
            Go to POS
          </Button>
        </View>
      ) : (
        <Card style={styles.openShiftCard}>
          <Card.Title title="Open New Shift" />
          <Card.Content>
            <Text variant="bodyMedium" style={{ marginBottom: 12 }}>
              Select a register and enter opening cash amount
            </Text>

            <View style={styles.registersRow}>
              {registers?.map((register) => (
                <Chip
                  key={register.id}
                  selected={selectedRegister === register.id}
                  onPress={() => setSelectedRegister(register.id)}
                  style={styles.registerChip}
                  icon={register.isActive ? 'store' : 'store-off'}
                  disabled={!register.isActive}
                  showSelectedCheck={false}
                >
                  {register.name}
                </Chip>
              ))}
            </View>

            <TextInput
              mode="outlined"
              label="Opening Cash Amount"
              value={openingAmount}
              onChangeText={setOpeningAmount}
              keyboardType="numeric"
              style={styles.input}
              left={<TextInput.Affix text="MMK" />}
            />

            <TextInput
              mode="outlined"
              label="Notes (optional)"
              value={notes}
              onChangeText={setNotes}
              multiline
              numberOfLines={2}
              style={styles.input}
            />

            <Button
              mode="contained"
              onPress={() => openMutation.mutate()}
              loading={openMutation.isPending}
              disabled={!selectedRegister || !openingAmount}
              style={styles.openButton}
              icon="store"
            >
              Open Shift
            </Button>
          </Card.Content>
        </Card>
      )}

      {showCloseForm && currentShift && (
        <Card style={styles.closeShiftCard}>
          <Card.Title title="Close Shift" />
          <Card.Content>
            <TextInput
              mode="outlined"
              label="Closing Cash Amount"
              value={closingAmount}
              onChangeText={setClosingAmount}
              keyboardType="numeric"
              style={styles.input}
              left={<TextInput.Affix text="MMK" />}
            />
            <TextInput
              mode="outlined"
              label="Notes"
              value={notes}
              onChangeText={setNotes}
              style={styles.input}
            />
            <View style={styles.closeActions}>
              <Button
                mode="outlined"
                onPress={() => setShowCloseForm(false)}
                style={styles.cancelButton}
              >
                Cancel
              </Button>
              <Button
                mode="contained"
                onPress={() => closeMutation.mutate()}
                loading={closeMutation.isPending}
                disabled={!closingAmount}
                style={styles.confirmButton}
                buttonColor={theme.colors.error}
              >
                Close Shift
              </Button>
            </View>
          </Card.Content>
        </Card>
      )}

      <Text variant="titleMedium" style={styles.historyTitle}>
        Shift History
      </Text>

      <FlatList
        data={shiftHistory}
        renderItem={renderShift}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
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
  currentShiftBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f5e9',
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 8,
  },
  bannerInfo: {
    flex: 1,
    marginLeft: 12,
  },
  openShiftCard: {
    margin: 16,
    marginTop: 0,
  },
  registersRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  registerChip: {
    marginBottom: 8,
  },
  input: {
    marginBottom: 12,
  },
  openButton: {
    marginTop: 8,
  },
  closeShiftCard: {
    margin: 16,
    marginTop: 0,
  },
  closeActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
  },
  confirmButton: {
    flex: 1,
  },
  historyTitle: {
    marginHorizontal: 16,
    marginBottom: 8,
    fontWeight: 'bold',
  },
  listContent: {
    padding: 16,
    paddingTop: 0,
  },
  shiftCard: {
    marginBottom: 12,
  },
  currentShiftCard: {
    borderLeftWidth: 4,
    borderLeftColor: '#4caf50',
  },
  shiftHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  shiftInfo: {
    flex: 1,
  },
  shiftNumber: {
    fontWeight: 'bold',
  },
  shiftMeta: {
    opacity: 0.6,
    marginTop: 2,
  },
  statusChip: {
    marginLeft: 8,
  },
  closeButton: {
    marginTop: 12,
  },
});

