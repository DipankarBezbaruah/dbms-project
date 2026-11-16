const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // send session cookies
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
  // Auth
  login: (email, password) => request('POST', '/auth/login', { email, password }),
  me: () => request('GET', '/auth/me'),
  logout: () => request('POST', '/auth/logout'),

  // Students
  createStudent: (body) => request('POST', '/students', body),

  // Outpasses
  createOutpass: (body) => request('POST', '/outpasses', body),
  getStudentOutpasses: (studentId) => request('GET', `/outpasses/student/${studentId}`),
  getPendingOutpasses: (hostelId) => request('GET', `/outpasses/pending/${hostelId}`),
  getMentorPending: (mentorId) => request('GET', `/outpasses/pending/mentor/${mentorId}`),
  getMentorAllOutpasses: (mentorId) => request('GET', `/outpasses/mentor/${mentorId}`),
  getDeptPending: (department) => request('GET', `/outpasses/pending/department/${encodeURIComponent(department)}`),
  getDeptAllOutpasses: (department) => request('GET', `/outpasses/department/${encodeURIComponent(department)}`),
  approveOutpass: (outpassId, userId, remark) =>
    request('POST', `/outpasses/${outpassId}/approve`, { user_id: userId, remark }),
  rejectOutpass: (outpassId, userId, remark) =>
    request('POST', `/outpasses/${outpassId}/reject`, { user_id: userId, remark }),

  // Gate Log
  logExit: (outpassId, staffId) =>
    request('POST', `/gatelog/${outpassId}/exit`, { staff_id: staffId }),
  logReturn: (outpassId, staffId) =>
    request('POST', `/gatelog/${outpassId}/return`, { staff_id: staffId }),

  // Admin
  registerStudent: (body) => request('POST', '/admin/register-student', body),
  registerStaff: (body) => request('POST', '/admin/register-staff', body),
  getHostels: () => request('GET', '/hostels'),
  getMentors: () => request('GET', '/mentors'),

  // Reports
  getOverdueReport: (hostelId) => request('GET', `/reports/overdue/${hostelId}`),
  getMentorOverdueReport: (mentorId) => request('GET', `/reports/overdue/mentor/${mentorId}`),
  getDeptOverdueReport: (department) => request('GET', `/reports/overdue/department/${encodeURIComponent(department)}`),
};
