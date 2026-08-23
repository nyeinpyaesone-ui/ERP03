import React from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { Text, useTheme, Button } from 'react-native-paper';
import { useTranslation } from 'react-i18next';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// Loading State
export const LoadingState: React.FC<{ message?: string }> = ({ message }) => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <View style={styles.centerContainer}>
      <ActivityIndicator size="large" color={theme.colors.primary} />
      <Text variant="bodyMedium" style={styles.loadingText}>
        {message || t('common.loading')}
      </Text>
    </View>
  );
};

// Error State
export const ErrorState: React.FC<{
  message?: string;
  onRetry?: () => void;
}> = ({ message, onRetry }) => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <View style={styles.centerContainer}>
      <MaterialCommunityIcons name="alert-circle" size={64} color={theme.colors.error} />
      <Text variant="titleMedium" style={[styles.errorText, { color: theme.colors.error }]}>
        {message || t('common.error')}
      </Text>
      {onRetry && (
        <Button mode="contained" onPress={onRetry} style={styles.retryButton}>
          {t('common.retry')}
        </Button>
      )}
    </View>
  );
};

// Empty State
export const EmptyState: React.FC<{
  icon?: string;
  title?: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
}> = ({ icon = 'inbox', title, message, actionLabel, onAction }) => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <View style={styles.centerContainer}>
      <MaterialCommunityIcons name={icon as any} size={64} color={theme.colors.outline} />
      <Text variant="titleMedium" style={styles.emptyTitle}>
        {title || t('common.noResults')}
      </Text>
      {message && (
        <Text variant="bodyMedium" style={styles.emptyMessage}>
          {message}
        </Text>
      )}
      {onAction && actionLabel && (
        <Button mode="contained" onPress={onAction} style={styles.actionButton}>
          {actionLabel}
        </Button>
      )}
    </View>
  );
};

// Offline Banner
export const OfflineBanner: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();

  return (
    <View style={[styles.offlineBanner, { backgroundColor: theme.colors.errorContainer }]}>
      <MaterialCommunityIcons name="wifi-off" size={20} color={theme.colors.error} />
      <Text variant="bodyMedium" style={[styles.offlineText, { color: theme.colors.error }]}>
        {t('common.offline')}
      </Text>
    </View>
  );
};

// Status Badge
export const StatusBadge: React.FC<{
  status: string;
  size?: 'small' | 'medium';
}> = ({ status, size = 'small' }) => {
  const theme = useTheme();
  const color = getStatusColor(status);

  return (
    <View style={[styles.badge, { backgroundColor: color + '20' }, size === 'medium' && styles.badgeMedium]}>
      <View style={[styles.badgeDot, { backgroundColor: color }]} />
      <Text variant={size === 'small' ? 'bodySmall' : 'bodyMedium'} style={[styles.badgeText, { color }]}>
        {status.replace(/_/g, ' ').replace(/\w/g, (l) => l.toUpperCase())}
      </Text>
    </View>
  );
};

// Amount Display
export const AmountDisplay: React.FC<{
  amount: number;
  currency?: string;
  type?: 'positive' | 'negative' | 'neutral';
  size?: 'small' | 'medium' | 'large';
}> = ({ amount, currency = 'MMK', type = 'neutral', size = 'medium' }) => {
  const theme = useTheme();
  const { formatCurrency } = useLanguage();

  const colorMap = {
    positive: theme.colors.primary,
    negative: theme.colors.error,
    neutral: theme.colors.onSurface,
  };

  const sizeMap = {
    small: 'bodyMedium',
    medium: 'titleMedium',
    large: 'headlineSmall',
  };

  return (
    <Text variant={sizeMap[size]} style={{ color: colorMap[type], fontWeight: 'bold' }}>
      {type === 'negative' ? '-' : type === 'positive' ? '+' : ''}
      {formatCurrency(Math.abs(amount), currency)}
    </Text>
  );
};

// Avatar with initials
export const AvatarInitials: React.FC<{
  name: string;
  size?: number;
  color?: string;
}> = ({ name, size = 40, color }) => {
  const theme = useTheme();
  const bgColor = color || theme.colors.primary;
  const text = initials(name);

  return (
    <View style={[styles.avatar, { width: size, height: size, borderRadius: size / 2, backgroundColor: bgColor }]}>
      <Text variant="titleMedium" style={[styles.avatarText, { fontSize: size * 0.4, color: '#fff' }]}>
        {text}
      </Text>
    </View>
  );
};

// Card with shadow
export const ShadowCard: React.FC<{
  children: React.ReactNode;
  style?: any;
}> = ({ children, style }) => {
  return (
    <View style={[styles.shadowCard, style]}>
      {children}
    </View>
  );
};

import { getStatusColor, initials } from '../utils/helpers';
import { useLanguage } from '../hooks/useLanguage';

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    opacity: 0.7,
  },
  errorText: {
    marginTop: 16,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
  },
  emptyTitle: {
    marginTop: 16,
    fontWeight: 'bold',
    opacity: 0.7,
  },
  emptyMessage: {
    marginTop: 8,
    textAlign: 'center',
    opacity: 0.5,
  },
  actionButton: {
    marginTop: 16,
  },
  offlineBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 8,
    gap: 8,
  },
  offlineText: {
    fontWeight: '500',
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  badgeMedium: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  badgeText: {
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  avatar: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontWeight: 'bold',
  },
  shadowCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
});

