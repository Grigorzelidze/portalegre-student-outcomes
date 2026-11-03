-- These limits belong to the pinned UCI file (data/SHA256SUMS), not to every future extract.
CREATE OR REPLACE FUNCTION qa.assert_all()
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    got integer;
    bad integer;
BEGIN
    SELECT count(*) INTO got FROM raw.student;
    IF got <> 4424 THEN
        RAISE EXCEPTION 'check:rowcount raw %', got;
    END IF;

    SELECT count(*) INTO got FROM clean.student;
    IF got <> 4424 THEN
        RAISE EXCEPTION 'check:rowcount clean %', got;
    END IF;

    SELECT count(*) INTO bad
    FROM clean.student
    WHERE target NOT IN ('Graduate', 'Dropout', 'Enrolled');
    IF bad <> 0 THEN
        RAISE EXCEPTION 'check:target %', bad;
    END IF;

    SELECT count(DISTINCT target) INTO got FROM clean.student;
    IF got <> 3 THEN
        RAISE EXCEPTION 'check:target_cardinality %', got;
    END IF;

    SELECT count(DISTINCT course) INTO got FROM clean.student;
    IF got <> 17 THEN
        RAISE EXCEPTION 'check:course_cardinality %', got;
    END IF;

    SELECT count(*) INTO bad
    FROM clean.student
    WHERE daytime_evening NOT IN (0, 1)
       OR displaced NOT IN (0, 1)
       OR special_needs NOT IN (0, 1)
       OR debtor NOT IN (0, 1)
       OR tuition_up_to_date NOT IN (0, 1)
       OR gender NOT IN (0, 1)
       OR scholarship NOT IN (0, 1)
       OR international NOT IN (0, 1);
    IF bad <> 0 THEN
        RAISE EXCEPTION 'check:flags %', bad;
    END IF;

    SELECT count(*) INTO bad
    FROM clean.student
    WHERE sem1_approved > sem1_enrolled
       OR sem2_approved > sem2_enrolled
       OR sem1_credited > sem1_enrolled
       OR sem2_credited > sem2_enrolled;
    IF bad <> 0 THEN
        RAISE EXCEPTION 'check:approved_vs_enrolled %', bad;
    END IF;

    SELECT count(*) INTO bad
    FROM clean.student
    WHERE sem1_grade < 0 OR sem1_grade > 20
       OR sem2_grade < 0 OR sem2_grade > 20;
    IF bad <> 0 THEN
        RAISE EXCEPTION 'check:grade_range %', bad;
    END IF;

    IF (SELECT n_graduate + n_dropout + n_enrolled FROM mart.headline)
        <> (SELECT n FROM mart.headline) THEN
        RAISE EXCEPTION 'check:headline_sum';
    END IF;

    IF (SELECT n_graduate + n_dropout FROM mart.headline)
        <> (SELECT n_resolved FROM mart.headline) THEN
        RAISE EXCEPTION 'check:resolved_sum';
    END IF;

    IF (SELECT n FROM mart.headline) <> 4424 THEN
        RAISE EXCEPTION 'check:headline_n';
    END IF;
END;
$$;

SELECT qa.assert_all();
