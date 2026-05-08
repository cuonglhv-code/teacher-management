import React, { useEffect, useState } from 'react';
import {
  Container, Typography, Box, CircularProgress, Alert, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip,
  useMediaQuery, Stack, List, ListItem, ListItemText, Divider
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useParams } from 'react-router-dom';
import { fetchCentreDraft } from '../api/timetable';

// Define time slots for the week
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const TIME_SLOTS = [
  '08:00-09:30',
  '09:30-11:00',
  '11:00-12:30',
  '13:30-15:00',
  '15:00-16:30',
  '16:30-18:00',
  '18:00-19:30',
  '19:30-21:00',
];

export default function CentreTimetable() {
  const { id } = useParams();
  const [timetableData, setTimetableData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md')); // <960px

  useEffect(() => {
    loadTimetable();
  }, [id]);

  async function loadTimetable() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCentreDraft(id);
      setTimetableData(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load timetable');
    } finally {
      setLoading(false);
    }
  }

  const renderMobileList = () => {
    if (!timetableData || !timetableData.slots) return null;
    
    const { slots } = timetableData;
    
    // Group slots by day for mobile view
    const slotsByDay = {};
    slots.forEach(slot => {
      const day = slot.day_of_week;
      if (!slotsByDay[day]) {
        slotsByDay[day] = [];
      }
      slotsByDay[day].push(slot);
        });
    
    const sortedDays = DAYS.filter(day => slotsByDay[day]);
    
    return (
      <Stack spacing={2}>
        {sortedDays.map(day => (
          <Paper key={day} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>{day}</Typography>
            <List dense>
              {slotsByDay[day].map((slot, index) => (
                <React.Fragment key={slot.id}>
                  {index > 0 && <Divider />}
                  <ListItem>
                    <ListItemText
                      primary={slot.class_name || `Class ${slot.class_id}`}
                      secondary={
                        <>
                          <span>{slot.start_time} - {slot.end_time}</span>
                          <br />
                          <span>Room: {slot.room_id || 'Unassigned'}</span>
                          <br />
                          <span>Teacher: {slot.teacher_name || `Teacher ${slot.teacher_id}`}</span>
                        </>
                      }
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </Paper>
        ))}
      </Stack>
    );
  };

  const renderDesktopTable = () => {
    if (!timetableData || !timetableData.slots) return null;

    const { draft, slots } = timetableData;

    // Group slots by room
    const roomMap = {};
    slots.forEach(slot => {
      const roomKey = slot.room_id || `no-room-${slot.id}`;
      if (!roomMap[roomKey]) {
        roomMap[roomKey] = {
          roomName: `Room ${slot.room_id || 'Unassigned'}`,
          slots: {},
        };
      }
      const timeKey = `${slot.day_of_week}-${slot.start_time}-${slot.end_time}`;
      roomMap[roomKey].slots[timeKey] = slot;
    });

    // Create time slot headers
    const timeSlotHeaders = [];
    DAYS.forEach(day => {
      TIME_SLOTS.forEach(timeSlot => {
        timeSlotHeaders.push({ day, time: timeSlot, key: `${day}-${timeSlot}` });
      });
    });

    return (
      <TableContainer component={Paper}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ minWidth: 120, fontWeight: 'bold' }}>Room</TableCell>
              {timeSlotHeaders.map(header => (
                <TableCell key={header.key} sx={{ minWidth: 150, fontSize: '0.75rem' }}>
                  <Box>{header.day}</Box>
                  <Box color="text.secondary">{header.time}</Box>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(roomMap).map(([roomKey, roomData]) => (
              <TableRow key={roomKey}>
                <TableCell sx={{ fontWeight: 'medium' }}>{roomData.roomName}</TableCell>
                {timeSlotHeaders.map(header => {
                  const slot = roomData.slots[header.key];
                  return (
                    <TableCell key={header.key} sx={{ minHeight: 80 }}>
                      {slot && (
                        <Box>
                          <Typography variant="caption" display="block" fontWeight="bold">
                            {slot.class_name || `Class ${slot.class_id}`}
                          </Typography>
                          <Chip
                            label={slot.teacher_name || `Teacher ${slot.teacher_id}`}
                            size="small"
                            sx={{ fontSize: '0.7rem', height: 20 }}
                          />
                        </Box>
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2 }}>
      <Typography variant="h5" gutterBottom>
        Timetable for Centre {id}
      </Typography>
      {timetableData?.draft && (
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Draft Status: {timetableData.draft.status} |
          Total Slots: {timetableData.draft.total_slots} |
          Unassigned: {timetableData.draft.total_unassigned}
        </Typography>
      )}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        isMobile ? renderMobileList() : renderDesktopTable()
      )}
    </Container>
  );
}