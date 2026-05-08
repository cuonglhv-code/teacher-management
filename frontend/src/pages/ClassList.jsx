import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, TextField, MenuItem,
  Table, TableHead, TableRow, TableCell, TableBody, Paper, Button, Chip,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { fetchClasses } from '../api/classes';

const STATUS_COLORS = {
  planned: 'default',
  approved: 'primary',
  timetabled: 'info',
  open: 'success',
  completed: 'secondary',
  cancelled: 'error',
};

export default function ClassList() {
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [centreFilter, setCentreFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const navigate = useNavigate();

  useEffect(() => { loadClasses(); }, [centreFilter, statusFilter]);

  async function loadClasses() {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (centreFilter) params.centre_id = centreFilter;
      if (statusFilter) params.status = statusFilter;
      const data = await fetchClasses(params);
      setClasses(data);
    } catch (err) {
      setError('Failed to load classes');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Classes</Typography>
        <Button variant="contained" onClick={() => navigate('/classes/new')}>+ New Class</Button>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField select label="Centre" size="small" sx={{ minWidth: 160 }}
          value={centreFilter} onChange={(e) => setCentreFilter(e.target.value)}>
          <MenuItem value="">All Centres</MenuItem>
          <MenuItem value="1">JTH</MenuItem>
          <MenuItem value="2">JLL</MenuItem>
        </TextField>
        <TextField select label="Status" size="small" sx={{ minWidth: 140 }}
          value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <MenuItem value="">All Statuses</MenuItem>
          <MenuItem value="planned">Planned</MenuItem>
          <MenuItem value="approved">Approved</MenuItem>
          <MenuItem value="timetabled">Timetabled</MenuItem>
          <MenuItem value="open">Open</MenuItem>
          <MenuItem value="completed">Completed</MenuItem>
          <MenuItem value="cancelled">Cancelled</MenuItem>
        </TextField>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? <CircularProgress /> : (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Centre</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Qualification</TableCell>
                <TableCell>Day/Time</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {classes.map((c) => (
                <TableRow key={c.id} hover sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/classes/${c.id}`)}>
                  <TableCell>{c.id}</TableCell>
                  <TableCell>{c.name}</TableCell>
                  <TableCell>{c.centre_id === 1 ? 'JTH' : 'JLL'}</TableCell>
                  <TableCell>{c.level || '-'}</TableCell>
                  <TableCell>{c.required_teacher_qualification || '-'}</TableCell>
                  <TableCell>
                    {c.preferred_day ? `${c.preferred_day} ${c.preferred_start_time?.slice(0, 5) || ''}` : '-'}
                  </TableCell>
                  <TableCell>
                    <Chip label={c.status} size="small" color={STATUS_COLORS[c.status] || 'default'} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
    </Container>
  );
}