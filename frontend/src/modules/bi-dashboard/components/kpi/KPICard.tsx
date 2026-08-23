import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Text, ProgressBar } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { KPIMetric } from '../types/dashboard';
import { formatCurrency, formatNumber, formatPercentage, getTrendColor, getTrendIcon } from '../utils/dashboard';
import { CHART_COLORS } from '../constants/dashboard';

interface KPICardProps {
  title: string;
  metric: KPIMetric;
  type: 'currency' | 'number' | 'percentage' | 'days';
  icon?: string;
  color?: string;
  onPress?: () => void;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  metric,
  type,
  icon,
  color = CHART_COLORS.primary,
  onPress,
}) => {
  const formatValue = (value: number): string => {
    switch (type) {
      case 'currency':
        return formatCurrency(value);
      case 'percentage':
        return `${value.toFixed(1)}%`;
      case 'days':
        return `${value.toFixed(0)}d`;
      default:
        return formatNumber(value);
    }
  };

  const achievementPercent = Math.min(metric.achievement * 100, 100);
  const isOnTrack = metric.achievement >= 0.9;

  return (
    <Card style={styles.card} onPress={onPress}>
      <Card.Content>
        <View style={styles.header}>
          <View style={[styles.iconContainer, { backgroundColor: `${color}15` }]}>
            <MaterialCommunityIcons
              name={icon as any || 'chart-line'}
              size={24}
              color={color}
            />
          </View>
          <View style={styles.trendContainer}>
            <MaterialCommunityIcons
              name={getTrendIcon(metric.achievement - 1) as any}
              size={16}
              color={getTrendColor(metric.achievement - 1)}
            />
            <Text
              variant="bodySmall"
              style={{ color: getTrendColor(metric.achievement - 1) }}
            >
              {formatPercentage((metric.achievement - 1) * 100)}
            </Text>
          </View>
        </View>

        <Text variant="titleLarge" style={styles.value}>
          {formatValue(metric.value)}
        </Text>
        <Text variant="bodySmall" style={styles.label}>
          {title}
        </Text>

        <View style={styles.progressContainer}>
          <ProgressBar
            progress={achievementPercent / 100}
            color={isOnTrack ? CHART_COLORS.success : CHART_COLORS.warning}
            style={styles.progressBar}
          />
          <View style={styles.targetRow}>
            <Text variant="bodySmall" style={styles.targetText}>
              Target: {formatValue(metric.target)}
            </Text>
            <Text
              variant="bodySmall"
              style={[
                styles.achievementText,
                { color: isOnTrack ? CHART_COLORS.success : CHART_COLORS.warning },
              ]}
            >
              {achievementPercent.toFixed(0)}%
            </Text>
          </View>
        </View>
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    margin: 4,
    flex: 1,
    minWidth: 280,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  value: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  label: {
    color: '#666',
    marginBottom: 12,
  },
  progressContainer: {
    marginTop: 8,
  },
  progressBar: {
    height: 6,
    borderRadius: 3,
  },
  targetRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  targetText: {
    color: '#888',
  },
  achievementText: {
    fontWeight: 'bold',
  },
});

export const KPICardSkeleton: React.FC = () => (
  <Card style={styles.card}>
    <Card.Content>
      <View style={[styles.iconContainer, { backgroundColor: '#E0E0E0' }]} />
      <View style={{ height: 28, backgroundColor: '#E0E0E0', borderRadius: 4, marginVertical: 8, width: '60%' }} />
      <View style={{ height: 16, backgroundColor: '#E0E0E0', borderRadius: 4, marginBottom: 12, width: '40%' }} />
      <View style={{ height: 6, backgroundColor: '#E0E0E0', borderRadius: 3 }} />
    </Card.Content>
  </Card>
);

