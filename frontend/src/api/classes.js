import client from './client';

export async function fetchClasses(params = {}) {
  const res = await client.get('/classes', { params });
  return res.data;
}

export async function fetchClass(id) {
  const res = await client.get(`/classes/${id}`);
  return res.data;
}

export async function createClass(data) {
  const res = await client.post('/classes', data);
  return res.data;
}

export async function updateClass(id, data) {
  const res = await client.put(`/classes/${id}`, data);
  return res.data;
}

export async function deleteClass(id) {
  await client.delete(`/classes/${id}`);
}

export async function validateRoomBooking(roomId, dayOfWeek, startTime, endTime) {
  const res = await client.get('/classes/validate/room-booking', {
    params: { room_id: roomId, day_of_week: dayOfWeek, start_time: startTime, end_time: endTime },
  });
  return res.data;
}