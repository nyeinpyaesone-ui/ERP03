import React, { useState, useCallback } from 'react';
import { View, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { Text, Card, Searchbar, Chip, useTheme } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const MOCK_RESULTS = [
  { id: '1', type: 'contact', title: 'John Smith', subtitle: 'john@acme.com', description: 'Lead Engineer at Acme Corp', tags: ['active', 'customer'] },
  { id: '2', type: 'company', title: 'Acme Corporation', subtitle: 'Technology', description: 'Enterprise software solutions', tags: ['enterprise', 'tech'] },
  { id: '3', type: 'invoice', title: 'INV-2024-156', subtitle: '124,500 MMK', description: 'Software licensing - Q2 2024', tags: ['paid', 'enterprise'] },
  { id: '4', type: 'project', title: 'Website Redesign', subtitle: 'In Progress', description: 'Complete overhaul of company website', tags: ['active', 'design'] },
  { id: '5', type: 'product', title: 'ERP Pro License', subtitle: '299,000 MMK/mo', description: 'Full-featured ERP with AI capabilities', tags: ['active', 'saas'] },
];

const ENTITY_COLORS: Record<string, { bg: string; text: string; icon: string }> = {
  contact: { bg: '#DBEAFE', text: '#3B82F6', icon: 'account' },
  company: { bg: '#D1FAE5', text: '#10B981', icon: 'office-building' },
  invoice: { bg: '#FEE2E2', text: '#EF4444', icon: 'file-document' },
  project: { bg: '#CFFAFE', text: '#06B6D4', icon: 'folder' },
  product: { bg: '#FEF3C7', text: '#F59E0B', icon: 'package' },
};

const FACETS = [
  { id: 'contact', label: 'Contacts', count: 1247 },
  { id: 'company', label: 'Companies', count: 342 },
  { id: 'product', label: 'Products', count: 89 },
  { id: 'invoice', label: 'Invoices', count: 156 },
  { id: 'project', label: 'Projects', count: 42 },
];

const RECENT_SEARCHES = ['John', 'Acme', 'invoice Q2', 'active projects'];

export default function SearchScreen() {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
  const [results, setResults] = useState(MOCK_RESULTS);
  const [isSearching, setIsSearching] = useState(false);

  const onChangeSearch = useCallback((query: string) => {
    setSearchQuery(query);
    if (query.length > 0) {
      setIsSearching(true);
      // Simulate search
      const filtered = MOCK_RESULTS.filter(r =>
        r.title.toLowerCase().includes(query.toLowerCase()) ||
        r.description.toLowerCase().includes(query.toLowerCase())
      );
      setResults(filtered);
      setIsSearching(false);
    } else {
      setResults([]);
    }
  }, []);

  const toggleType = (type: string) => {
    const next = new Set(selectedTypes);
    if (next.has(type)) next.delete(type);
    else next.add(type);
    setSelectedTypes(next);
  };

  const renderResult = ({ item }: { item: typeof MOCK_RESULTS[0] }) => {
    const colors = ENTITY_COLORS[item.type] || ENTITY_COLORS.contact;
    return (
      <TouchableOpacity>
        <Card style={styles.resultCard}>
          <Card.Content style={styles.resultContent}>
            <View style={[styles.resultIcon, { backgroundColor: colors.bg }]}>
              <Icon name={colors.icon} size={20} color={colors.text} />
            </View>
            <View style={styles.resultInfo}>
              <View style={styles.resultHeader}>
                <Text variant="titleMedium" style={{ fontWeight: '600' }}>{item.title}</Text>
                <View style={[styles.typeBadge, { backgroundColor: colors.bg }]}>
                  <Text variant="bodySmall" style={{ color: colors.text, fontWeight: '600', fontSize: 10 }}>
                    {item.type.toUpperCase()}
                  </Text>
                </View>
              </View>
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{item.subtitle}</Text>
              <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, marginTop: 2 }}>{item.description}</Text>
              <View style={styles.tagRow}>
                {item.tags.map((tag, i) => (
                  <Chip key={i} style={styles.tag} textStyle={{ fontSize: 10 }}>{tag}</Chip>
                ))}
              </View>
            </View>
          </Card.Content>
        </Card>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="headlineSmall" style={{ fontWeight: '700' }}>Search</Text>
      </View>

      <Searchbar
        placeholder="Search everything..."
        onChangeText={onChangeSearch}
        value={searchQuery}
        style={styles.searchBar}
        loading={isSearching}
        inputStyle={{ fontSize: 14 }}
      />

      {/* Facets */}
      <View style={styles.facetRow}>
        {FACETS.map(facet => (
          <TouchableOpacity
            key={facet.id}
            onPress={() => toggleType(facet.id)}
            style={[
              styles.facetChip,
              {
                backgroundColor: selectedTypes.has(facet.id) ? theme.colors.primaryContainer : theme.colors.surfaceVariant,
                borderColor: selectedTypes.has(facet.id) ? theme.colors.primary : theme.colors.outline,
              }
            ]}
          >
            <Text variant="bodySmall" style={{
              color: selectedTypes.has(facet.id) ? theme.colors.primary : theme.colors.onSurfaceVariant,
              fontWeight: selectedTypes.has(facet.id) ? '600' : '400'
            }}>
              {facet.label} ({facet.count})
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recent searches */}
      {searchQuery.length === 0 && (
        <View style={styles.recentSection}>
          <Text variant="titleSmall" style={{ fontWeight: '600', marginBottom: 8 }}>Recent Searches</Text>
          <View style={styles.recentRow}>
            {RECENT_SEARCHES.map((search, i) => (
              <TouchableOpacity
                key={i}
                onPress={() => onChangeSearch(search)}
                style={[styles.recentChip, { backgroundColor: theme.colors.surfaceVariant }]}
              >
                <Icon name="history" size={14} color={theme.colors.onSurfaceVariant} style={{ marginRight: 4 }} />
                <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{search}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {/* Results */}
      {searchQuery.length > 0 && (
        <FlatList
          data={results}
          renderItem={renderResult}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <Icon name="magnify-close" size={48} color={theme.colors.onSurfaceVariant} />
              <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant, marginTop: 8 }}>
                No results found
              </Text>
            </View>
          }
        />
      )}
    </View>
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
  searchBar: {
    margin: 16,
    marginTop: 0,
    borderRadius: 10,
    elevation: 2,
  },
  facetRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    gap: 8,
  },
  facetChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
  },
  recentSection: {
    padding: 16,
  },
  recentRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  recentChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
  },
  list: {
    padding: 16,
  },
  resultCard: {
    marginBottom: 8,
    elevation: 1,
  },
  resultContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
  },
  resultIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  resultInfo: {
    flex: 1,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 6,
  },
  tag: {
    height: 24,
  },
  emptyState: {
    alignItems: 'center',
    paddingTop: 48,
  },
});

