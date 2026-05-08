import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container, Typography, TextField, Button, Box, CircularProgress, Alert,
  MenuItem, Paper, Grid,
} from '@mui/material';
import { fetchTeacher, updateTeacher, createTeacher, deleteTeacher } from '../api/teachers';
import AvailabilityEditor from '../components/AvailabilityEditor';

export default function TeacherDetail() {
  const { id } = useParams();
  const isNew = id === 'new';
  const navigate = useNavigate();

  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', phone: '',
    contract_type: 'full_time', contracted_hours: 40,
    hourly_rate: '', salary: '',
    primary_centre_id: 1, status: 'active',
    qualifications: '', notes: '',
  });
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isNew) {
      loadTeacher();
    }
  }, [id]);

  async function loadTeacher() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTeacher(id, 'hr');
      setForm({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        email: data.email || '',
        phone: data.phone || '',
        contract_type: data.contract_type || 'full_time',
        contracted_hours: data.contracted_hours ?? 40,
        hourly_rate: data.hourly_rate ?? '',
        salary: data.salary ?? '',
        primary_centre_id: data.primary_centre_id || 1,
        status: data.status || 'active',
        qualifications: data.qualifications || '',
        notes: data.notes || '',
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load teacher');
    } finally {
      setLoading(false);
    }
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        hourly_rate: form.hourly_rate === '' ? null : Number(form.hourly_rate),
        salary: form.salary === '' ? null : Number(form.salary),
        contracted_hours: Number(form.contracted_hours),
      };
      if (isNew) {
        await createTeacher(payload);
      } else {
        await updateTeacher(id, payload);
      }
      navigate('/teachers');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save teacher');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm('Delete this teacher?')) return;
    setSaving(true);
    try {
      await deleteTeacher(id);
      navigate('/teachers');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Container sx={{ mt: 4 }}><CircularProgress /></Container>;

  return (
    <Container maxWidth="md" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        {isNew ? 'New Teacher' : `Edit Teacher #${id}`}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField fullWidth label="First Name" name="first_name" value={form.first_name} onChange={handleChange} required />
          </Grid>
          <Grid item xs={6}>
            <TextField fullWidth label="Last Name" name="last_name" value={form.last_name} onChange={handleChange} required />
          </Grid>
          <Grid item xs={6}>
            <TextField fullWidth label="Email" name="email" value={form.email} onChange={handleChange} required />
          </Grid>
          <Grid item xs={6}>
            <TextField fullWidth label="Phone" name="phone" value={form.phone} onChange={handleChange} />
          </Grid>
          <Grid item xs={4}>
            <TextField select fullWidth label="Contract" name="contract_type" value={form.contract_type} onChange={handleChange}>
              <MenuItem value="full_time">Full-Time</MenuItem>
              <MenuItem value="part_time">Part-Time</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={4}>
            <TextField fullWidth label="Hours/Week" name="contracted_hours" type="number" value={form.contracted_hours} onChange={handleChange} />
          </Grid>
          <Grid item xs={4}>
            <TextField select fullWidth label="Status" name="status" value={form.status} onChange={handleChange}>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="on_leave">On Leave</MenuItem>
              <MenuItem value="terminated">Terminated</MenuItem>
              <MenuItem value="onboarding">Onboarding</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={4}>
            <TextField fullWidth label="Hourly Rate (HR)" name="hourly_rate" type="number" value={form.hourly_rate} onChange={handleChange} />
          </Grid>
          <Grid item xs={4}>
            <TextField fullWidth label="Monthly Salary (HR)" name="salary" type="number" value={form.salary} onChange={handleChange} />
          </Grid>
          <Grid item xs={4}>
            <TextField select fullWidth label="Primary Centre" name="primary_centre_id" value={form.primary_centre_id} onChange={handleChange}>
              <MenuItem value={1}>JTH</MenuItem>
              <MenuItem value={2}>JLL</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth label="Qualifications" name="qualifications" value={form.qualifications} onChange={handleChange} />
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth label="Notes" name="notes" multiline rows={2} value={form.notes} onChange={handleChange} />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="outlined" onClick={() => navigate('/teachers')}>Cancel</Button>
          {!isNew && (
            <Button variant="outlined" color="error" onClick={handleDelete} disabled={saving}>
              Delete
            </Button>
          )}
        </Box>
      </Paper>

      {!isNew && <AvailabilityEditor teacherId={id} />}
    </Container>
  );
}