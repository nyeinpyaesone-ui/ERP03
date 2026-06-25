import React from 'react';
import { View, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { Text, Avatar, List, Switch, useTheme, Divider, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useAuthStore } from '../store/authStore';
import { useThemeStore } from '../store/themeStore';

const MENU_ITEMS = [
  { icon: 'account-cog', title: 'Account Settings', subtitle: 'Profile, password, notifications' },
  { icon: 'theme-light-dark', title: 'Appearance', subtitle: 'Dark mode, font size' },
  { icon: 'bell-outline', title: 'Notifications', subtitle: 'Push, email, in-app' },
  { icon: 'shield-check', title: 'Security', subtitle: 'Biometric, 2FA, sessions' },
  { icon: 'database', title: 'Offline Data', subtitle: 'Sync settings, storage' },
  { icon: 'help-circle-outline', title: 'Help & Support', subtitle: 'FAQ, contact, feedback' },
  { icon: 'information-outline', title: 'About', subtitle: 'Version, licenses, privacy' },
];

export default function ProfileScreen() {
  const theme = useTheme();
  const { user, logout } = useAuthStore();
  const { isDarkMode, toggleTheme } = useThemeStore();

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Profile Header */}
      <View style={[styles.header, { backgroundColor: theme.colors.surface }]}>
        <Avatar.Text
          size={72}
          label={user?.name?.split(' ').map(n => n[0]).join('') || 'U'}
          style={{ backgroundColor: theme.colors.primary }}
          labelStyle={{ color: '#fff', fontSize: 28, fontWeight: '700' }}
        />
        <Text variant="headlineSmall" style={{ fontWeight: '700', marginTop: 12 }}>
          {user?.name || 'Alex Johnson'}
        </Text>
        <Text variant="bodyMedium" style={{ color: theme.colors.onSurfaceVariant }}>
          {user?.email || 'alex@company.com'}
        </Text>
        <View style={styles.roleBadge}>
          <Text variant="bodySmall" style={{ color: theme.colors.primary, fontWeight: '600' }}>
            {user?.role || 'Admin'}
          </Text>
        </View>
      </View>

      <Divider />

      {/* Quick Stats */}
      <View style={styles.statsRow}>
        {[
          { label: 'Contacts', value: '2.8K', icon: 'account-group' },
          { label: 'Invoices', value: '156', icon: 'file-document' },
          { label: 'Deals', value: '28', icon: 'handshake' },
        ].map((stat, i) => (
          <View key={i} style={[styles.statCard, { backgroundColor: theme.colors.surface }]}>
            <Icon name={stat.icon} size={24} color={theme.colors.primary} />
            <Text variant="titleLarge" style={{ fontWeight: '700', marginTop: 4 }}>{stat.value}</Text>
            <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant }}>{stat.label}</Text>
          </View>
        ))}
      </View>

      <Divider />

      {/* Settings */}
      <View style={styles.settingsSection}>
        <List.Item
          title="Dark Mode"
          description="Toggle between light and dark theme"
          left={props => <List.Icon {...props} icon="theme-light-dark" />}
          right={() => (
            <Switch
              value={isDarkMode}
              onValueChange={toggleTheme}
              color={theme.colors.primary}
            />
          )}
        />
        <Divider />

        {MENU_ITEMS.map((item, i) => (
          <React.Fragment key={i}>
            <List.Item
              title={item.title}
              description={item.subtitle}
              left={props => <List.Icon {...props} icon={item.icon} />}
              right={props => <List.Icon {...props} icon="chevron-right" />}
              onPress={() => {}}
            />
            <Divider />
          </React.Fragment>
        ))}
      </View>

      {/* Logout */}
      <View style={styles.logoutSection}>
        <Button
          mode="outlined"
          onPress={logout}
          style={{ borderColor: theme.colors.error }}
          labelStyle={{ color: theme.colors.error }}
          icon="logout"
        >
          Sign Out
        </Button>
      </View>

      <View style={styles.versionSection}>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}>
          ERP SOLUTION Mobile v2.5.0
        </Text>
        <Text variant="bodySmall" style={{ color: theme.colors.onSurfaceVariant, textAlign: 'center' }}>
          Built with React Native + Expo
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    alignItems: 'center',
    padding: 24,
    paddingTop: 32,
  },
  roleBadge: {
    marginTop: 8,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: '#DBEAFE',
  },
  statsRow: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    elevation: 1,
  },
  settingsSection: {
    paddingVertical: 8,
  },
  logoutSection: {
    padding: 16,
    marginTop: 8,
  },
  versionSection: {
    padding: 24,
    alignItems: 'center',
  },
});

