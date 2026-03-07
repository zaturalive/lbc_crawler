-- Migration: add user_id to IA tables
-- Run with:
--   docker exec fmc-db-dev mariadb -u fmc -pdevpassword find_my_car < backend/migrations/add_user_id_to_ia_tables.sql

ALTER TABLE requete_ia ADD COLUMN IF NOT EXISTS user_id INT DEFAULT 1;
ALTER TABLE analyse_recherche ADD COLUMN IF NOT EXISTS user_id INT DEFAULT 1;
