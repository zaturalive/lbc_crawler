# TASK-004 — Fix UNIQUE KEY vehicles (BUG-04)

**Status:** ✅ **OK**

**Date:** 2025-01-12  
**Component:** Infrastructure / Database Schema  
**Modified Files:** `infra/db/init.sql`

---

## Summary

Fixed the `vehicles` table in MariaDB to enforce unique constraints on `(brand, model)` pairs. Replaced non-unique `INDEX idx_brand_model` with `UNIQUE KEY uk_brand_model` to enable proper `ON DUPLICATE KEY UPDATE` functionality in scraper upserts.

---

## State Before Migration

### Database State (Live)
```
Index on vehicles table:
- Key_name: idx_brand_model
- Non_unique: YES (Non_unique = 1)
- Columns: (brand, model)
```

### Duplicates Check
```
Total vehicles: 1
Unique pairs: 1
Duplicates: 0
```

### init.sql State
```sql
INDEX idx_brand_model (brand, model)  -- Line 18
```

---

## Changes Applied

### 1. File Modification: `infra/db/init.sql`

**Before (Line 18):**
```sql
INDEX idx_brand_model (brand, model)
```

**After (Line 18):**
```sql
UNIQUE KEY uk_brand_model (brand, model)
```

---

### 2. Live Migration SQL

Executed on container `fmc-mariadb-dev`:

```sql
-- Remove any duplicate entries (keeps row with smallest id)
DELETE v1 FROM vehicles v1
INNER JOIN vehicles v2
WHERE v1.brand = v2.brand AND v1.model = v2.model AND v1.id > v2.id;

-- Replace non-unique index with unique key
ALTER TABLE vehicles DROP INDEX idx_brand_model;
ALTER TABLE vehicles ADD UNIQUE KEY uk_brand_model (brand, model);
```

---

## State After Migration

### Database Verification
```
Index on vehicles table:
- Key_name: uk_brand_model
- Non_unique: NO (Non_unique = 0)
- Columns: (brand, model)
- Type: BTREE
```

### Final Count
```
Total vehicles: 1
Unique pairs: 1
Duplicates removed: 0
```

---

## Impact

✅ **Positive Outcomes:**

1. **Duplicate Prevention:** Future scraper runs will properly handle duplicates via `ON DUPLICATE KEY UPDATE`
2. **Data Integrity:** Database now enforces that each `(brand, model)` pair is unique
3. **Schema Consistency:** `init.sql` now matches live database schema
4. **Zero Data Loss:** No vehicles were deleted (0 duplicates existed)

---

## Verification

All verification queries passed:

```bash
# Check UNIQUE KEY exists
docker exec fmc-mariadb-dev mariadb -u fmc -pdevpassword find_my_car -e \
  "SHOW INDEX FROM vehicles WHERE Key_name = 'uk_brand_model';"
# Result: ✅ Key_name uk_brand_model exists with Non_unique = 0

# Check final vehicle count
docker exec fmc-mariadb-dev mariadb -u fmc -pdevpassword find_my_car -e \
  "SELECT COUNT(*) as total_vehicles, COUNT(DISTINCT CONCAT(brand,'|',model)) as unique_pairs FROM vehicles;"
# Result: ✅ 1 vehicle, 1 unique pair, 0 duplicates
```

---

## Scraper Integration Impact

**fiches-auto.fr scraper** will now properly upsert vehicle data:

```python
INSERT INTO vehicles (...) VALUES (...)
ON DUPLICATE KEY UPDATE
    year_start = VALUES(year_start),
    year_end = VALUES(year_end),
    reliability_score = VALUES(reliability_score),
    ...
```

If a `(brand, model)` pair already exists:
- The existing row is updated with new data
- No duplicate rows are created

---

## Related Issues

- **BUG-04:** Duplicate vehicles after scraper sync
- **Context:** `/home/dimitry/Documents/Perso/Projets/find_my_car/_byan/_output/fmc/context/infra-context.md`

---

## Rollback (if needed)

If reverting to non-unique index is necessary:

```sql
ALTER TABLE vehicles DROP KEY uk_brand_model;
ALTER TABLE vehicles ADD INDEX idx_brand_model (brand, model);
```

And update `infra/db/init.sql` Line 18:
```sql
INDEX idx_brand_model (brand, model)
```

---

**Task Completed:** TASK-004-fix-unique-key-report.md  
**Migration Status:** ✅ SUCCESSFUL  
**Duplicates Removed:** 0  
**Total Vehicles After:** 1
