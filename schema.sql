CREATE TABLE patients (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  age INTEGER NOT NULL CHECK (age >= 0),
  gender VARCHAR(20) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  address VARCHAR(250)
);
CREATE TABLE doctors (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  specialization VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL
);
CREATE TABLE appointments (
  id SERIAL PRIMARY KEY,
  patient_id INTEGER NOT NULL REFERENCES patients(id),
  doctor_id INTEGER NOT NULL REFERENCES doctors(id),
  appointment_date DATE NOT NULL,
  appointment_time VARCHAR(10) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'Scheduled'
);
CREATE TABLE prescriptions (
  id SERIAL PRIMARY KEY,
  appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
  diagnosis TEXT NOT NULL,
  medicines TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE bills (
  id SERIAL PRIMARY KEY,
  appointment_id INTEGER NOT NULL UNIQUE REFERENCES appointments(id),
  amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
  payment_status VARCHAR(20) NOT NULL DEFAULT 'Unpaid',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
