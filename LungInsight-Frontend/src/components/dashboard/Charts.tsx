import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Card } from '@/components/ui/Card';
import type { ConfidenceTrendPoint, DistributionSlice } from '@/types';

const CYAN = '#0891a8';
const FLAG = '#b8433a';

export function ConfidenceTrendChart({ data }: { data: ConfidenceTrendPoint[] }) {
  return (
    <Card>
      <h3 className="font-display text-sm font-semibold text-ink">Confidence trend</h3>
      <p className="text-xs text-steel">Average model confidence over time</p>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#dde3ee" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: '#5c6b85' }}
              tickFormatter={(v: string) => new Date(v).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
            />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#5c6b85' }} />
            <Tooltip
              contentStyle={{ borderRadius: 8, borderColor: '#dde3ee', fontSize: 12 }}
              formatter={(value) => [`${value}%`, 'Avg. confidence']}
              labelFormatter={(v) => (typeof v === 'string' ? new Date(v).toLocaleDateString() : String(v))}
            />
            <Line type="monotone" dataKey="averageConfidence" stroke={CYAN} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export function DistributionChart({ data }: { data: DistributionSlice[] }) {
  const colors: Record<string, string> = { Normal: CYAN, Pneumonia: FLAG };
  return (
    <Card>
      <h3 className="font-display text-sm font-semibold text-ink">Prediction distribution</h3>
      <p className="text-xs text-steel">Normal vs. Pneumonia calls</p>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="count" nameKey="label" innerRadius={55} outerRadius={85} paddingAngle={3}>
              {data.map((entry) => (
                <Cell key={entry.label} fill={colors[entry.label]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ borderRadius: 8, borderColor: '#dde3ee', fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
