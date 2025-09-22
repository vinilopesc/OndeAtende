// frontend/src/types/index.ts

export interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'ADMIN' | 'DOCTOR' | 'TRIAGE_NURSE' | 'NURSE' | 'COORDINATOR' | 'RECEPTIONIST'
  facility?: Facility
  permissions: string[]
}

export interface Facility {
  id: string
  name: string
  facility_type: 'UPA' | 'UBS' | 'HOSPITAL' | 'PS'
  address: string
  city: string
  state: string
  latitude: number
  longitude: number
  phone_primary: string
  phone_emergency?: string
  is_24h: boolean
  opening_time?: string
  closing_time?: string
  is_accepting_emergencies: boolean
  is_accepting_walkins: boolean
  current_occupancy_percent: number
  resources: string[]
  specialties: string[]
  distance_km?: number
  is_open?: boolean
}

export interface MedicalShift {
  id: string
  specialty_name: string
  doctor_name: string
  shift_date: string
  start_time: string
  end_time: string
  is_on_call: boolean
  max_appointments: number
  current_appointments: number
  status: 'SCHEDULED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED'
  is_available: boolean
}

export interface Patient {
  id: string
  first_name: string
  last_name: string
  full_name: string
  birth_date: string
  gender: 'M' | 'F' | 'O'
  age: number
  age_months: number
  blood_type?: string
  allergies?: string[]
  chronic_conditions?: string[]
  current_medications?: string[]
}

export interface TriageSession {
  id: string
  session_uuid: string
  patient: Patient
  facility: Facility
  arrival_time: string
  chief_complaint: string
  complaint_description: string
  symptom_duration_hours?: number
  pain_scale?: number
  manchester_flowchart: string
  discriminators_answered: Record<string, boolean>
  vital_signs?: VitalSigns
  priority_color: 'RED' | 'ORANGE' | 'YELLOW' | 'GREEN' | 'BLUE'
  priority_level: number
  priority_reason: string
  status: 'ARRIVAL' | 'TRIAGE' | 'WAITING' | 'IN_CARE' | 'OBSERVATION' | 'DISCHARGED' | 'TRANSFERRED' | 'LEFT'
  queue_position?: number
  estimated_wait_minutes?: number
  recommendations: string[]
}

export interface VitalSigns {
  blood_pressure_systolic?: number
  blood_pressure_diastolic?: number
  heart_rate?: number
  respiratory_rate?: number
  temperature?: number
  spo2?: number
  glucose?: number
  gcs?: number
  pain_scale?: number
}

export interface MedicalSpecialty {
  id: string
  code: string
  name: string
  description: string
  requires_emergency: boolean
}

export interface TriageResult {
  priority: 'RED' | 'ORANGE' | 'YELLOW' | 'GREEN' | 'BLUE'
  label: string
  wait: string
  message: string
  timestamp: string
  recommended_facilities?: RecommendedFacility[]
}

export interface RecommendedFacility {
  facility: Facility
  score: number
  distance_km?: number
  estimated_wait_minutes: number
  occupancy_percent: number
  has_specialty: boolean
  recommendation: string
  route_url?: string
}

export interface QueueStatus {
  queues: {
    RED: TriageSession[]
    ORANGE: TriageSession[]
    YELLOW: TriageSession[]
    GREEN: TriageSession[]
    BLUE: TriageSession[]
  }
  statistics: {
    total_waiting: number
    critical_count: number
    average_wait_time: number
    last_update: string
  }
}