import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchClasses } from '../api/classes';

const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'name', headerName: 'Class Name', flex: 1 },
  { field: 'level', headerName: 'Level', width: 100 },
  {
    field: 'status',
    headerName: 'Status',
    width: 120,
    valueGetter: (v) => v?.charAt(0).toUpperCase() + v?.slice(1).replace('_', ' '),
  },
  { field: 'max_students', headerName: 'Max Students', width: 120 },
];

export default function CentreClasses() {
  const { id } = useParams();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadClasses();
  }, [id]);

  async function loadClasses() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchClasses({ centre_id: id });
      setClasses(data.classes || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load classes');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        Classes at Centre {id}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={classes}
            columns={columns}
            pageSizeOptions={[10, 25, 50]}
            initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
            onRowClick={(params) => navigate(`/classes/${params.id}`)}
            sx={{ cursor: 'pointer' }}
          />
        </Box>
      )}
    </Container>
  );
}