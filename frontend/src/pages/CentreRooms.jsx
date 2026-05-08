import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, DataGrid
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchRooms } from '../api/rooms';

const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'name', headerName: 'Room Name', flex: 1 },
  { field: 'capacity', headerName: 'Capacity', width: 100 },
  {
    field: 'has_projector',
    headerName: 'Projector',
    width: 100,
    valueGetter: (v) => (v ? 'Yes' : 'No'),
  },
  {
    field: 'has_whiteboard',
    headerName: 'Whiteboard',
    width: 100,
    valueGetter: (v) => (v ? 'Yes' : 'No'),
  },
];

export default function CentreRooms() {
  const { id } = useParams();
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadRooms();
  }, [id]);

  async function loadRooms() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRooms(id);
      setRooms(data.rooms || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load rooms');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        Rooms at Centre {id}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Box sx={{ height: 500, width: '100%' }}>
          <DataGrid
            rows={rooms}
            columns={columns}
            pageSizeOptions={[10, 25, 50]}
            initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
            onRowClick={(params) => navigate(`/rooms/${params.id}`)}
            sx={{ cursor: 'pointer' }}
          />
        </Box>
      )}
    </Container>
  );
}