CREATE SCHEMA IF NOT EXISTS schedule;

-- Custom Types
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shift_status_type' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'schedule')) THEN
        CREATE TYPE schedule.shift_status_type AS ENUM ('working', 'off', 'leave', 'sick', 'vacation', 'training', 'business_trip', 'hourly');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'swap_status' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'schedule')) THEN
        CREATE TYPE schedule.swap_status AS ENUM ('pending', 'accepted', 'tl_approved', 'approved', 'rejected', 'cancelled');
    END IF;
END $$;

-- Read model for Employees (populated via events)
CREATE TABLE IF NOT EXISTS schedule.employees (
    id UUID PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department_id UUID,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shifts Table
CREATE TABLE IF NOT EXISTS schedule.shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL,
    name_en VARCHAR(50),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    color_code VARCHAR(7) DEFAULT '#3788d8',
    requires_vehicle BOOLEAN DEFAULT false,
    min_rest_hours INTEGER DEFAULT 8,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weekly Schedule Templates
CREATE TABLE IF NOT EXISTS schedule.schedule_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES schedule.employees(id) ON DELETE CASCADE,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
    shift_id UUID REFERENCES schedule.shifts(id) ON DELETE SET NULL,
    is_off BOOLEAN DEFAULT false,
    valid_from DATE,
    valid_to DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (employee_id, day_of_week, valid_from)
);

-- Published Weekly Schedules
CREATE TABLE IF NOT EXISTS schedule.weekly_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    template_id UUID REFERENCES schedule.schedule_templates(id),
    status VARCHAR(20) DEFAULT 'draft',
    published_by UUID REFERENCES schedule.employees(id),
    published_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES schedule.employees(id),
    UNIQUE (week_start_date)
);

-- Employee Shifts (Daily Assignments)
CREATE TABLE IF NOT EXISTS schedule.employee_shifts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES schedule.weekly_schedule(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES schedule.employees(id) ON DELETE CASCADE,
    shift_id UUID REFERENCES schedule.shifts(id) ON DELETE SET NULL,
    shift_date DATE NOT NULL,
    shift_status schedule.shift_status_type NOT NULL DEFAULT 'working',
    leave_reason TEXT,
    is_replacement BOOLEAN DEFAULT false,
    replaced_employee_id UUID REFERENCES schedule.employees(id),
    replacement_approved_by UUID REFERENCES schedule.employees(id),
    check_in_time TIMESTAMP,
    check_out_time TIMESTAMP,
    actual_worked_hours DECIMAL(4,2),
    overtime_hours DECIMAL(4,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES schedule.employees(id),
    UNIQUE (employee_id, shift_date)
);

-- Shift Swaps
CREATE TABLE IF NOT EXISTS schedule.shift_swaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID NOT NULL REFERENCES schedule.employees(id),
    target_employee_id UUID NOT NULL REFERENCES schedule.employees(id),
    shift_date DATE NOT NULL,
    shift_id UUID NOT NULL REFERENCES schedule.shifts(id),
    reason TEXT,
    status schedule.swap_status DEFAULT 'pending',
    approved_by_team_leader UUID REFERENCES schedule.employees(id),
    approved_by_manager UUID REFERENCES schedule.employees(id),
    approval_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shift Handovers
CREATE TABLE IF NOT EXISTS schedule.shift_handovers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shift_id UUID REFERENCES schedule.employee_shifts(id) ON DELETE CASCADE,
    department_id UUID,
    creator_id UUID REFERENCES schedule.employees(id),
    claimer_id UUID REFERENCES schedule.employees(id),
    status VARCHAR(20) DEFAULT 'pending',
    notes TEXT,
    claimer_notes TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schedule.shift_handover_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handover_id UUID REFERENCES schedule.shift_handovers(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES schedule.employees(id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
