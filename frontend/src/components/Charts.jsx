import React from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from 'recharts';

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#84cc16'];

/**
 * Render a responsive line chart with configurable axes, height, and line color.
 * @param {Array<Object>} data - The data points displayed in the chart.
 * @param {string} xKey - The data property used for the horizontal axis.
 * @param {string} yKey - The data property used for the vertical axis and line values.
 * @param {number} [height=300] - The chart height in pixels.
 * @param {string} [color='#4f46e5'] - The line and point color.
 */
export function LineChartComponent({ data, xKey, yKey, height = 300, color = '#4f46e5' }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey={xKey} tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
        <YAxis tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-card)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            color: 'var(--color-text)'
          }}
        />
        <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={{ fill: color }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

/**
 * Renders a responsive bar chart from the provided data.
 * @param {Array<Object>} data - The chart data.
 * @param {string} xKey - The data property used for x-axis labels.
 * @param {string} yKey - The data property used for bar values.
 * @param {number} [height=300] - The chart height in pixels.
 * @param {string} [color='#4f46e5'] - The bar color.
 * @returns {JSX.Element} The rendered bar chart.
 */
export function BarChartComponent({ data, xKey, yKey, height = 300, color = '#4f46e5' }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey={xKey} tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
        <YAxis tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-card)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            color: 'var(--color-text)'
          }}
        />
        <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/**
 * Renders a responsive donut chart with labeled segments and a legend.
 * @param {Array<Object>} data - The data records used to create the chart segments.
 * @param {string} nameKey - The property containing each segment's label.
 * @param {string} valueKey - The property containing each segment's numeric value.
 * @param {number} [height=300] - The chart height in pixels.
 * @return {JSX.Element} The rendered pie chart.
 */
export function PieChartComponent({ data, nameKey, valueKey, height = 300 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={5}
          dataKey={valueKey}
          nameKey={nameKey}
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-card)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            color: 'var(--color-text)'
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

/**
 * Renders a responsive area chart with configurable axes, dimensions, and color.
 * @param {Array<Object>} data - The data points to display.
 * @param {string} xKey - The property used for x-axis values.
 * @param {string} yKey - The property used for area values.
 * @param {number} [height=300] - The chart height in pixels.
 * @param {string} [color='#4f46e5'] - The color used for the area and gradient.
 * @returns {JSX.Element} The rendered area chart.
 */
export function AreaChartComponent({ data, xKey, yKey, height = 300, color = '#4f46e5' }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <defs>
          <linearGradient id={`gradient-${yKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis dataKey={xKey} tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
        <YAxis tick={{ fill: 'var(--color-text-secondary)', fontSize: 12 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-card)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            color: 'var(--color-text)'
          }}
        />
        <Area type="monotone" dataKey={yKey} stroke={color} fill={`url(#gradient-${yKey})`} strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/**
 * Renders a compact line chart without axes, gridlines, tooltips, or point markers.
 * @param {Array} data - The chart data.
 * @param {string} dataKey - The property containing the values to plot.
 * @param {number} [width=120] - The chart width.
 * @param {number} [height=40] - The chart height.
 * @param {string} [color='#4f46e5'] - The line color.
 */
export function Sparkline({ data, dataKey, width = 120, height = 40, color = '#4f46e5' }) {
  return (
    <ResponsiveContainer width={width} height={height}>
      <LineChart data={data}>
        <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

