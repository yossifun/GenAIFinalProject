/* --------  create_Tech_Schedules ----------------------------- */
USE master;

IF DB_ID(N'Tech') IS NOT NULL
BEGIN
    USE Tech;

    -- Drop tables if they exist
    IF OBJECT_ID('dbo.Interviews', 'U') IS NOT NULL
    DROP TABLE dbo.Interviews;

    IF OBJECT_ID('dbo.Schedules', 'U') IS NOT NULL
    DROP TABLE dbo.Schedules;

    -- Drop the database
    USE master;
    ALTER DATABASE Tech SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE Tech;
END



CREATE DATABASE Tech;
GO

USE Tech;
GO

CREATE TABLE dbo.Schedules
(
    ScheduleID INT IDENTITY(1,1) PRIMARY KEY,
    [date] DATE NOT NULL,
    [time] TIME(0) NOT NULL,
    position VARCHAR(20)NOT NULL,
    available BIT NOT NULL
);
GO

CREATE TABLE dbo.Interviews
(
    InterviewID INT IDENTITY(1,1) PRIMARY KEY,
    ScheduleID INT NOT NULL REFERENCES dbo.Schedules(ScheduleID),
    CandidatePhone VARCHAR(15) NOT NULL,
    RecruiterPhone VARCHAR(15) NOT NULL
);
GO

DECLARE @StartDate DATE = DATEFROMPARTS(YEAR(GETDATE()), 1, 1),
        @EndDate   DATE = DATEFROMPARTS(YEAR(GETDATE()), 12, 31);

;WITH
    -- Dates from start to end
    Dates
    AS
    (
                    SELECT @StartDate AS d
        UNION ALL
            SELECT DATEADD(DAY,1,d)
            FROM Dates
            WHERE  d < @EndDate
    ),
    -- Tue-Fri & Sun only
    ValidDates
    AS
    (
        SELECT d
        FROM Dates
        WHERE  DATENAME(WEEKDAY,d) NOT IN ('Saturday','Monday')
    ),
    -- Hours 09:00–17:00
    Times
    AS
    (
                    SELECT CAST('09:00' AS TIME) AS t
        UNION ALL
            SELECT DATEADD(HOUR,1,t)
            FROM Times
            WHERE  t < '17:00'
    ),

    -- CTE
    Positions
    AS
    (
                                    SELECT 'Python Developer' AS position
        UNION ALL
            SELECT 'SQL Developer'
        UNION ALL
            SELECT 'Business Analyst'
        UNION ALL
            SELECT 'ML Engineer'
    ),
    InsertSet
    AS
    (
        SELECT
            vd.d                      AS [date],
            tm.t                      AS [time],
            ps.position,
            /* pseudo-normal: N(0.5,≈0.13) then threshold 0.5 */
            CASE
            WHEN (ABS(CHECKSUM(NEWID())) % 100
                + ABS(CHECKSUM(NEWID())) % 100) / 200.0 >= 0.5
            THEN 1 ELSE 0
        END                       AS available
        FROM ValidDates vd
          CROSS JOIN Times     tm
          CROSS JOIN Positions ps
    )
INSERT INTO dbo.Schedules
    ([date],[time],position,available)
SELECT [date], [time], position, available
FROM InsertSet
OPTION
(MAXRECURSION
0);          -- allow full-year recursion
GO



/* optional sanity check */
SELECT *
FROM dbo.Schedules
ORDER BY ScheduleID;
GO