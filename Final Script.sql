/*
===================================================================================
Project: HR Intelligent System (Data Warehouse Phase)
Database: HR_DW
Structure: 4 Dimensions | 1 Fact Table
Logic: Staging -> Truncate & Load | Fact/Dim -> MERGE (Upsert)
===================================================================================
*/

-- ===================================================================================
-- Step 1: Create the Database
-- ===================================================================================
USE master;
GO

IF DB_ID('HR_DW') IS NOT NULL
BEGIN
    ALTER DATABASE HR_DW SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE HR_DW;
END
GO

CREATE DATABASE HR_DW;
GO

USE HR_DW;
GO

-- ===================================================================================
-- Step 2: Create the Staging Table (Landing Zone)
-- ===================================================================================
DROP TABLE IF EXISTS Staging_HR_Data;
CREATE TABLE Staging_HR_Data (
    Employee_ID INT,
    FirstName VARCHAR(100),
    LastName VARCHAR(100),
    StartDate DATE,
    ExitDate DATE,
    Title VARCHAR(100),
    Supervisor VARCHAR(100),
    ADEmail VARCHAR(150),
    BusinessUnit VARCHAR(50),
    EmployeeStatus VARCHAR(50),
    EmployeeType VARCHAR(50),
    PayZone VARCHAR(50),
    EmployeeClassificationType VARCHAR(100),
    TerminationType VARCHAR(100),
    TerminationDescription VARCHAR(MAX),
    DepartmentType VARCHAR(100),
    Division VARCHAR(100),
    DOB DATE,
    State VARCHAR(50),
    JobFunctionDescription VARCHAR(MAX),
    GenderCode VARCHAR(20),
    LocationCode INT,
    RaceDesc VARCHAR(50),
    MaritalDesc VARCHAR(50),
    Performance_Score VARCHAR(50),
    Current_Employee_Rating INT,
    Survey_Date DATE,
    Engagement_Score INT,
    Satisfaction_Score INT,
    Work_Life_Balance_Score INT,
    Training_Date DATE,
    Training_Program_Name VARCHAR(200),
    Training_Type VARCHAR(50),
    Training_Outcome VARCHAR(50),
    Location VARCHAR(100),
    Trainer VARCHAR(100),
    Training_Duration_Days INT,
    Training_Cost DECIMAL(12,2)
);
GO

-- ===================================================================================
-- Step 3: Create Dimension Tables (The 4 Dimensions)
-- ===================================================================================

-- 3.1 Dim_Employee (Added Supervisor)
DROP TABLE IF EXISTS Dim_Employee;
CREATE TABLE Dim_Employee (
    EmployeeKey INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT UNIQUE,
    FullName VARCHAR(200),
    Age INT,
    Gender VARCHAR(20),
    Race VARCHAR(50),
    MaritalStatus VARCHAR(50),
    Supervisor VARCHAR(100),
    Email VARCHAR(150)
);

-- 3.2 Dim_Job (Added JobFunctionDescription)
DROP TABLE IF EXISTS Dim_Job;
CREATE TABLE Dim_Job (
    JobKey INT IDENTITY(1,1) PRIMARY KEY,
    Title VARCHAR(100),
    Department VARCHAR(100),
    BusinessUnit VARCHAR(50),
    Division VARCHAR(100),
    JobFunctionDescription VARCHAR(MAX)
);

-- 3.3 Dim_Location 
DROP TABLE IF EXISTS Dim_Location;
CREATE TABLE Dim_Location (
    LocationKey INT IDENTITY(1,1) PRIMARY KEY,
    LocationCode INT UNIQUE,
    State VARCHAR(50),
    City VARCHAR(100)
);

-- 3.4 Dim_Training 
DROP TABLE IF EXISTS Dim_Training;
CREATE TABLE Dim_Training (
    TrainingKey INT IDENTITY(1,1) PRIMARY KEY,
    ProgramName VARCHAR(200),
    TrainingType VARCHAR(50),
    TrainerName VARCHAR(100)
);
GO

-- ===================================================================================
-- Step 4: Insert "Unknown" Members for Data Quality
-- ===================================================================================

-- Unknown Employee
INSERT INTO Dim_Employee (EmployeeID, FullName, Age, Gender, Race, MaritalStatus, Supervisor, Email)
VALUES (-1, 'Unknown Employee', -1, 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'Unknown');

-- Unknown Job
SET IDENTITY_INSERT Dim_Job ON;
INSERT INTO Dim_Job (JobKey, Title, Department, BusinessUnit, Division, JobFunctionDescription)
VALUES (-1, 'Unknown Title', 'Unknown Dept', 'Unknown BU', 'Unknown Div', 'Unknown Description');
SET IDENTITY_INSERT Dim_Job OFF;

