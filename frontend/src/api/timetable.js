import client from './client';

export async function fetchCentreDraft(centreId) {
  const res = await client.get(`/timetable/drafts/${centreId}`);
  return res.data;
}

export async function generateDraft(centreId, weekStart, weekEnd, createdBy = 'academic_manager') {
  const res = await client.post('/timetable/generate-draft', {
    centre_id: centreId,
    week_start: weekStart,
    week_end: weekEnd,
    created_by: createdBy,
  }, { params: { role: 'academic_manager' } });
  return res.data;
}

export async function publishDraft(draftId) {
  const res = await client.post(`/timetable/publish/${draftId}`, null, {
    params: { role: 'academic_manager' },
  });
  return res.data;
}