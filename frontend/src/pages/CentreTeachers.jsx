import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, DataGrid
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
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

export default function CentreTeachers() {
  const { id } = useParams();
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadTeachers();
  }, [id]);

  async function loadTeachers() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTeachers({ centre_id: id });
      setTeachers(data.teachers || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load teachers');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        Teachers at Centre {id}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
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