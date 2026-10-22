-- ============================================================================
-- queries.sql — Museum Artifact Explorer
-- 14+ Relational SQL Queries demonstrating DBMS Concepts:
-- INNER/LEFT JOINs, GROUP BY + HAVING, Aggregates, Subqueries, EXISTS,
-- Views, Many-to-Many M:N Associations, and Trigger Auditing.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. INNER JOIN: Retrieve artifacts with their civilization and category names
-- ----------------------------------------------------------------------------
SELECT 
    a.id,
    a.name AS artifact_name,
    a.period,
    c.name AS civilization_name,
    c.region,
    cat.name AS category_name
FROM artifacts a
JOIN civilizations c ON a.civilization_id = c.id
JOIN categories cat ON a.category_id = cat.id
ORDER BY a.name ASC;

-- ----------------------------------------------------------------------------
-- 2. LEFT JOIN: List all civilizations with their artifact counts
-- ----------------------------------------------------------------------------
SELECT 
    c.id,
    c.name AS civilization,
    c.region,
    COUNT(a.id) AS total_artifacts
FROM civilizations c
LEFT JOIN artifacts a ON a.civilization_id = c.id
GROUP BY c.id, c.name, c.region
ORDER BY total_artifacts DESC, c.name ASC;

-- ----------------------------------------------------------------------------
-- 3. LEFT JOIN: Artifacts with user favorite status
-- ----------------------------------------------------------------------------
SELECT 
    a.id,
    a.name AS artifact_name,
    a.material,
    CASE WHEN f.id IS NOT NULL THEN 'Favorited' ELSE 'Not Favorited' END AS favorite_status,
    f.created_at AS favorited_at
FROM artifacts a
LEFT JOIN favorites f ON f.artifact_id = a.id
ORDER BY a.id ASC;

-- ----------------------------------------------------------------------------
-- 4. GROUP BY + HAVING: Categories having more than 1 artifact
-- ----------------------------------------------------------------------------
SELECT 
    cat.id,
    cat.name AS category_name,
    COUNT(a.id) AS artifact_count
FROM categories cat
JOIN artifacts a ON a.category_id = cat.id
GROUP BY cat.id, cat.name
HAVING COUNT(a.id) > 1
ORDER BY artifact_count DESC;

-- ----------------------------------------------------------------------------
-- 5. GROUP BY + HAVING: Curators managing exhibitions with more than 2 artifacts
-- ----------------------------------------------------------------------------
SELECT 
    c.name AS curator_name,
    c.email,
    e.title AS exhibition_title,
    COUNT(ea.artifact_id) AS total_artifacts
FROM curators c
JOIN exhibitions e ON e.curator_id = c.id
JOIN exhibition_artifacts ea ON ea.exhibition_id = e.id
GROUP BY c.id, e.id
HAVING COUNT(ea.artifact_id) > 2
ORDER BY total_artifacts DESC;

-- ----------------------------------------------------------------------------
-- 6. Aggregate Functions: Global discovery year statistics (AVG, MIN, MAX, COUNT)
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(discovery_year) AS dated_artifacts_count,
    ROUND(AVG(discovery_year), 1) AS avg_discovery_year,
    MIN(discovery_year) AS earliest_discovery_year,
    MAX(discovery_year) AS latest_discovery_year
FROM artifacts
WHERE discovery_year IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 7. Aggregation by Group: Discovery statistics per civilization
-- ----------------------------------------------------------------------------
SELECT 
    c.name AS civilization,
    COUNT(a.id) AS artifact_count,
    MIN(a.discovery_year) AS first_excavated_year,
    MAX(a.discovery_year) AS last_excavated_year,
    GROUP_CONCAT(DISTINCT a.material) AS materials_used
FROM civilizations c
JOIN artifacts a ON a.civilization_id = c.id
GROUP BY c.id, c.name
ORDER BY artifact_count DESC;

