import React, { useState } from 'react';
import { View, FlatList, StyleSheet, TouchableOpacity } from 'react-native';
import { Text, Card, Avatar, Searchbar, useTheme, FAB } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const MOCK_CONTACTS = [
  { id: '1', name: 'John Smith', email: 'john@acme.com', company: 'Acme Corp', phone: '+95 9 123 456 789', status: 'active', initials: 'JS' },
  { id: '2', name: 'Sarah Chen', email: 'sarah@techlabs.io', company: 'TechLabs', phone: '+95 9 234 567 890', status: 'active', initials: 'SC' },
  { id: '3', name: 'Mike Ross', email: 'mike@startup.io', company: 'Startup.io', phone: '+95 9 345 678 901', status: 'lead', initials: 'MR' },
  { id: '4', name: 'Emma Wilson', email: 'emma@design.co', company: 'Design Co', phone: '+95 9 456 789 012', status: 'customer', initials: 'EW' },
  { id: '5', name: 'James Lee', email: 'james@logistics.mm', company: 'MM Logistics', phone: '+95 9 567 890 123', status: 'active', initials: 'JL' },
];

export default function ContactsScreen() {
  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredContacts, setFilteredContacts] = useState(MOCK_CONTACTS);

  const onChangeSearch = (query: string) => {
    setSearchQuery(query);
    const filtered = MOCK_CONTACTS.filter(c =>
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.company.toLowerCase().includes(query.toLowerCase()) ||
      c.email.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredContacts(filtered);
  };

  const renderContact = ({ item }: { item: typeof MOCK_CONTACTS[0] }) => (
    <TouchableOpacity>
      <Card style={styles.contactCard}>
        <Card.Content style={styles.contactContent}>
          <Avatar.Text
            size={48}
            label={item.initials}
            style={{ backgroundColor: theme.colors.primaryContainer }}
            labelStyle={{ color: theme.colors.primary, fontWeight: '600' }}
          />
          <View style={styles.contactInfo}>
            <Text variant="titleMedium" style={{ fontWeight: '600' }}>{item.name}</Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{item.company}</Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{item.email}</Text>
          </View>
          <View style={styles.contactActions}>
            <View style={[styles.statusBadge, { backgroundColor: item.status === 'active' ? '#D1FAE5' : item.status === 'lead' ? '#FEF3C7' : '#DBEAFE' }]}>
              <Text variant="bodySmall" style={{ color: item.status === 'active' ? '#10B981' : item.status === 'lead' ? '#F59E0B' : '#3B82F6', fontWeight: '600', fontSize: 11 }}>
                {item.status.toUpperCase()}
              </Text>
            </View>
            <TouchableOpacity style={styles.actionButton}>
              <Icon name="phone" size={20} color={theme.colors.primary} />
            </TouchableOpacity>
          </View>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <Text variant="headlineSmall" style={{ fontWeight: '700' }}>Contacts</Text>
      </View>

      <Searchbar
        placeholder="Search contacts, companies..."
        onChangeText={onChangeSearch}
        value={searchQuery}
        style={styles.searchBar}
        inputStyle={{ fontSize: 14 }}
      />

      <FlatList
        data={filteredContacts}
        renderItem={renderContact}
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
    padding: 16,
    paddingTop: 24,
  },
  searchBar: {
    margin: 16,
    marginTop: 0,
    borderRadius: 10,
    elevation: 2,
  },
  list: {
    padding: 16,
    paddingTop: 0,
  },
  contactCard: {
    marginBottom: 8,
    elevation: 1,
  },
  contactContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
  },
  contactInfo: {
    flex: 1,
    marginLeft: 12,
  },
  contactActions: {
    alignItems: 'flex-end',
    gap: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 12,
  },
  actionButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
  },
});

