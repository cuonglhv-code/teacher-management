import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, Paper,
  FormControl, InputLabel, Select, MenuItem, Button, Table,
  TableBody, TableCell, TableContainer, TableHead, TableRow,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import client from '../api/client';

export default function ReportsPage() {
  const [reportType, setReportType] = useState('utilisation');
  const [centreId, setCentreId] = useState('');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function generateReport() {
    setLoading(true);
    setError(null);
    try {
      const params = { centre_id: centreId || undefined };
      if (startDate) params.start_date = startDate.toISOString().split('T')[0];
      if (endDate) params.end_date = endDate.toISOString().split('T')[0];
      
      let endpoint = '/reports/kpi/';
      if (reportType === 'fill-rate') endpoint += 'fill-rate';
      else if (reportType === 'utilisation') endpoint += 'utilisation';
      else if (reportType === 'cost-efficiency') endpoint += 'cost-efficiency';
      
      const res = await client.get(endpoint, { params });
      setData(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  }

  async function exportCSV() {
    try {
      const params = { report_type: reportType };
      if (startDate) params.start_date = startDate.toISOString().split('T')[0];
      if (endDate) params.end_date = endDate.toISOString().split('T')[0];
      
      const res = await client.get('/reports/export/csv', {
        params,
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${reportType}_report.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to export CSV');
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        Reports & Analytics
      </Typography>
      
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Report Type</InputLabel>
            <Select
              value={reportType}
              label="Report Type"
              onChange={(e) => setReportType(e.target.value)}
            >
              <MenuItem value="fill-rate">Fill Rate</MenuItem>
              <MenuItem value="utilisation">Utilisation</MenuItem>
              <MenuItem value="cost-efficiency">Cost Efficiency</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Centre (Optional)</InputLabel>
            <Select
              value={centreId}
              label="Centre (Optional)"
              onChange={(e) => setCentreId(e.target.value)}
            >
              <MenuItem value="">All Centres</MenuItem>
              <MenuItem value="1">Centre 1</MenuItem>
              <MenuItem value="2">Centre 2</MenuItem>
            </Select>
          </FormControl>
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DatePicker
              label="Start Date"
              value={startDate}
              onChange={(newValue) => setStartDate(newValue)}
              renderInput={(params) => <TextField {...params} size="small" />}
            />
            <DatePicker
              label="End Date"
              value={endDate}
              onChange={(newValue) => setEndDate(newValue)}
              renderInput={(params) => <TextField {...params} size="small" />}
            />
          </LocalizationProvider>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={generateReport} disabled={loading}>
            Generate Report
          </Button>
          <Button variant="outlined" onClick={exportCSV} disabled={!data}>
            Export CSV
          </Button>
        </Box>
      </Paper>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : data ? (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report
          </Typography>
          
          {reportType === 'utilisation' && data.teachers && (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Teacher</TableCell>
                    <TableCell>Centre</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Contracted</TableCell>
                    <TableCell>Assigned</TableCell>
                    <TableCell>Utilisation %</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {data.teachers.map((t) => (
                    <TableRow key={t.teacher_id}>
                      <TableCell>{t.teacher_name}</TableCell>
                      <TableCell>{t.centre_id}</TableCell>
                      <TableCell>{t.contract_type}</TableCell>
                      <TableCell>{t.contracted_hours}h</TableCell>
                      <TableCell>{t.assigned_hours}h</TableCell>
                      <TableCell>{t.utilisation_percentage?.toFixed(1)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          
          {reportType === 'fill-rate' && (
            <Box>
              <Typography>Total Classes: {data.total_classes}</Typography>
              <Typography>Timetabled: {data.timetabled_classes}</Typography>
              <Typography>Fill Rate: {data.fill_rate_percentage?.toFixed(1)}%</Typography>
            </Box>
          )}
          
          {reportType === 'cost-efficiency' && (
            <Box>
              <Typography>Planned Cost: ${data.total_planned_cost?.toFixed(2)}</Typography>
              <Typography>Actual Cost: ${data.total_actual_cost?.toFixed(2)}</Typography>
              <Typography>Efficiency: {data.efficiency_percentage?.toFixed(1)}%</Typography>
            </Box>
          )}
        </Paper>
      ) : null}
    </Container>
  );
}