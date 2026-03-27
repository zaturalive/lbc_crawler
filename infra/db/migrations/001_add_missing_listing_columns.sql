-- Migration 001 — Colonnes manquantes dans listings
-- Appliquée le : 2026-03-08
-- Contexte : le modèle SQLAlchemy avait évolué (fuel_type, doors, seats,
--            color, images) mais la table listings créée par init.sql n'avait
--            pas été mise à jour.
-- Auteur   : généré via audit modèle vs DB

USE find_my_car;

-- ─── listings : colonnes manquantes ──────────────────────────────────────────
ALTER TABLE listings
  ADD COLUMN IF NOT EXISTS fuel_type  VARCHAR(50)  NULL AFTER gearbox,
  ADD COLUMN IF NOT EXISTS doors      INT          NULL AFTER fuel_type,
  ADD COLUMN IF NOT EXISTS seats      INT          NULL AFTER doors,
  ADD COLUMN IF NOT EXISTS color      VARCHAR(50)  NULL AFTER seats,
  ADD COLUMN IF NOT EXISTS images     JSON         NULL COMMENT 'Liste des URLs images LBC' AFTER matched_keywords;

-- ─── vehicles : colonnes manquantes (ajoutées manuellement avant cette migration)
-- Listées ici pour traçabilité — déjà présentes si la migration manuelle a été faite
ALTER TABLE vehicles
  ADD COLUMN IF NOT EXISTS reliability_rank  VARCHAR(20)  NULL AFTER total_testimonials,
  ADD COLUMN IF NOT EXISTS category          VARCHAR(50)  NULL AFTER scraped_at,
  ADD COLUMN IF NOT EXISTS rank_in_category  INT          NULL AFTER category,
  ADD COLUMN IF NOT EXISTS total_in_category INT          NULL AFTER rank_in_category;

-- ─── Vérification finale ──────────────────────────────────────────────────────
-- SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_SCHEMA='find_my_car' AND TABLE_NAME='listings'
-- ORDER BY ORDINAL_POSITION;
