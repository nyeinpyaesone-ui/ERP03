import React from 'react';
import { View, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import { Card, Text, Searchbar, Chip, FAB, useTheme, IconButton } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';
import { bomAPI } from '../../services/api/mrpApi';
import { useMRPStore } from '../../store/mrpStore';
import { BillOfMaterials } from '../../types/mrp';

export const BOMListScreen: React.FC = () => {
  const { t } = useTranslation();
  const theme = useTheme();
  const navigation = useNavigation();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterActive, setFilterActive] = React.useState(true);
  const { setSelectedBOM } = useMRPStore();

  const { data: boms, isLoading } = useQuery<BillOfMaterials[]>({
    queryKey: ['boms', filterActive],
    queryFn: () => bomAPI.getAll(),
  });

  const filteredBOMs = React.useMemo(() => {
    if (!boms) return [];
    return boms.filter((bom) => {
      const matchesSearch =
        !searchQuery ||
        bom.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        bom.finishedGoodName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        bom.finishedGoodSku.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesFilter = !filterActive || bom.isActive;
      return matchesSearch && matchesFilter;
    });
  }, [boms, searchQuery, filterActive]);

  const renderBOMItem = ({ item }: { item: BillOfMaterials }) => (
    <TouchableOpacity
      onPress={() => {
        setSelectedBOM(item);
        navigation.navigate('BOMDetail' as never);
      }}
    >
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.cardHeader}>
            <View style={styles.cardTitleSection}>
              <Text variant="titleMedium" style={styles.cardTitle}>
                {item.name}
              </Text>
              <Text variant="bodySmall" style={styles.sku}>
                SKU: {item.finishedGoodSku}
              </Text>
            </View>
            <Chip
              compact
              style={[
                styles.statusChip,
                {
                  backgroundColor: item.isActive
                    ? theme.colors.primaryContainer
                    : theme.colors.surfaceVariant,
                },
              ]}
            >
              {item.isActive ? 'Active' : 'Inactive'}
            </Chip>
          </View>

          <Text variant="bodyMedium" style={styles.productName}>
            {item.finishedGoodName}
          </Text>

          <View style={styles.cardFooter}>
            <View style={styles.footerItem}>
              <Text variant="bodySmall" style={styles.footerLabel}>
                Items
              </Text>
              <Text variant="titleSmall" style={styles.footerValue}>
                {item.items.length}
              </Text>
            </View>
            <View style={styles.footerItem}>
              <Text variant="bodySmall" style={styles.footerLabel}>
                Total Cost
              </Text>
              <Text variant="titleSmall" style={styles.footerValue}>
                {item.totalCost.toLocaleString()} MMK
              </Text>
            </View>
            <View style={styles.footerItem}>
              <Text variant="bodySmall" style={styles.footerLabel}>
                Version
              </Text>
              <Text variant="titleSmall" style={styles.footerValue}>
                v{item.version}
              </Text>
            </View>
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="Search BOMs by name or SKU..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        style={styles.searchbar}
      />

      <View style={styles.filterRow}>
        <Chip
          selected={filterActive}
          onPress={() => setFilterActive(!filterActive)}
          style={styles.filterChip}
        >
          Active Only
        </Chip>
      </View>

      <FlatList
        data={filteredBOMs}
        renderItem={renderBOMItem}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
      />

      <FAB
        icon="plus"
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        onPress={() => navigation.navigate('BOMCreate' as never)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  searchbar: {
    margin: 16,
    marginBottom: 8,
  },
  filterRow: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  filterChip: {
    alignSelf: 'flex-start',
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
    marginBottom: 4,
  },
  cardTitleSection: {
    flex: 1,
  },
  cardTitle: {
    fontWeight: 'bold',
  },
  sku: {
    opacity: 0.6,
    marginTop: 2,
  },
  statusChip: {
    marginLeft: 8,
  },
  productName: {
    marginBottom: 12,
    opacity: 0.8,
  },
  cardFooter: {
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
  footerValue: {
    fontWeight: '600',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});

