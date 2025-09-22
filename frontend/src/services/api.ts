const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface Facility {
  id: number;
  name: string;
  type: 'UPA' | 'UBS' | 'HOSPITAL';
  address: string;
  lat: number;
  lng: number;
  phone: string;
  is_24h: boolean;
  shifts_today: Shift[];
  distance_km: number;
  open_now: boolean;
}

export interface Shift {
  id: number;
  specialty_name: string;
  doctor_name: string;
  start_time: string;
  end_time: string;
}

export interface TriageSubmission {
  facility_id: number;
  complaint: string;
  discriminators: Record<string, boolean>;
}

export interface TriageResult {
  uuid: string;
  color: 'RED' | 'ORANGE' | 'YELLOW' | 'GREEN' | 'BLUE';
  priority: number;
  recommendation: string;
  position: number;
}

class ApiService {
  async getFacilities(): Promise<Facility[]> {
    const res = await fetch(`${API_URL}/facilities/`);
    if (!res.ok) throw new Error('Erro ao buscar unidades');
    const data = await res.json();
    return data.results || data;
  }

  async getWeekSchedule(facilityId: number): Promise<Shift[]> {
    const res = await fetch(`${API_URL}/facilities/${facilityId}/week_schedule/`);
    if (!res.ok) throw new Error('Erro ao buscar agenda');
    return res.json();
  }

  async submitTriage(data: TriageSubmission): Promise<TriageResult> {
    const res = await fetch(`${API_URL}/triage/submit/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Erro na triagem');
    return res.json();
  }

  async getTriageQueue(facilityId: number): Promise<any[]> {
    const res = await fetch(`${API_URL}/triage/?facility=${facilityId}&pending=true`);
    if (!res.ok) throw new Error('Erro ao buscar fila');
    const data = await res.json();
    return data.results || data;
  }
}

export default new ApiService();