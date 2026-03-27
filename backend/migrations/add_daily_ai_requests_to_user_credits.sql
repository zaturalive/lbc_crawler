-- Migration: add daily_ai_requests_used to user_credits
-- Tracks how many AI analysis requests a user has made today (resets daily at midnight UTC)
ALTER TABLE user_credits
    ADD COLUMN daily_ai_requests_used INT NOT NULL DEFAULT 0;
