CREATE VIEW mart.headline AS
SELECT
    count(*)::integer AS n,
    count(*) FILTER (WHERE target = 'Graduate')::integer AS n_graduate,
    count(*) FILTER (WHERE target = 'Dropout')::integer AS n_dropout,
    count(*) FILTER (WHERE target = 'Enrolled')::integer AS n_enrolled,
    count(*) FILTER (WHERE target IN ('Graduate', 'Dropout'))::integer AS n_resolved
FROM clean.student;

CREATE VIEW mart.by_tuition AS
SELECT
    tuition_up_to_date::text AS level,
    count(*)::integer AS n,
    count(*) FILTER (WHERE target IN ('Graduate', 'Dropout'))::integer AS n_resolved,
    count(*) FILTER (WHERE target = 'Graduate')::integer AS n_graduate,
    count(*) FILTER (WHERE target = 'Dropout')::integer AS n_dropout
FROM clean.student
GROUP BY tuition_up_to_date;

CREATE VIEW mart.by_scholarship AS
SELECT
    scholarship::text AS level,
    count(*)::integer AS n,
    count(*) FILTER (WHERE target IN ('Graduate', 'Dropout'))::integer AS n_resolved,
    count(*) FILTER (WHERE target = 'Graduate')::integer AS n_graduate,
    count(*) FILTER (WHERE target = 'Dropout')::integer AS n_dropout
FROM clean.student
GROUP BY scholarship;

-- Bands are duplicated on purpose in checks/recompute.py.
CREATE VIEW mart.by_age_scholarship AS
SELECT
    CASE
        WHEN age_at_enrollment <= 20 THEN '<=20'
        WHEN age_at_enrollment <= 23 THEN '21-23'
        WHEN age_at_enrollment <= 26 THEN '24-26'
        ELSE '27+'
    END AS age_band,
    scholarship::text AS scholarship,
    count(*) FILTER (WHERE target IN ('Graduate', 'Dropout'))::integer AS n_resolved,
    count(*) FILTER (WHERE target = 'Graduate')::integer AS n_graduate
FROM clean.student
GROUP BY 1, 2;

CREATE VIEW mart.sem1 AS
SELECT grp, n_resolved, n_graduate, n_dropout
FROM (
    SELECT
        'zero'::text AS grp,
        count(*)::integer AS n_resolved,
        count(*) FILTER (WHERE target = 'Graduate')::integer AS n_graduate,
        count(*) FILTER (WHERE target = 'Dropout')::integer AS n_dropout
    FROM clean.student
    WHERE target IN ('Graduate', 'Dropout')
      AND sem1_enrolled > 0
      AND sem1_approved = 0
    UNION ALL
    SELECT
        'some'::text,
        count(*)::integer,
        count(*) FILTER (WHERE target = 'Graduate')::integer,
        count(*) FILTER (WHERE target = 'Dropout')::integer
    FROM clean.student
    WHERE target IN ('Graduate', 'Dropout')
      AND sem1_enrolled > 0
      AND sem1_approved > 0
) s;

CREATE VIEW mart.sem1_not_enrolled AS
SELECT count(*)::integer AS n
FROM clean.student
WHERE sem1_enrolled = 0;

CREATE VIEW mart.by_course AS
SELECT
    course::text AS course,
    count(*)::integer AS n,
    count(*) FILTER (WHERE target IN ('Graduate', 'Dropout'))::integer AS n_resolved,
    count(*) FILTER (WHERE target = 'Graduate')::integer AS n_graduate,
    count(*) FILTER (WHERE target = 'Dropout')::integer AS n_dropout
FROM clean.student
GROUP BY course;

CREATE VIEW mart.admission AS
SELECT
    scholarship::text AS scholarship,
    avg(admission_grade)::float8 AS mean_grade,
    count(*)::integer AS n
FROM clean.student
GROUP BY scholarship;
