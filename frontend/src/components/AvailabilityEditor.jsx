import React, { useState, useEffect } from 'react';
import {
  Typography, Paper, Box, Checkbox, FormControlLabel, Button, Alert,
} from '@mui/material';
import { fetchAvailability, bulkSetAvailability } from '../api/teachers';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIME_SLOTS = [
  { label: 'Morning (8:00-12:00)', start: '08:00', end: '12:00' },
  { label: 'Afternoon (13:00-17:00)', start: '13:00', end: '17:00' },
  { label: 'Evening (17:00-21:00)', start: '17:00', end: '21:00' },
];

export default function AvailabilityEditor({ teacherId }) {
  const [slots, setSlots] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAvailability();
  }, [teacherId]);

  async function loadAvailability() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAvailability(teacherId);
      const map = {};
      for (const s of data) {
        const key = `${s.day_of_week}_${s.start_time}`;
        map[key] = s.is_available;
      }
      setSlots(map);
    } catch (err) {
      setError('Failed to load availability');
    } finally {
      setLoading(false);
    }
  }

  function toggle(day, slot) {
    const key = `${day}_${slot.start}`;
    setSlots((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function isChecked(day, slot) {
    return slots[`${day}_${slot.start}`] ?? false;
  }

  async function handleSave() {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const payload = [];
      for (const day of DAYS) {
        for (const slot of TIME_SLOTS) {
          const key = `${day}_${slot.start}`;
          if (slots[key]) {
            payload.push({
              day_of_week: day,
              start_time: slot.start,
              end_time: slot.end,
              is_available: true,
            });
          }
        }
      }
      await bulkSetAvailability(teacherId, payload);
      setMessage(`Saved ${payload.length} availability slots`);
    } catch (err) {
      setError('Failed to save availability');
    } finally {
      setSaving(false);
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>Weekly Availability</Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}

      {loading ? (
        <Typography>Loading...</Typography>
      ) : (
        <Box>
          {DAYS.map((day) => (
            <Box key={day} sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
              <Typography sx={{ minWidth: 100, fontWeight: 500 }}>{day}</Typography>
              {TIME_SLOTS.map((slot) => (
                <FormControlLabel
                  key={slot.start}
                  control={
                    <Checkbox
                      checked={isChecked(day, slot)}
                      onChange={() => toggle(day, slot)}
                      size="small"
                    />
                  }
                  label={slot.label}
                  sx={{ '& .MuiFormControlLabel-label': { fontSize: '0.8rem' } }}
                />
              ))}
            </Box>
          ))}
          <Button variant="contained" onClick={handleSave} disabled={saving} sx={{ mt: 2 }}>
            {saving ? 'Saving...' : 'Save Availability'}
          </Button>
        </Box>
      )}
    </Paper>
  );
}