-- Unknown Location
SET IDENTITY_INSERT Dim_Location ON;
INSERT INTO Dim_Location (LocationKey, LocationCode, State, City)
VALUES (-1, -1, 'Unknown State', 'Unknown City');
SET IDENTITY_INSERT Dim_Location OFF;

-- Unknown Training
SET IDENTITY_INSERT Dim_Training ON;
INSERT INTO Dim_Training (TrainingKey, ProgramName, TrainingType, TrainerName)
VALUES (-1, 'No Training', 'N/A', 'N/A');
SET IDENTITY_INSERT Dim_Training OFF;
GO

-- ===================================================================================
-- Step 5: Create the Fact Table
-- ===================================================================================
DROP TABLE IF EXISTS Fact_HR;
CREATE TABLE Fact_HR (
    FactKey INT IDENTITY(1,1) PRIMARY KEY,
    EmployeeID INT, 
    
    -- Foreign Keys
    EmployeeKey INT,
    JobKey INT,
    LocationKey INT,
    TrainingKey INT,
    
    -- Dates
    StartDate DATE,
    ExitDate DATE,
    SurveyDate DATE,
    TrainingDate DATE,
    
    -- Employment & Classification Details
    EmployeeStatus VARCHAR(50),
    EmployeeType VARCHAR(50),
    EmployeeClassificationType VARCHAR(100),
    PayZone VARCHAR(50), 
    
    -- Termination Details
    AttritionFlag INT, 
    TerminationType VARCHAR(100),
    TerminationDescription VARCHAR(MAX),
    
    TenureDays AS (
        DATEDIFF(day, StartDate, ISNULL(ExitDate, GETDATE()))
    ),    
    
    -- KPIs, Scores & Training Details
    PerformanceScore VARCHAR(50),
    CurrentRating INT,
    EngagementScore INT,
    SatisfactionScore INT,
    WorkLifeBalanceScore INT,
    TrainingOutcome VARCHAR(50),
    TrainingDurationDays INT,
    TrainingCost DECIMAL(12,2),
    
    LastUpdateDate DATETIME DEFAULT GETDATE()
);
GO

