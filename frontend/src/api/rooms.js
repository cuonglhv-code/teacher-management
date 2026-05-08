import client from './client';

export async function fetchRooms(centreId) {
  const params = {};
  if (centreId) params.centre_id = centreId;
  const res = await client.get('/rooms', { params });
  return res.data;
}

export async function fetchRoom(id) {
  const res = await client.get(`/rooms/${id}`);
  return res.data;
}

export async function createRoom(data) {
  const res = await client.post('/rooms', data);
  return res.data;
}

export async function updateRoom(id, data) {
  const res = await client.put(`/rooms/${id}`, data);
  return res.data;
}

export async function deleteRoom(id) {
  await client.delete(`/rooms/${id}`);
}