-- ----------------------------------------------------------------------------
-- 8. Subquery (Scalar / Filter): Artifacts discovered before the average discovery year
-- ----------------------------------------------------------------------------
SELECT 
    id,
    name,
    discovery_year,
    discovery_location
FROM artifacts
WHERE discovery_year IS NOT NULL 
  AND discovery_year < (SELECT AVG(discovery_year) FROM artifacts WHERE discovery_year IS NOT NULL)
ORDER BY discovery_year ASC;

-- ----------------------------------------------------------------------------
-- 9. Subquery with IN: Civilizations that have artifacts in the 'Sculpture' category
-- ----------------------------------------------------------------------------
SELECT 
    id,
    name,
    region,
    period
FROM civilizations
WHERE id IN (
    SELECT DISTINCT a.civilization_id
    FROM artifacts a
    JOIN categories cat ON a.category_id = cat.id
    WHERE cat.name = 'Sculpture'
)
ORDER BY name ASC;

-- ----------------------------------------------------------------------------
-- 10. Correlated Subquery with EXISTS: Curators currently assigned to an exhibition
-- ----------------------------------------------------------------------------
SELECT 
    c.id,
    c.name,
    c.email,
    c.specialization
FROM curators c
WHERE EXISTS (
    SELECT 1 
    FROM exhibitions e 
    WHERE e.curator_id = c.id
)
ORDER BY c.name ASC;

-- ----------------------------------------------------------------------------
-- 11. Correlated Subquery with NOT EXISTS: Artifacts that are not in favorites
-- ----------------------------------------------------------------------------
SELECT 
    a.id,
    a.name,
    a.period,
    a.material
FROM artifacts a
WHERE NOT EXISTS (
    SELECT 1 
    FROM favorites f 
    WHERE f.artifact_id = a.id
)
ORDER BY a.name ASC;

-- ----------------------------------------------------------------------------
-- 12. View Usage: Querying the artifact_details view with filtering & sorting
-- ----------------------------------------------------------------------------
SELECT 
    id,
    name,
    civilization,
    category,
    period,
    material,
    discovery_location
FROM artifact_details
WHERE region LIKE '%Mediterranean%' OR civilization = 'Indus Valley'
ORDER BY civilization ASC, name ASC;

-- ----------------------------------------------------------------------------
-- 13. Many-to-Many M:N JOIN: Exhibitions, Curators, and Linked Artifacts
-- ----------------------------------------------------------------------------
SELECT 
    e.title AS exhibition_title,
    e.start_date,
    e.end_date,
    c.name AS curator,
    a.name AS artifact_name,
    a.material,
    civ.name AS civilization
FROM exhibitions e
JOIN curators c ON e.curator_id = c.id
JOIN exhibition_artifacts ea ON ea.exhibition_id = e.id
JOIN artifacts a ON ea.artifact_id = a.id
JOIN civilizations civ ON a.civilization_id = civ.id
ORDER BY e.start_date ASC, a.name ASC;

-- ----------------------------------------------------------------------------
-- 14. Trigger Demonstration: Auditing artifact deletions in deleted_artifacts_log
-- ----------------------------------------------------------------------------
-- Step A: Insert a temporary sample artifact
INSERT INTO artifacts (
    name, description, period, discovery_location, discovery_year,
    material, image_url, civilization_id, category_id
) VALUES (
    'Audit Trail Test Artifact',
    'Temporary artifact created specifically to verify the deletion trigger.',
    'Modern Era',
    'Test Excavation Trench 4',
    2024,
    'Bronze & Clay',
    'https://example.com/test.jpg',
    1,
    1
);

-- Step B: Delete the temporary artifact (this automatically fires trg_artifact_deleted)
DELETE FROM artifacts WHERE name = 'Audit Trail Test Artifact';

-- Step C: Verify the trigger audit log entry
SELECT 
    id,
    artifact_id,
    name,
    deleted_at
FROM deleted_artifacts_log
ORDER BY id DESC
LIMIT 5;
