import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container, Typography, TextField, Button, Box, CircularProgress, Alert,
  MenuItem, Paper, Grid, Chip,
} from '@mui/material';
import { fetchClass, updateClass, createClass, deleteClass } from '../api/classes';

const DAYS = ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const STATUS_OPTIONS = ['planned', 'approved', 'timetabled', 'open', 'completed', 'cancelled'];

export default function ClassDetail() {
  const { id } = useParams();
  const isNew = id === 'new';
  const navigate = useNavigate();

  const [form, setForm] = useState({
    centre_id: 1, name: '', level: '', required_teacher_qualification: '',
    preferred_day: '', preferred_start_time: '', preferred_end_time: '',
    duration_minutes: '', max_students: 1, notes: '',
    status: 'planned',
  });
  const [loading, setLoading] = useState(!isNew);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { if (!isNew) loadClass(); }, [id]);

  async function loadClass() {
    setLoading(true);
    try {
      const data = await fetchClass(id);
      setForm({
        centre_id: data.centre_id,
        name: data.name || '',
        level: data.level || '',
        required_teacher_qualification: data.required_teacher_qualification || '',
        preferred_day: data.preferred_day || '',
        preferred_start_time: data.preferred_start_time?.slice(0, 5) || '',
        preferred_end_time: data.preferred_end_time?.slice(0, 5) || '',
        duration_minutes: data.duration_minutes ?? '',
        max_students: data.max_students ?? 1,
        notes: data.notes || '',
        status: data.status || 'planned',
      });
    } catch (err) {
      setError('Failed to load class');
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
        duration_minutes: form.duration_minutes === '' ? null : Number(form.duration_minutes),
        max_students: Number(form.max_students),
        preferred_start_time: form.preferred_start_time || null,
        preferred_end_time: form.preferred_end_time || null,
      };
      if (isNew) {
        await createClass(payload);
      } else {
        await updateClass(id, payload);
      }
      navigate('/classes');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save class');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm('Delete this class?')) return;
    try {
      await deleteClass(id);
      navigate('/classes');
    } catch (err) {
      setError('Failed to delete');
    }
  }

  if (loading) return <Container sx={{ mt: 4 }}><CircularProgress /></Container>;

  return (
    <Container maxWidth="md" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        {isNew ? 'New Class' : `Edit Class #${id}`}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <TextField select fullWidth label="Centre" name="centre_id"
              value={form.centre_id} onChange={handleChange}>
              <MenuItem value={1}>JTH</MenuItem>
              <MenuItem value={2}>JLL</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={6}>
            <TextField select fullWidth label="Status" name="status"
              value={form.status} onChange={handleChange}
              disabled={isNew}>
              {STATUS_OPTIONS.map((s) => (
                <MenuItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={8}>
            <TextField fullWidth label="Class Name" name="name" value={form.name} onChange={handleChange} required />
          </Grid>
          <Grid item xs={4}>
            <TextField fullWidth label="Level" name="level" value={form.level} onChange={handleChange} />
          </Grid>
          <Grid item xs={6}>
            <TextField fullWidth label="Required Qualification" name="required_teacher_qualification"
              value={form.required_teacher_qualification} onChange={handleChange} />
          </Grid>
          <Grid item xs={3}>
            <TextField fullWidth label="Max Students" name="max_students" type="number"
              value={form.max_students} onChange={handleChange} />
          </Grid>
          <Grid item xs={3}>
            <TextField fullWidth label="Duration (min)" name="duration_minutes" type="number"
              value={form.duration_minutes} onChange={handleChange} />
          </Grid>
          <Grid item xs={4}>
            <TextField select fullWidth label="Preferred Day" name="preferred_day"
              value={form.preferred_day} onChange={handleChange}>
              {DAYS.map((d) => (
                <MenuItem key={d} value={d}>{d || 'None'}</MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={4}>
            <TextField fullWidth label="Start Time" name="preferred_start_time" type="time"
              value={form.preferred_start_time} onChange={handleChange}
              InputLabelProps={{ shrink: true }} />
          </Grid>
          <Grid item xs={4}>
            <TextField fullWidth label="End Time" name="preferred_end_time" type="time"
              value={form.preferred_end_time} onChange={handleChange}
              InputLabelProps={{ shrink: true }} />
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth label="Notes" name="notes" multiline rows={2}
              value={form.notes} onChange={handleChange} />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="outlined" onClick={() => navigate('/classes')}>Cancel</Button>
          {!isNew && (
            <Button variant="outlined" color="error" onClick={handleDelete} disabled={saving}>
              Delete
            </Button>
          )}
        </Box>
      </Paper>
    </Container>
  );
}