-- ===================================================================================
-- Step 6: Create the Incremental ETL Stored Procedure
-- ===================================================================================
GO
CREATE OR ALTER PROCEDURE sp_LoadHRDataWarehouse
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 1. Sync Dim_Employee (Includes Supervisor)
        MERGE Dim_Employee AS Target
        USING (
            SELECT Employee_ID, 
                   MAX(FirstName) AS FirstName, MAX(LastName) AS LastName, 
                   MAX(DOB) AS DOB, MAX(GenderCode) AS GenderCode, 
                   MAX(RaceDesc) AS RaceDesc, MAX(MaritalDesc) AS MaritalDesc, 
                   MAX(Supervisor) AS Supervisor, MAX(ADEmail) AS ADEmail 
            FROM Staging_HR_Data 
            WHERE Employee_ID IS NOT NULL
            GROUP BY Employee_ID
        ) AS Source
        ON Target.EmployeeID = Source.Employee_ID
        WHEN MATCHED THEN
            UPDATE SET 
                Target.FullName = CONCAT(Source.FirstName, ' ', Source.LastName),
                Target.Age = DATEDIFF(YEAR, Source.DOB, GETDATE()),
                Target.MaritalStatus = Source.MaritalDesc,
                Target.Supervisor = Source.Supervisor,
                Target.Email = Source.ADEmail
        WHEN NOT MATCHED THEN
            INSERT (EmployeeID, FullName, Age, Gender, Race, MaritalStatus, Supervisor, Email)
            VALUES (Source.Employee_ID, CONCAT(Source.FirstName, ' ', Source.LastName), 
                    DATEDIFF(YEAR, Source.DOB, GETDATE()), 
                    Source.GenderCode, Source.RaceDesc, Source.MaritalDesc, Source.Supervisor, Source.ADEmail);

        -- 2. Sync Dim_Job (Includes JobFunctionDescription)
        MERGE Dim_Job AS Target
        USING (
            SELECT Title, DepartmentType, 
                   MAX(BusinessUnit) AS BusinessUnit, MAX(Division) AS Division,
                   MAX(JobFunctionDescription) AS JobFunctionDescription
            FROM Staging_HR_Data 
            WHERE Title IS NOT NULL
            GROUP BY Title, DepartmentType
        ) AS Source
        ON Target.Title = Source.Title AND Target.Department = Source.DepartmentType
        WHEN MATCHED THEN
            UPDATE SET Target.JobFunctionDescription = Source.JobFunctionDescription
        WHEN NOT MATCHED THEN
            INSERT (Title, Department, BusinessUnit, Division, JobFunctionDescription)
            VALUES (Source.Title, Source.DepartmentType, Source.BusinessUnit, Source.Division, Source.JobFunctionDescription);

        -- 3. Sync Dim_Location
        MERGE Dim_Location AS Target
        USING (
            SELECT LocationCode, MAX(State) AS State, MAX(Location) AS Location 
            FROM Staging_HR_Data WHERE LocationCode IS NOT NULL GROUP BY LocationCode
        ) AS Source
        ON Target.LocationCode = Source.LocationCode
        WHEN NOT MATCHED THEN
            INSERT (LocationCode, State, City) VALUES (Source.LocationCode, Source.State, Source.Location);

        -- 4. Sync Dim_Training
        MERGE Dim_Training AS Target
        USING (
            SELECT Training_Program_Name, Trainer, MAX(Training_Type) AS Training_Type 
            FROM Staging_HR_Data WHERE Training_Program_Name IS NOT NULL GROUP BY Training_Program_Name, Trainer
        ) AS Source
        ON Target.ProgramName = Source.Training_Program_Name AND Target.TrainerName = Source.Trainer
        WHEN NOT MATCHED THEN
            INSERT (ProgramName, TrainingType, TrainerName) VALUES (Source.Training_Program_Name, Source.Training_Type, Source.Trainer);

        -- 5. Sync Fact_HR (Includes All Missing Columns)
        MERGE Fact_HR AS Target
        USING (
            SELECT 
                s.Employee_ID, e.EmployeeKey, j.JobKey, l.LocationKey, t.TrainingKey,
                s.StartDate, s.ExitDate, s.Survey_Date, s.Training_Date,
                s.EmployeeStatus, s.EmployeeType, s.EmployeeClassificationType, s.PayZone, 
                s.TerminationType, s.TerminationDescription,
                s.Performance_Score, s.Current_Employee_Rating, s.Engagement_Score, s.Satisfaction_Score,
                s.Work_Life_Balance_Score, s.Training_Outcome, s.Training_Duration_Days, s.Training_Cost,
                CASE WHEN s.EmployeeStatus = 'Active' THEN 0 ELSE 1 END AS AttritionFlag
            FROM Staging_HR_Data s
            LEFT JOIN Dim_Employee e ON s.Employee_ID = e.EmployeeID
            LEFT JOIN Dim_Job j ON s.Title = j.Title AND s.DepartmentType = j.Department
            LEFT JOIN Dim_Location l ON s.LocationCode = l.LocationCode
            LEFT JOIN Dim_Training t ON s.Training_Program_Name = t.ProgramName AND s.Trainer = t.TrainerName
        ) AS Source
        ON Target.EmployeeID = Source.Employee_ID
        
        WHEN MATCHED THEN
            UPDATE SET 
                Target.ExitDate = Source.ExitDate,
                Target.EmployeeStatus = Source.EmployeeStatus,
                Target.EmployeeClassificationType = Source.EmployeeClassificationType,
                Target.PayZone = Source.PayZone,
                Target.TerminationType = Source.TerminationType,
                Target.TerminationDescription = Source.TerminationDescription,
                Target.AttritionFlag = Source.AttritionFlag,
                Target.PerformanceScore = Source.Performance_Score,
                Target.CurrentRating = Source.Current_Employee_Rating,
                Target.SatisfactionScore = Source.Satisfaction_Score,
                Target.TrainingOutcome = Source.Training_Outcome,
                Target.LastUpdateDate = GETDATE()

        WHEN NOT MATCHED THEN
            INSERT (EmployeeID, EmployeeKey, JobKey, LocationKey, TrainingKey, 
                    StartDate, ExitDate, SurveyDate, TrainingDate, 
                    EmployeeStatus, EmployeeType, EmployeeClassificationType, PayZone, AttritionFlag, 
                    TerminationType, TerminationDescription,
                    PerformanceScore, CurrentRating, EngagementScore, SatisfactionScore, 
                    WorkLifeBalanceScore, TrainingOutcome, TrainingDurationDays, TrainingCost)
            VALUES (
                Source.Employee_ID, ISNULL(Source.EmployeeKey, -1), ISNULL(Source.JobKey, -1), ISNULL(Source.LocationKey, -1), ISNULL(Source.TrainingKey, -1),
                Source.StartDate, Source.ExitDate, Source.Survey_Date, Source.Training_Date, 
                Source.EmployeeStatus, Source.EmployeeType, Source.EmployeeClassificationType, Source.PayZone, Source.AttritionFlag,
                Source.TerminationType, Source.TerminationDescription,
                Source.Performance_Score, Source.Current_Employee_Rating, Source.Engagement_Score, Source.Satisfaction_Score, 
                Source.Work_Life_Balance_Score, Source.Training_Outcome, Source.Training_Duration_Days, Source.Training_Cost
            );

        COMMIT TRANSACTION;
        PRINT 'SUCCESS: HR_DW Star Schema Load Completed.';
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO