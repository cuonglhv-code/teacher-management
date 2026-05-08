import React, { useState, useEffect } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert,
  Table, TableHead, TableRow, TableCell, TableBody, Paper,
  TextField, MenuItem, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, Checkbox, FormControlLabel,
} from '@mui/material';
import { fetchRooms, createRoom, updateRoom, deleteRoom } from '../api/rooms';

export default function RoomList() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [centreFilter, setCentreFilter] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editRoom, setEditRoom] = useState(null);
  const [form, setForm] = useState({ centre_id: 1, name: '', capacity: 1, has_projector: false, has_whiteboard: true, notes: '' });

  useEffect(() => { loadRooms(); }, [centreFilter]);

  async function loadRooms() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRooms(centreFilter || undefined);
      setRooms(data);
    } catch (err) {
      setError('Failed to load rooms');
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setEditRoom(null);
    setForm({ centre_id: 1, name: '', capacity: 1, has_projector: false, has_whiteboard: true, notes: '' });
    setDialogOpen(true);
  }

  function openEdit(room) {
    setEditRoom(room);
    setForm({ centre_id: room.centre_id, name: room.name, capacity: room.capacity, has_projector: room.has_projector, has_whiteboard: room.has_whiteboard, notes: room.notes || '' });
    setDialogOpen(true);
  }

  async function handleSave() {
    try {
      if (editRoom) {
        await updateRoom(editRoom.id, form);
      } else {
        await createRoom(form);
      }
      setDialogOpen(false);
      loadRooms();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save room');
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this room?')) return;
    try {
      await deleteRoom(id);
      loadRooms();
    } catch (err) {
      setError('Failed to delete room');
    }
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Rooms</Typography>
        <Button variant="contained" onClick={openCreate}>+ New Room</Button>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField select label="Centre" size="small" sx={{ minWidth: 160 }}
          value={centreFilter} onChange={(e) => setCentreFilter(e.target.value)}>
          <MenuItem value="">All Centres</MenuItem>
          <MenuItem value="1">JTH</MenuItem>
          <MenuItem value="2">JLL</MenuItem>
        </TextField>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? <CircularProgress /> : (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Centre</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Capacity</TableCell>
                <TableCell>Projector</TableCell>
                <TableCell>Whiteboard</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rooms.map((r) => (
                <TableRow key={r.id}>
                  <TableCell>{r.id}</TableCell>
                  <TableCell>{r.centre_id === 1 ? 'JTH' : 'JLL'}</TableCell>
                  <TableCell>{r.name}</TableCell>
                  <TableCell>{r.capacity}</TableCell>
                  <TableCell>{r.has_projector ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{r.has_whiteboard ? 'Yes' : 'No'}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => openEdit(r)}>Edit</Button>
                    <Button size="small" color="error" onClick={() => handleDelete(r.id)}>Delete</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>{editRoom ? 'Edit Room' : 'New Room'}</DialogTitle>
        <DialogContent>
          <TextField select label="Centre" fullWidth sx={{ mt: 2 }}
            value={form.centre_id} onChange={(e) => setForm({ ...form, centre_id: Number(e.target.value) })}>
            <MenuItem value={1}>JTH</MenuItem>
            <MenuItem value={2}>JLL</MenuItem>
          </TextField>
          <TextField label="Room Name" fullWidth sx={{ mt: 2 }}
            value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <TextField label="Capacity" type="number" fullWidth sx={{ mt: 2 }}
            value={form.capacity} onChange={(e) => setForm({ ...form, capacity: Number(e.target.value) })} />
          <FormControlLabel control={<Checkbox checked={form.has_projector} onChange={(e) => setForm({ ...form, has_projector: e.target.checked })} />} label="Has Projector" sx={{ mt: 1 }} />
          <FormControlLabel control={<Checkbox checked={form.has_whiteboard} onChange={(e) => setForm({ ...form, has_whiteboard: e.target.checked })} />} label="Has Whiteboard" />
          <TextField label="Notes" multiline rows={2} fullWidth sx={{ mt: 2 }}
            value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}