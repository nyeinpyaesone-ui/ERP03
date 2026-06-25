import React from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Text, Card } from 'react-native-paper';
import { LineChart } from 'react-native-chart-kit';
import { ChartData } from '../types/dashboard';
import { CHART_COLORS } from '../constants/dashboard';

interface LineChartCardProps {
  title: string;
  subtitle?: string;
  data: ChartData | null;
  loading: boolean;
  height?: number;
  yAxisLabel?: string;
  yAxisSuffix?: string;
  formatYLabel?: (value: string) => string;
}

export const LineChartCard: React.FC<LineChartCardProps> = ({
  title,
  subtitle,
  data,
  loading,
  height = 220,
  yAxisLabel = '',
  yAxisSuffix = '',
  formatYLabel,
}) => {
  if (loading || !data) {
    return (
      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.skeletonHeader}>
            <View style={{ height: 20, backgroundColor: '#E0E0E0', borderRadius: 4, width: '40%' }} />
          </View>
          <View style={[styles.skeletonChart, { height }]} />
        </Card.Content>
      </Card>
    );
  }

  const chartData = {
    labels: data.labels.slice(-7),
    datasets: data.datasets.map((ds, i) => ({
      data: ds.data.slice(-7),
      color: () => ds.color || CHART_COLORS.primary,
      strokeWidth: 2,
    })),
    legend: data.datasets.map(ds => ds.label),
  };

  const screenWidth = Dimensions.get('window').width - 48;

  return (
    <Card style={styles.card}>
      <Card.Content>
        <Text variant="titleMedium" style={styles.title}>{title}</Text>
        {subtitle && <Text variant="bodySmall" style={styles.subtitle}>{subtitle}</Text>}
        <LineChart
          data={chartData}
          width={screenWidth}
          height={height}
          chartConfig={{
            backgroundColor: '#fff',
            backgroundGradientFrom: '#fff',
            backgroundGradientTo: '#fff',
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(25, 118, 210, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
            style: {
              borderRadius: 8,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '2',
            },
            propsForLabels: {
              fontSize: 10,
            },
            formatYLabel: formatYLabel || ((value: string) => {
              const num = parseFloat(value);
              if (num >= 1000) return `${(num / 1000).toFixed(0)}k`;
              return value;
            }),
          }}
          bezier
          style={styles.chart}
          yAxisLabel={yAxisLabel}
          yAxisSuffix={yAxisSuffix}
          fromZero
        />
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    margin: 8,
  },
  title: {
    fontWeight: 'bold',
    marginBottom: 4,
  },
  subtitle: {
    color: '#666',
    marginBottom: 12,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 8,
  },
  skeletonHeader: {
    marginBottom: 12,
  },
  skeletonChart: {
    backgroundColor: '#E0E0E0',
    borderRadius: 8,
  },
});

