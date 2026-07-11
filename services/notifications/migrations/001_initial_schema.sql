-- =====================================================
-- Initial Schema for Notifications Service
-- =====================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enums
CREATE TYPE notification_type AS ENUM ('shift_change', 'task_assigned', 'leave_request', 'approval', 'system_alert', 'reminder');
CREATE TYPE notification_priority AS ENUM ('low', 'medium', 'high');

-- =====================================================
-- Audit Logs Table
-- =====================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID, -- References Auth Service employee
    action VARCHAR(50) NOT NULL,  -- INSERT, UPDATE, DELETE
    table_name VARCHAR(50) NOT NULL,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_record ON audit_logs(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_employee ON audit_logs(employee_id);

-- =====================================================
-- Notifications Table
-- =====================================================
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_id UUID NOT NULL, -- References Auth Service employee
    sender_id UUID, -- References Auth Service employee
    type notification_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    related_entity_type VARCHAR(30),  -- schedule, task, leave, swap
    related_entity_id UUID,
    priority notification_priority DEFAULT 'medium',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    action_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient_id);

-- =====================================================
-- Daily Statistics Table
-- =====================================================
CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stat_date DATE UNIQUE NOT NULL,
    total_employees INTEGER,
    present_count INTEGER,
    absent_count INTEGER,
    leave_count INTEGER,
    vacation_count INTEGER,
    night_shift_count INTEGER,
    morning_shift_count INTEGER,
    evening_shift_count INTEGER,
    open_tasks_count INTEGER,
    completed_tasks_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- Announcements Table
-- =====================================================
CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL, -- References Auth Service department
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('info', 'normal', 'important', 'critical')),
    is_active BOOLEAN DEFAULT false,
    images TEXT[] DEFAULT '{}',
    is_ticker BOOLEAN DEFAULT false,
    created_by UUID, -- References Auth Service employee
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_announcements_department ON announcements(department_id);
CREATE INDEX IF NOT EXISTS idx_announcements_active ON announcements(is_active);

-- =====================================================
-- Push Subscriptions Table
-- =====================================================
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL, -- References Auth Service employee
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, endpoint)
);
