-- find_my_car — MariaDB initialization
-- Sprint 0 — E0-US4

CREATE DATABASE IF NOT EXISTS find_my_car CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE find_my_car;

-- Vehicle model data from fiches-auto.fr
CREATE TABLE IF NOT EXISTS vehicles (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    brand               VARCHAR(100) NOT NULL,
    model               VARCHAR(100) NOT NULL,
    year_start          INT,
    year_end            INT,
    reliability_score   TINYINT,
    common_issues       JSON,
    fuel_type           VARCHAR(50),
    scraped_at          DATETIME DEFAULT NOW(),
    INDEX idx_brand_model (brand, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- LBC listings
CREATE TABLE IF NOT EXISTS listings (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    lbc_id              VARCHAR(50) NOT NULL,
    title               VARCHAR(255),
    price               INT,
    year                INT,
    mileage             INT,
    horsepower          INT,
    gearbox             ENUM('manual', 'automatic'),
    location            VARCHAR(100),
    description         TEXT,
    url                 VARCHAR(500),
    matched_keywords    JSON,
    vehicle_id          INT,
    scraped_at          DATETIME DEFAULT NOW(),
    UNIQUE KEY uk_lbc_id (lbc_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL,
    INDEX idx_price (price),
    INDEX idx_year (year),
    INDEX idx_mileage (mileage),
    INDEX idx_scraped_at (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Pre-configured and user regex patterns
CREATE TABLE IF NOT EXISTS regex_patterns (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    pattern     VARCHAR(500) NOT NULL,
    description VARCHAR(255),
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  DATETIME DEFAULT NOW()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Search session history
CREATE TABLE IF NOT EXISTS search_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    filters         JSON,
    patterns        JSON,
    result_count    INT DEFAULT 0,
    created_at      DATETIME DEFAULT NOW()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Default regex patterns
INSERT INTO regex_patterns (name, pattern, description, is_default) VALUES
('CT valide',           '(?:\\bct\\b|\\bcontr[oô]le\\s+technique\\b)',        'Contrôle technique valide mentionné dans l''annonce',    TRUE),
('Carte grise',         '\\bcarte\\s+grise\\b',                               'Carte grise disponible ou mentionnée',                   TRUE),
('Premier propriétaire','\\bpremier\\s+propri[eé]taire\\b|\\b1[eè]re?\\s+main\\b', 'Véhicule vendu par son premier propriétaire',       TRUE),
('Carnet entretien',    '\\bcarnet\\s+d''?entretien\\b',                       'Carnet d''entretien présent',                            TRUE),
('Factures garage',     '\\bfacture[s]?\\s+(?:garage|entretien|réparation)\\b', 'Factures d''entretien disponibles',                  TRUE),
('Non fumeur',          '\\bnon[- ]fumeur\\b|\\bsans\\s+odeur\\b',            'Véhicule non-fumeur',                                    TRUE),
('Révision récente',    '\\br[eé]vision\\s+(?:r[eé]cente|faite|effectu[eé]e)\\b', 'Révision récente effectuée',                      TRUE);
