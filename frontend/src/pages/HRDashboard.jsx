import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, Accordion, AccordionSummary,
  AccordionDetails, List, ListItem, ListItemText, Chip, Button, Paper
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useParams } from 'react-router-dom';
import client from '../api/client';

export default function HRDashboard() {
  const { id } = useParams();
  const [alerts, setAlerts] = useState(null);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [id]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const alertsRes = await client.get('/hr/alerts', {
        params: id ? { centre_id: id } : {}
      });
      setAlerts(alertsRes.data);
      
      const requestsRes = await client.get('/hr/headcount-requests', {
        params: id ? { centre_id: id } : {}
      });
      setRequests(requestsRes.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load HR data');
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(requestId) {
    try {
      await client.put(`/hr/headcount-requests/${requestId}/approve`, null, {
        params: { approved_by: 'hr_manager' }
      });
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve request');
    }
  }

  async function handleReject(requestId) {
    try {
      await client.put(`/hr/headcount-requests/${requestId}/reject`);
      loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reject request');
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      default: return 'info';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        HR Dashboard {id ? `- Centre ${id}` : ''}
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Alerts ({alerts?.total_alerts || 0})
            </Typography>
            {alerts?.alerts?.map((alert, index) => (
              <Accordion key={index}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    <Chip 
                      label={alert.type.replace('_', ' ').toUpperCase()} 
                      color={getSeverityColor(alert.severity)}
                      size="small"
                    />
                    <Typography sx={{ flexGrow: 1 }}>{alert.message}</Typography>
                    <Chip label={alert.severity} size="small" />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <pre>{JSON.stringify(alert, null, 2)}</pre>
                </AccordionDetails>
              </Accordion>
            ))}
            {(!alerts?.alerts || alerts.alerts.length === 0) && (
              <Typography color="text.secondary">No active alerts</Typography>
            )}
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Headcount Requests ({requests.length})
              </Typography>
              <Button variant="contained" color="primary">
                New Request
              </Button>
            </Box>
            <List>
              {requests.map((req) => (
                <ListItem key={req.id} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <Typography>Centre {req.centre_id}</Typography>
                        <Chip label={req.contract_type} size="small" />
                        <Chip label={`${req.hours_per_week}h/week`} size="small" />
                        <Chip 
                          label={req.status} 
                          color={
                            req.status === 'open' ? 'warning' :
                            req.status === 'approved' ? 'success' : 'default'
                          }
                          size="small"
                        />
                      </Box>
                    }
                    secondary={req.reason || 'No reason provided'}
                  />
                  {req.status === 'open' && (
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button size="small" color="primary" onClick={() => handleApprove(req.id)}>
                        Approve
                      </Button>
                      <Button size="small" color="error" onClick={() => handleReject(req.id)}>
                        Reject
                      </Button>
                    </Box>
                  )}
                </ListItem>
              ))}
              {requests.length === 0 && (
                <Typography color="text.secondary">No headcount requests</Typography>
              )}
            </List>
          </Paper>
        </>
      )}
    </Container>
  );
}