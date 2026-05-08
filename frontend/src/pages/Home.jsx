import React from 'react';
import { Container, Typography, Box, Button, Card, CardContent, Grid, CircularProgress } from '@mui/material';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { fetchCentre } from '../api/centres';
import { useTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';

export default function Home() {
  const { id } = useParams();
  const [centre, setCentre] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  React.useEffect(() => {
    if (id) {
      loadCentre();
    } else {
      setLoading(false);
    }
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h4" gutterBottom>
        {centre ? `${centre.name} - Home` : 'Welcome to JTWMS'}
      </Typography>
      
      <Grid container spacing={2} sx={{ mt: 2 }}>
        {/* Teacher Availability Button */}
        <Grid item xs={12} sm={6} md={4}>
          <Card 
            component={RouterLink} 
            to={id ? `/centres/${id}/availability` : '/availability'}
            sx={{ textDecoration: 'none' }}
          >
            <CardContent>
              <Typography variant="h6">Submit Weekly Availability</Typography>
              <Typography variant="body2" color="text.secondary">
                Tap here to update your weekly availability schedule
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* View Schedule */}
        <Grid item xs={12} sm={6} md={4}>
          <Card 
            component={RouterLink} 
            to={id ? `/centres/${id}/timetable` : '/timetable'}
            sx={{ textDecoration: 'none' }}
          >
            <CardContent>
              <Typography variant="h6">My Schedule</Typography>
              <Typography variant="body2" color="text.secondary">
                View your teaching schedule for the week
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Manager Links - shown if manager role */}
        {id && (
          <>
            <Grid item xs={12} sm={6} md={4}>
              <Card component={RouterLink} to={`/centres/${id}/teachers`} sx={{ textDecoration: 'none' }}>
                <CardContent>
                  <Typography variant="h6">Teachers</Typography>
                  <Typography variant="body2" color="text.secondary">Manage teachers</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card component={RouterLink} to={`/centres/${id}/classes`} sx={{ textDecoration: 'none' }}>
                <CardContent>
                  <Typography variant="h6">Classes</Typography>
                  <Typography variant="body2" color="text.secondary">Manage classes</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <Card component={RouterLink} to={`/centres/${id}/rooms`} sx={{ textDecoration: 'none' }}>
                <CardContent>
                  <Typography variant="h6">Rooms</Typography>
                  <Typography variant="body2" color="text.secondary">Manage rooms</Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>
    </Container>
  );
}