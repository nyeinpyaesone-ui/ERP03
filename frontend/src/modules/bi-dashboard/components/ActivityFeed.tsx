import React from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Card, Text, Avatar, Divider } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { ActivityItem } from '../types/dashboard';
import { ACTIVITY_ICONS, ACTIVITY_COLORS } from '../constants/dashboard';
import { formatRelativeTime } from '../utils/dashboard';

interface ActivityFeedProps {
  activities: ActivityItem[] | null;
  loading: boolean;
  maxItems?: number;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  loading,
  maxItems = 10,
}) => {
  if (loading) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.title}>Recent Activity</Text>
          {[1, 2, 3, 4, 5].map(i => (
            <View key={i} style={styles.skeletonItem}>
              <View style={[styles.skeletonIcon, { backgroundColor: '#E0E0E0' }]} />
              <View style={styles.skeletonContent}>
                <View style={{ height: 16, backgroundColor: '#E0E0E0', borderRadius: 4, width: '70%' }} />
                <View style={{ height: 12, backgroundColor: '#E0E0E0', borderRadius: 4, width: '40%', marginTop: 4 }} />
              </View>
            </View>
          ))}
        </Card.Content>
      </Card>
    );
  }

  if (!activities || !activities.length) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.title}>Recent Activity</Text>
          <Text variant="bodyMedium" style={styles.emptyText}>No recent activity</Text>
        </Card.Content>
      </Card>
    );
  }

  const displayActivities = activities.slice(0, maxItems);

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.title}>Recent Activity</Text>
        <ScrollView style={styles.scrollView} nestedScrollEnabled>
          {displayActivities.map((activity, index) => (
            <View key={activity.id}>
              <View style={styles.item}>
                <View style={[
                  styles.iconContainer,
                  { backgroundColor: `${ACTIVITY_COLORS[activity.type] || '#757575'}15` },
                ]}>
                  <MaterialCommunityIcons
                    name={(ACTIVITY_ICONS[activity.type] || 'information-outline') as any}
                    size={18}
                    color={ACTIVITY_COLORS[activity.type] || '#757575'}
                  />
                </View>
                <View style={styles.content}>
                  <Text variant="bodyMedium" style={styles.activityTitle}>
                    {activity.title}
                  </Text>
                  <Text variant="bodySmall" style={styles.activityDescription}>
                    {activity.description}
                  </Text>
                  <View style={styles.metaRow}>
                    {activity.userName && (
                      <View style={styles.userRow}>
                        <Avatar.Text
                          size={16}
                          label={activity.userName.charAt(0).toUpperCase()}
                          style={styles.avatar}
                          labelStyle={{ fontSize: 8 }}
                        />
                        <Text variant="bodySmall" style={styles.userName}>
                          {activity.userName}
                        </Text>
                      </View>
                    )}
                    <Text variant="bodySmall" style={styles.timestamp}>
                      {formatRelativeTime(activity.timestamp)}
                    </Text>
                  </View>
                </View>
              </View>
              {index < displayActivities.length - 1 && <Divider style={styles.divider} />}
            </View>
          ))}
        </ScrollView>
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    margin: 8,
    maxHeight: 400,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  scrollView: {
    maxHeight: 340,
  },
  item: {
    flexDirection: 'row',
    paddingVertical: 10,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  activityTitle: {
    fontWeight: '500',
  },
  activityDescription: {
    color: '#666',
    marginTop: 2,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  userRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  avatar: {
    backgroundColor: '#E0E0E0',
  },
  userName: {
    color: '#888',
  },
  timestamp: {
    color: '#888',
  },
  divider: {
    marginLeft: 48,
  },
  emptyText: {
    color: '#888',
    textAlign: 'center',
    paddingVertical: 20,
  },
  skeletonItem: {
    flexDirection: 'row',
    paddingVertical: 10,
    alignItems: 'center',
  },
  skeletonIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    marginRight: 12,
  },
  skeletonContent: {
    flex: 1,
  },
});

