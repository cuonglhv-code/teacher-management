import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, Card, CardContent, Grid, CircularProgress } from '@mui/material';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { fetchCentre } from '../api/centres';

export default function CentreDashboard() {
  const { id } = useParams();
  const [centre, setCentre] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCentre();
  }, [id]);

  async function loadCentre() {
    try {
      const data = await fetchCentre(id);
      setCentre(data);
    } catch (err) {
      console.error('Failed to load centre:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h4" gutterBottom>
        {centre?.name || `Centre ${id}`} Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Centre Code: {centre?.code}
      </Typography>

      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card component={RouterLink} to={`/centres/${id}/teachers`} sx={{ textDecoration: 'none' }}>
            <CardContent>
              <Typography variant="h6">Teachers</Typography>
              <Typography variant="body2" color="text.secondary">View and manage teachers</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card component={RouterLink} to={`/centres/${id}/classes`} sx={{ textDecoration: 'none' }}>
            <CardContent>
              <Typography variant="h6">Classes</Typography>
              <Typography variant="body2" color="text.secondary">View and manage classes</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card component={RouterLink} to={`/centres/${id}/rooms`} sx={{ textDecoration: 'none' }}>
            <CardContent>
              <Typography variant="h6">Rooms</Typography>
              <Typography variant="body2" color="text.secondary">View and manage rooms</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card component={RouterLink} to={`/centres/${id}/timetable`} sx={{ textDecoration: 'none' }}>
            <CardContent>
              <Typography variant="h6">Timetable</Typography>
              <Typography variant="body2" color="text.secondary">View published timetable</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}