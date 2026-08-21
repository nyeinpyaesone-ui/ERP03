import React from 'react';
import { View, StyleSheet } from 'react-native';
import { SegmentedButtons, Menu, Button } from 'react-native-paper';
import { DashboardFilter } from '../types/dashboard';
import { DASHBOARD_PERIODS, COMPARE_OPTIONS } from '../constants/dashboard';

interface PeriodFilterProps {
  filter: DashboardFilter;
  onPeriodChange: (period: string) => void;
  onCompareChange: (compare: 'previous_period' | 'previous_year') => void;
}

export const PeriodFilter: React.FC<PeriodFilterProps> = ({
  filter,
  onPeriodChange,
  onCompareChange,
}) => {
  const [compareMenuVisible, setCompareMenuVisible] = React.useState(false);

  return (
    <View style={styles.container}>
      <SegmentedButtons
        value={filter.period}
        onValueChange={onPeriodChange}
        buttons={DASHBOARD_PERIODS.map(period => ({
          value: period.value,
          label: period.label,
          style: styles.segmentButton,
        }))}
        style={styles.segmentGroup}
      />
      <Menu
        visible={compareMenuVisible}
        onDismiss={() => setCompareMenuVisible(false)}
        anchor={
          <Button
            mode="outlined"
            onPress={() => setCompareMenuVisible(true)}
            style={styles.compareButton}
            icon="compare"
          >
            {COMPARE_OPTIONS.find(o => o.value === filter.compareWith)?.label || 'Compare'}
          </Button>
        }
      >
        {COMPARE_OPTIONS.map(option => (
          <Menu.Item
            key={option.value}
            onPress={() => {
              onCompareChange(option.value as 'previous_period' | 'previous_year');
              setCompareMenuVisible(false);
            }}
            title={option.label}
            leadingIcon={filter.compareWith === option.value ? 'check' : undefined}
          />
        ))}
      </Menu>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  segmentGroup: {
    flex: 1,
  },
  segmentButton: {
    minWidth: 80,
  },
  compareButton: {
    minWidth: 140,
  },
});

