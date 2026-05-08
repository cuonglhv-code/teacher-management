import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, LinearProgress, Chip, Select, MenuItem
} from '@mui/material';
import { useParams } from 'react-router-dom';
import { fetchCentre, fetchCentres } from '../api/centres';
import client from '../api/client';

export default function WorkloadDashboard() {
  const { id } = useParams();
  const [centre, setCentre] = useState(null);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(() => {
    const today = new Date();
    const monday = new Date(today);
    monday.setDate(today.getDate() - (today.getDay() === 0 ? 6 : today.getDay() - 1));
    return monday.toISOString().split('T')[0];
  });

  useEffect(() => {
    loadData();
  }, [id, selectedWeek]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const centreData = await fetchCentre(id);
      setCentre(centreData);
      
      // Get teachers for this centre
      const teachersRes = await client.get('/teachers', {
        params: { centre_id: id }
      });
      
      // Fetch workload for each teacher
      const weekEnd = new Date(selectedWeek);
      weekEnd.setDate(weekEnd.getDate() + 6);
      const weekEndStr = weekEnd.toISOString().split('T')[0];
      
      const teachersWithWorkload = await Promise.all(
        teachersRes.data.teachers.map(async (t) => {
          try {
            const workload = await client.get(`/teachers/${t.id}/workload`, {
              params: { week_start: selectedWeek, week_end: weekEndStr }
            });
            return { ...t, workload: workload.data };
          } catch (e) {
            return { ...t, workload: null };
          }
        })
      );
      
      setTeachers(teachersWithWorkload);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  const getUtilizationColor = (pct) => {
    if (pct >= 80) return 'success';
    if (pct >= 60) return 'info';
    if (pct >= 40) return 'warning';
    return 'error';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        Workload Dashboard - Centre {id}
      </Typography>
      
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <Typography>Week Starting:</Typography>
        <input
          type="date"
          value={selectedWeek}
          onChange={(e) => setSelectedWeek(e.target.value)}
          style={{ padding: '8px' }}
        />
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Teacher</TableCell>
                <TableCell>Contract Type</TableCell>
                <TableCell>Contracted Hours</TableCell>
                <TableCell>Assigned Hours</TableCell>
                <TableCell>Utilization</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {teachers.map((t) => {
                const util = t.workload?.utilization_percentage || 0;
                return (
                  <TableRow key={t.id}>
                    <TableCell>{t.first_name} {t.last_name}</TableCell>
                    <TableCell>
                      <Chip 
                        label={t.contract_type === 'full_time' ? 'FT' : 'PT'} 
                        size="small" 
                        color={t.contract_type === 'full_time' ? 'primary' : 'default'} 
                      />
                    </TableCell>
                    <TableCell>{t.contracted_hours || 0}h</TableCell>
                    <TableCell>{t.workload?.assigned_hours?.toFixed(1) || 0}h</TableCell>
                    <TableCell sx={{ minWidth: 200 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={Math.min(util, 100)}
                          color={getUtilizationColor(util)}
                          sx={{ flexGrow: 1, height: 10, borderRadius: 5 }}
                        />
                        <Typography variant="caption">{util.toFixed(0)}%</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {util < 60 ? (
                        <Chip label="Under-utilized" color="warning" size="small" />
                      ) : util > 100 ? (
                        <Chip label="Overloaded" color="error" size="small" />
                      ) : (
                        <Chip label="Normal" color="success" size="small" />
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Container>
  );
}