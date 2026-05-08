import client from './client';

export async function fetchTeachers(params = {}) {
  const res = await client.get('/teachers', { params: { role: 'academic_manager', ...params } });
  return res.data;
}

export async function fetchTeacher(id, role = 'academic_manager') {
  const res = await client.get(`/teachers/${id}`, { params: { role } });
  return res.data;
}

export async function createTeacher(data) {
  const res = await client.post('/teachers', data, { params: { role: 'hr' } });
  return res.data;
}

export async function updateTeacher(id, data) {
  const res = await client.put(`/teachers/${id}`, data, { params: { role: 'hr' } });
  return res.data;
}

export async function deleteTeacher(id) {
  await client.delete(`/teachers/${id}`);
}

export async function fetchAvailability(teacherId) {
  const res = await client.get(`/teachers/${teacherId}/availability`);
  return res.data;
}

export async function bulkSetAvailability(teacherId, slots) {
  const res = await client.post(`/teachers/${teacherId}/availability/bulk`, { teacher_id: teacherId, slots });
  return res.data;
}

export async function fetchLeaves(teacherId) {
  const res = await client.get(`/teachers/${teacherId}/leaves`);
  return res.data;
}

export async function createLeave(teacherId, data) {
  const res = await client.post(`/teachers/${teacherId}/leaves`, { ...data, teacher_id: teacherId });
  return res.data;
}