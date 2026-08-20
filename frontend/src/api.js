const BASE_URL = 'http://localhost:5000';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, opts);
  const data = await res.json();

  if (!res.ok) {
    const err = new Error(data.error || `Request failed (${res.status})`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  // Students
  createStudent: (body) => request('POST', '/students', body),

  // Outpasses
  createOutpass: (body) => request('POST', '/outpasses', body),
  getStudentOutpasses: (studentId) => request('GET', `/outpasses/student/${studentId}`),
  getPendingOutpasses: (hostelId) => request('GET', `/outpasses/pending/${hostelId}`),
  approveOutpass: (outpassId, wardenId, remark) =>
    request('POST', `/outpasses/${outpassId}/approve`, { warden_id: wardenId, remark }),
  rejectOutpass: (outpassId, wardenId, remark) =>
    request('POST', `/outpasses/${outpassId}/reject`, { warden_id: wardenId, remark }),

  // Gate Log
  logExit: (outpassId, staffId) =>
    request('POST', `/gatelog/${outpassId}/exit`, { staff_id: staffId }),
  logReturn: (outpassId, staffId) =>
    request('POST', `/gatelog/${outpassId}/return`, { staff_id: staffId }),

  // Reports
  getOverdueReport: (hostelId) => request('GET', `/reports/overdue/${hostelId}`),
};
