import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Alert,
  AppBar,
  Box,
  CssBaseline,
  Grid,
  Paper,
  Tab,
  Tabs,
  Toolbar,
  Typography,
} from '@mui/material';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

function App() {
  const [tab, setTab] = useState(0);
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const load = async () => {
      const [metricRes, alertRes, predictionRes] = await Promise.all([
        fetch(`${API}/api/observability/metrics/live`),
        fetch(`${API}/api/observability/alerts`),
        fetch(`${API}/api/observability/prediction`),
      ]);
      const metricData = await metricRes.json();
      const alertData = await alertRes.json();
      const predictionData = await predictionRes.json();
      setMetrics(metricData);
      setAlerts(alertData.alerts || []);
      setPrediction(predictionData);
      setHistory((items) => [
        ...items.slice(-29),
        {
          time: new Date().toLocaleTimeString(),
          deployments: metricData.deployment_frequency?.per_day || 0,
          failureRate: metricData.change_failure_rate?.rate_pct || 0,
          mttr: metricData.mean_time_to_restore?.avg_minutes || 0,
          leadTime: metricData.lead_time_for_change?.avg_minutes || 0,
        },
      ]);
    };
    load();
    const timer = setInterval(load, 1000);
    return () => clearInterval(timer);
  }, []);

  const cards = useMemo(() => {
    if (!metrics) return [];
    return [
      ['Deployment Frequency', metrics.deployment_frequency?.per_day ?? 0, 'per day'],
      ['Lead Time', metrics.lead_time_for_change?.avg_minutes ?? 0, 'minutes'],
      ['MTTR', metrics.mean_time_to_restore?.avg_minutes ?? 0, 'minutes'],
      ['Change Failure Rate', metrics.change_failure_rate?.rate_pct ?? 0, '%'],
    ];
  }, [metrics]);

  return (
    <Box className="app-shell">
      <CssBaseline />
      <AppBar position="static" color="inherit" elevation={0}>
        <Toolbar className="toolbar">
          <Typography variant="h6">Real-Time CI/CD Observability</Typography>
          <Tabs value={tab} onChange={(_, value) => setTab(value)}>
            <Tab label="Live Metrics" />
            <Tab label="Alerts" />
            <Tab label="Benchmarks" />
          </Tabs>
        </Toolbar>
      </AppBar>

      <Box component="main" className="content">
        {tab === 0 && (
          <>
            <Grid container spacing={2}>
              {cards.map(([label, value, suffix]) => (
                <Grid item xs={12} sm={6} md={3} key={label}>
                  <Paper className="metric-card">
                    <Typography variant="body2" color="text.secondary">{label}</Typography>
                    <Typography variant="h4">{value}</Typography>
                    <Typography variant="caption">{suffix}</Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
            <Paper className="chart-panel">
              <Typography variant="h6">Live DORA Trend</Typography>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="deployments" stroke="#1976d2" dot={false} />
                  <Line type="monotone" dataKey="failureRate" stroke="#d32f2f" dot={false} />
                  <Line type="monotone" dataKey="mttr" stroke="#2e7d32" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </>
        )}

        {tab === 1 && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <Paper className="chart-panel">
                <Typography variant="h6">Active Alerts</Typography>
                {alerts.length === 0 && <Alert severity="success">No active alerts</Alert>}
                {alerts.map((item) => (
                  <Alert severity={item.severity === 'CRITICAL' ? 'error' : 'warning'} key={item.alert_id} className="alert-row">
                    <strong>{item.name}</strong> {item.description}
                  </Alert>
                ))}
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper className="metric-card">
                <Typography variant="body2" color="text.secondary">Deployment Failure Probability</Typography>
                <Typography variant="h3">{prediction ? Math.round(prediction.risk_score * 100) : 0}%</Typography>
                <Typography>{prediction?.prediction || 'LOW_RISK'}</Typography>
              </Paper>
            </Grid>
          </Grid>
        )}

        {tab === 2 && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper className="chart-panel">
                <Typography variant="h6">Throughput</Typography>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={[100, 500, 1000, 5000, 10000].map((rate) => ({ rate, eps: rate }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="rate" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="eps" fill="#1976d2" />
                  </BarChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper className="chart-panel">
                <Typography variant="h6">Latency and Accuracy</Typography>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={[{ name: 'Batch', latency: 600, accuracy: 95 }, { name: 'Kafka-Flink', latency: 1, accuracy: 99 }]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Area dataKey="latency" fill="#f57c00" stroke="#f57c00" />
                    <Area dataKey="accuracy" fill="#2e7d32" stroke="#2e7d32" />
                  </AreaChart>
                </ResponsiveContainer>
              </Paper>
            </Grid>
          </Grid>
        )}
      </Box>
    </Box>
  );
}

createRoot(document.getElementById('root')).render(<App />);

