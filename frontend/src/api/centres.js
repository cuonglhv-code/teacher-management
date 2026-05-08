import client from './client';

export async function fetchCentres() {
  const res = await client.get('/centres');
  return res.data;
}

export async function fetchCentre(id) {
  const res = await client.get(`/centres/${id}`);
  return res.data;
}