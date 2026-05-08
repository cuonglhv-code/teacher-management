import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Button, Box, CircularProgress, Alert,
  TextField, MenuItem,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useNavigate } from 'react-router-dom';
import { fetchTeachers } from '../api/teachers';

const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'first_name', headerName: 'First Name', flex: 1 },
  { field: 'last_name', headerName: 'Last Name', flex: 1 },
  { field: 'email', headerName: 'Email', flex: 1.5 },
  {
    field: 'contract_type',
    headerName: 'Contract',
    width: 120,
    valueGetter: (v) => (v === 'full_time' ? 'Full-Time' : 'Part-Time'),
  },
  { field: 'contracted_hours', headerName: 'Hours/Week', width: 110 },
  {
    field: 'status',
    headerName: 'Status',
    width: 110,
    valueGetter: (v) => v?.charAt(0).toUpperCase() + v?.slice(1).replace('_', ' '),
  },
];

export default function TeacherList() {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [centreFilter, setCentreFilter] = useState('');
  const [contractFilter, setContractFilter] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadTeachers();
  }, [centreFilter, contractFilter]);

  async function loadTeachers() {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (centreFilter) params.centre_id = centreFilter;
      if (contractFilter) params.contract_type = contractFilter;
      const data = await fetchTeachers(params);
      setTeachers(data.teachers || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load teachers');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Teachers</Typography>
        <Button variant="contained" onClick={() => navigate('/teachers/new')}>
          + New Teacher
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField
          select label="Centre" size="small" sx={{ minWidth: 160 }}
          value={centreFilter} onChange={(e) => setCentreFilter(e.target.value)}
        >
          <MenuItem value="">All Centres</MenuItem>
          <MenuItem value="1">JTH</MenuItem>
          <MenuItem value="2">JLL</MenuItem>
        </TextField>
        <TextField
          select label="Contract" size="small" sx={{ minWidth: 140 }}
          value={contractFilter} onChange={(e) => setContractFilter(e.target.value)}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="full_time">Full-Time</MenuItem>
          <MenuItem value="part_time">Part-Time</MenuItem>
        </TextField>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <CircularProgress />
      ) : (
        <Box sx={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={teachers}
            columns={columns}
            pageSizeOptions={[10, 25, 50]}
            initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
            onRowClick={(params) => navigate(`/teachers/${params.id}`)}
            sx={{ cursor: 'pointer' }}
          />
        </Box>
      )}
    </Container>
  );
}