-- ============================================================
-- HealthRisk AI — Seed Data
-- Run this in Supabase SQL Editor after schema creation
-- ============================================================

-- ── USERS (50 users across all roles) ────────────────────────
-- Password for ALL users: Pass@1234  (bcrypt hash below)
-- Change passwords after seeding!

INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified) VALUES
-- 3 Clinicians
('a1000001-0000-0000-0000-000000000001','dr.sarah.chen@hospital.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Dr. Sarah Chen','clinician',TRUE,TRUE),
('a1000001-0000-0000-0000-000000000002','dr.james.wilson@hospital.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Dr. James Wilson','clinician',TRUE,TRUE),
('a1000001-0000-0000-0000-000000000003','dr.priya.patel@medclinic.org','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Dr. Priya Patel','clinician',TRUE,TRUE),
-- 10 Researchers
('a1000002-0000-0000-0000-000000000001','research.john@university.edu','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','John Adams','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000002','research.emily@university.edu','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Emily Rodriguez','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000003','research.michael@medlab.org','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Michael Chang','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000004','research.anna@pharma.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Anna Kowalski','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000005','research.david@biotech.io','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','David Kim','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000006','research.sofia@medschool.edu','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Sofia Martinez','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000007','research.liam@genomics.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Liam Nguyen','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000008','research.aisha@who.int','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Aisha Okafor','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000009','research.marco@clinresearch.eu','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Marco Bianchi','researcher',TRUE,TRUE),
('a1000002-0000-0000-0000-000000000010','research.yuki@nii.ac.jp','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Yuki Tanaka','researcher',TRUE,TRUE)
ON CONFLICT (email) DO NOTHING;

-- 37 Read-Only users (patients / general public)
INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified) VALUES
('a1000003-0000-0000-0000-000000000001','patient.alice@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Alice Thompson','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000002','patient.bob@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Bob Henderson','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000003','patient.carol@outlook.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Carol Davis','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000004','patient.dan@yahoo.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Daniel Morrison','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000005','patient.eva@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Eva Johansson','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000006','patient.frank@hotmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Frank Müller','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000007','patient.grace@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Grace Liu','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000008','patient.henry@outlook.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Henry Osei','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000009','patient.iris@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Iris Nakamura','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000010','patient.jack@yahoo.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Jack Williams','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000011','patient.kate@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Kate Murphy','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000012','patient.leon@hotmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Leon Petrov','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000013','patient.mia@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Mia Santos','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000014','patient.noah@outlook.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Noah Park','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000015','patient.olivia@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Olivia Brown','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000016','patient.peter@yahoo.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Peter Ivanov','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000017','patient.quinn@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Quinn Adams','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000018','patient.rose@hotmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Rose Garcia','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000019','patient.sam@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Sam Turner','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000020','patient.tina@outlook.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Tina Zhao','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000021','patient.uma@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Uma Singh','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000022','patient.victor@yahoo.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Victor Almeida','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000023','patient.wendy@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Wendy Larson','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000024','patient.xander@hotmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Xander Fox','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000025','patient.yara@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Yara Hassan','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000026','patient.zack@outlook.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Zack Coleman','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000027','patient.anya@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Anya Volkov','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000028','patient.ben@yahoo.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Ben Okonkwo','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000029','patient.clara@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Clara Eriksson','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000030','patient.diego@hotmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Diego Reyes','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000031','patient.elena@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Elena Popescu','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000032','patient.finn@outlook.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Finn McAllister','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000033','patient.greta@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Greta Weber','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000034','patient.hiro@yahoo.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Hiro Yamamoto','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000035','patient.ida@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Ida Lindqvist','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000036','patient.jose@hotmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Jose Fernandez','readonly',TRUE,TRUE),
('a1000003-0000-0000-0000-000000000037','patient.kira@gmail.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.','Kira Sokolova','readonly',TRUE,TRUE)
ON CONFLICT (email) DO NOTHING;

-- ── PATIENTS (35 patients with realistic clinical data) ───────
INSERT INTO patients (id, age, gender, bmi, blood_pressure_systolic, blood_pressure_diastolic,
  heart_rate, glucose_level, hba1c, cholesterol_total, cholesterol_ldl, cholesterol_hdl,
  triglycerides, smoking_status, alcohol_use, physical_activity_level,
  has_diabetes, has_hypertension, has_heart_disease, has_kidney_disease,
  family_history_diabetes, family_history_heart_disease) VALUES
('b1000001-0000-0000-0000-000000000001',52,'male',31.5,145,92,78,118,6.1,210,140,42,190,'former','moderate','sedentary',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000002',67,'female',28.2,158,95,82,142,7.2,245,168,38,220,'never','none','light',TRUE,TRUE,FALSE,TRUE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000003',44,'male',24.8,118,76,68,88,5.2,185,108,58,120,'never','moderate','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000004',71,'male',33.1,162,98,84,168,8.1,258,175,35,280,'current','heavy','sedentary',TRUE,TRUE,TRUE,FALSE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000005',38,'female',22.5,112,72,64,82,4.9,172,98,65,95,'never','none','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000006',59,'male',29.7,138,88,76,108,5.9,225,148,45,165,'former','none','light',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000007',48,'female',36.2,152,94,88,132,6.8,238,162,40,210,'never','moderate','sedentary',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000008',62,'male',27.4,128,82,72,96,5.4,198,118,52,135,  'never','light','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,TRUE),
('b1000001-0000-0000-0000-000000000009',55,'female',30.8,148,91,80,124,6.4,232,155,43,195,'former','none','sedentary',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000010',41,'male',23.6,115,74,70,86,5.1,178,102,60,108,'never','light','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000011',76,'female',26.9,168,102,86,156,7.8,268,185,32,295,'never','none','sedentary',TRUE,TRUE,TRUE,TRUE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000012',33,'male',21.8,108,68,62,78,4.7,162,88,68,85,'never','moderate','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000013',64,'female',32.4,155,96,84,138,7.0,248,170,38,225,'former','light','light',FALSE,TRUE,FALSE,FALSE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000014',58,'male',28.9,135,85,74,102,5.7,215,135,48,155,'never','none','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000015',47,'female',34.7,150,93,82,128,6.6,242,162,39,218,'never','none','sedentary',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000016',69,'male',30.2,160,99,88,162,7.9,262,178,34,285,'current','heavy','sedentary',TRUE,TRUE,TRUE,FALSE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000017',42,'female',25.6,122,78,68,90,5.3,188,112,56,118,'never','moderate','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000018',53,'male',27.8,132,84,72,98,5.6,205,128,50,148,'former','light','light',FALSE,FALSE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000019',60,'female',35.1,154,96,86,135,6.9,252,172,37,228,'never','none','sedentary',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000020',45,'male',26.3,125,80,70,94,5.4,192,115,54,128,'never','moderate','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,TRUE),
('b1000001-0000-0000-0000-000000000021',72,'female',29.4,164,100,88,158,7.7,265,182,33,290,'never','none','sedentary',TRUE,TRUE,TRUE,TRUE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000022',36,'male',22.1,110,70,64,84,5.0,175,100,62,98,'never','light','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000023',57,'female',31.9,146,90,80,122,6.3,228,152,42,188,'former','none','light',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000024',49,'male',24.2,119,76,68,88,5.2,182,105,58,112,'never','moderate','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000025',65,'female',33.8,156,97,84,145,7.3,255,175,36,238,'former','none','sedentary',TRUE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000026',50,'male',25.9,126,80,70,92,5.3,195,118,52,132,'never','light','moderate',FALSE,FALSE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000027',73,'male',31.4,166,101,90,165,8.2,270,188,31,298,'current','none','sedentary',TRUE,TRUE,TRUE,TRUE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000028',39,'female',23.8,114,74,66,86,5.1,179,104,60,105,'never','moderate','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000029',54,'male',29.1,136,86,74,105,5.8,218,138,47,162,'former','light','light',FALSE,FALSE,FALSE,FALSE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000030',61,'female',32.7,151,94,82,130,6.7,244,165,38,215,'never','none','sedentary',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000031',46,'male',26.8,124,79,70,92,5.3,190,114,54,125,'never','moderate','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000032',68,'female',28.5,158,96,84,148,7.4,258,176,35,242,'never','none','light',TRUE,TRUE,FALSE,FALSE,TRUE,TRUE),
('b1000001-0000-0000-0000-000000000033',43,'male',23.4,116,74,66,85,5.0,176,100,62,100,'never','light','active',FALSE,FALSE,FALSE,FALSE,FALSE,FALSE),
('b1000001-0000-0000-0000-000000000034',56,'female',30.5,142,89,78,118,6.2,222,148,44,178,'former','none','light',FALSE,TRUE,FALSE,FALSE,TRUE,FALSE),
('b1000001-0000-0000-0000-000000000035',63,'male',27.2,130,83,72,98,5.5,202,125,50,142,'never','none','moderate',FALSE,FALSE,FALSE,FALSE,FALSE,TRUE)
ON CONFLICT (id) DO NOTHING;

-- ── PREDICTION RECORDS (35 predictions matching patients) ────
INSERT INTO prediction_records (id, patient_id, requested_by, disease_type, model_type, model_version,
  risk_score, risk_category, confidence, input_features) VALUES
('c1000001-0000-0000-0000-000000000001','b1000001-0000-0000-0000-000000000001','a1000001-0000-0000-0000-000000000001','diabetes','ensemble','1.0.0',0.71,'high',0.97,'{"age":52,"gender":"male","bmi":31.5,"glucose_level":118,"hba1c":6.1}'),
('c1000001-0000-0000-0000-000000000002','b1000001-0000-0000-0000-000000000002','a1000001-0000-0000-0000-000000000001','diabetes','ensemble','1.0.0',0.88,'critical',0.96,'{"age":67,"gender":"female","bmi":28.2,"glucose_level":142,"hba1c":7.2}'),
('c1000001-0000-0000-0000-000000000003','b1000001-0000-0000-0000-000000000003','a1000001-0000-0000-0000-000000000002','diabetes','ensemble','1.0.0',0.14,'low',0.94,'{"age":44,"gender":"male","bmi":24.8,"glucose_level":88,"hba1c":5.2}'),
('c1000001-0000-0000-0000-000000000004','b1000001-0000-0000-0000-000000000004','a1000001-0000-0000-0000-000000000001','heart_disease','ensemble','1.0.0',0.91,'critical',0.98,'{"age":71,"gender":"male","bmi":33.1,"cholesterol_total":258,"cholesterol_ldl":175}'),
('c1000001-0000-0000-0000-000000000005','b1000001-0000-0000-0000-000000000005','a1000001-0000-0000-0000-000000000002','heart_disease','ensemble','1.0.0',0.09,'low',0.95,'{"age":38,"gender":"female","bmi":22.5,"cholesterol_total":172,"cholesterol_ldl":98}'),
('c1000001-0000-0000-0000-000000000006','b1000001-0000-0000-0000-000000000006','a1000001-0000-0000-0000-000000000001','hypertension','ensemble','1.0.0',0.62,'high',0.93,'{"age":59,"gender":"male","bmi":29.7,"blood_pressure_systolic":138}'),
('c1000001-0000-0000-0000-000000000007','b1000001-0000-0000-0000-000000000007','a1000001-0000-0000-0000-000000000003','diabetes','ensemble','1.0.0',0.68,'high',0.95,'{"age":48,"gender":"female","bmi":36.2,"glucose_level":132,"hba1c":6.8}'),
('c1000001-0000-0000-0000-000000000008','b1000001-0000-0000-0000-000000000008','a1000001-0000-0000-0000-000000000002','heart_disease','xgboost','1.0.0',0.28,'medium',0.91,'{"age":62,"gender":"male","bmi":27.4,"cholesterol_total":198}'),
('c1000001-0000-0000-0000-000000000009','b1000001-0000-0000-0000-000000000009','a1000001-0000-0000-0000-000000000001','hypertension','ensemble','1.0.0',0.74,'high',0.94,'{"age":55,"gender":"female","bmi":30.8,"blood_pressure_systolic":148}'),
('c1000001-0000-0000-0000-000000000010','b1000001-0000-0000-0000-000000000010','a1000001-0000-0000-0000-000000000002','diabetes','lightgbm','1.0.0',0.12,'low',0.93,'{"age":41,"gender":"male","bmi":23.6,"glucose_level":86,"hba1c":5.1}'),
('c1000001-0000-0000-0000-000000000011','b1000001-0000-0000-0000-000000000011','a1000001-0000-0000-0000-000000000001','stroke','ensemble','1.0.0',0.85,'critical',0.97,'{"age":76,"gender":"female","bmi":26.9,"blood_pressure_systolic":168}'),
('c1000001-0000-0000-0000-000000000012','b1000001-0000-0000-0000-000000000012','a1000001-0000-0000-0000-000000000003','diabetes','ensemble','1.0.0',0.08,'low',0.96,'{"age":33,"gender":"male","bmi":21.8,"glucose_level":78,"hba1c":4.7}'),
('c1000001-0000-0000-0000-000000000013','b1000001-0000-0000-0000-000000000013','a1000001-0000-0000-0000-000000000001','diabetes','ensemble','1.0.0',0.75,'high',0.95,'{"age":64,"gender":"female","bmi":32.4,"glucose_level":138,"hba1c":7.0}'),
('c1000001-0000-0000-0000-000000000014','b1000001-0000-0000-0000-000000000014','a1000001-0000-0000-0000-000000000002','heart_disease','ensemble','1.0.0',0.35,'medium',0.92,'{"age":58,"gender":"male","bmi":28.9,"cholesterol_total":215}'),
('c1000001-0000-0000-0000-000000000015','b1000001-0000-0000-0000-000000000015','a1000001-0000-0000-0000-000000000001','hypertension','ensemble','1.0.0',0.69,'high',0.93,'{"age":47,"gender":"female","bmi":34.7,"blood_pressure_systolic":150}'),
('c1000001-0000-0000-0000-000000000016','b1000001-0000-0000-0000-000000000016','a1000001-0000-0000-0000-000000000001','stroke','ensemble','1.0.0',0.89,'critical',0.98,'{"age":69,"gender":"male","bmi":30.2,"blood_pressure_systolic":160}'),
('c1000001-0000-0000-0000-000000000017','b1000001-0000-0000-0000-000000000017','a1000001-0000-0000-0000-000000000003','diabetes','ensemble','1.0.0',0.16,'low',0.94,'{"age":42,"gender":"female","bmi":25.6,"glucose_level":90,"hba1c":5.3}'),
('c1000001-0000-0000-0000-000000000018','b1000001-0000-0000-0000-000000000018','a1000001-0000-0000-0000-000000000002','heart_disease','random_forest','1.0.0',0.41,'medium',0.90,'{"age":53,"gender":"male","bmi":27.8,"cholesterol_total":205}'),
('c1000001-0000-0000-0000-000000000019','b1000001-0000-0000-0000-000000000019','a1000001-0000-0000-0000-000000000001','diabetes','ensemble','1.0.0',0.77,'high',0.96,'{"age":60,"gender":"female","bmi":35.1,"glucose_level":135,"hba1c":6.9}'),
('c1000001-0000-0000-0000-000000000020','b1000001-0000-0000-0000-000000000020','a1000001-0000-0000-0000-000000000002','heart_disease','ensemble','1.0.0',0.32,'medium',0.91,'{"age":45,"gender":"male","bmi":26.3,"cholesterol_total":192}'),
('c1000001-0000-0000-0000-000000000021','b1000001-0000-0000-0000-000000000021','a1000001-0000-0000-0000-000000000001','kidney_disease','ensemble','1.0.0',0.82,'critical',0.97,'{"age":72,"gender":"female","bmi":29.4,"glucose_level":158,"hba1c":7.7}'),
('c1000001-0000-0000-0000-000000000022','b1000001-0000-0000-0000-000000000022','a1000001-0000-0000-0000-000000000003','diabetes','ensemble','1.0.0',0.10,'low',0.95,'{"age":36,"gender":"male","bmi":22.1,"glucose_level":84,"hba1c":5.0}'),
('c1000001-0000-0000-0000-000000000023','b1000001-0000-0000-0000-000000000023','a1000001-0000-0000-0000-000000000001','hypertension','ensemble','1.0.0',0.65,'high',0.94,'{"age":57,"gender":"female","bmi":31.9,"blood_pressure_systolic":146}'),
('c1000001-0000-0000-0000-000000000024','b1000001-0000-0000-0000-000000000024','a1000001-0000-0000-0000-000000000002','diabetes','ensemble','1.0.0',0.18,'low',0.93,'{"age":49,"gender":"male","bmi":24.2,"glucose_level":88,"hba1c":5.2}'),
('c1000001-0000-0000-0000-000000000025','b1000001-0000-0000-0000-000000000025','a1000001-0000-0000-0000-000000000001','diabetes','ensemble','1.0.0',0.83,'critical',0.96,'{"age":65,"gender":"female","bmi":33.8,"glucose_level":145,"hba1c":7.3}'),
('c1000001-0000-0000-0000-000000000026','b1000001-0000-0000-0000-000000000026','a1000001-0000-0000-0000-000000000002','heart_disease','ensemble','1.0.0',0.29,'medium',0.92,'{"age":50,"gender":"male","bmi":25.9,"cholesterol_total":195}'),
('c1000001-0000-0000-0000-000000000027','b1000001-0000-0000-0000-000000000027','a1000001-0000-0000-0000-000000000001','stroke','ensemble','1.0.0',0.92,'critical',0.98,'{"age":73,"gender":"male","bmi":31.4,"blood_pressure_systolic":166}'),
('c1000001-0000-0000-0000-000000000028','b1000001-0000-0000-0000-000000000028','a1000001-0000-0000-0000-000000000003','diabetes','ensemble','1.0.0',0.13,'low',0.94,'{"age":39,"gender":"female","bmi":23.8,"glucose_level":86,"hba1c":5.1}'),
('c1000001-0000-0000-0000-000000000029','b1000001-0000-0000-0000-000000000029','a1000001-0000-0000-0000-000000000002','heart_disease','ensemble','1.0.0',0.44,'medium',0.91,'{"age":54,"gender":"male","bmi":29.1,"cholesterol_total":218}'),
('c1000001-0000-0000-0000-000000000030','b1000001-0000-0000-0000-000000000030','a1000001-0000-0000-0000-000000000001','hypertension','ensemble','1.0.0',0.71,'high',0.95,'{"age":61,"gender":"female","bmi":32.7,"blood_pressure_systolic":151}'),
('c1000001-0000-0000-0000-000000000031','b1000001-0000-0000-0000-000000000031','a1000001-0000-0000-0000-000000000002','diabetes','ensemble','1.0.0',0.22,'medium',0.92,'{"age":46,"gender":"male","bmi":26.8,"glucose_level":92,"hba1c":5.3}'),
('c1000001-0000-0000-0000-000000000032','b1000001-0000-0000-0000-000000000032','a1000001-0000-0000-0000-000000000001','diabetes','ensemble','1.0.0',0.80,'high',0.96,'{"age":68,"gender":"female","bmi":28.5,"glucose_level":148,"hba1c":7.4}'),
('c1000001-0000-0000-0000-000000000033','b1000001-0000-0000-0000-000000000033','a1000001-0000-0000-0000-000000000003','heart_disease','ensemble','1.0.0',0.15,'low',0.94,'{"age":43,"gender":"male","bmi":23.4,"cholesterol_total":176}'),
('c1000001-0000-0000-0000-000000000034','b1000001-0000-0000-0000-000000000034','a1000001-0000-0000-0000-000000000001','hypertension','ensemble','1.0.0',0.58,'medium',0.93,'{"age":56,"gender":"female","bmi":30.5,"blood_pressure_systolic":142}'),
('c1000001-0000-0000-0000-000000000035','b1000001-0000-0000-0000-000000000035','a1000001-0000-0000-0000-000000000002','heart_disease','ensemble','1.0.0',0.38,'medium',0.91,'{"age":63,"gender":"male","bmi":27.2,"cholesterol_total":202}')
ON CONFLICT (id) DO NOTHING;

-- ── REAL-TIME STATS VIEW (used by dashboard API) ─────────────
-- Run this too — it enables fast dashboard queries

CREATE OR REPLACE VIEW dashboard_stats AS
SELECT
  (SELECT COUNT(*) FROM prediction_records)                    AS total_predictions,
  (SELECT COUNT(DISTINCT patient_id) FROM prediction_records)  AS total_patients,
  (SELECT COUNT(*) FROM users WHERE is_active = TRUE)          AS total_users,
  (SELECT COUNT(*) FROM prediction_records WHERE risk_category IN ('high','critical')) AS high_risk_count,
  (SELECT COUNT(*) FROM prediction_records WHERE risk_category = 'low')     AS low_risk_count,
  (SELECT COUNT(*) FROM prediction_records WHERE risk_category = 'medium')  AS medium_risk_count,
  (SELECT COUNT(*) FROM prediction_records WHERE risk_category = 'critical') AS critical_risk_count,
  (SELECT COUNT(*) FROM users WHERE role = 'clinician')   AS clinician_count,
  (SELECT COUNT(*) FROM users WHERE role = 'researcher')  AS researcher_count,
  (SELECT COUNT(*) FROM users WHERE role = 'patient')     AS patient_count,
  (SELECT COUNT(*) FROM users WHERE role = 'readonly')    AS readonly_count,
  ROUND(AVG(risk_score)::numeric * 100, 1)               AS avg_risk_percentage
FROM prediction_records;

-- Disease breakdown view
CREATE OR REPLACE VIEW disease_breakdown AS
SELECT
  disease_type,
  COUNT(*) AS total_predictions,
  COUNT(*) FILTER (WHERE risk_category IN ('high','critical')) AS high_risk,
  ROUND(AVG(risk_score)::numeric * 100, 1) AS avg_risk_pct,
  ROUND(AVG(confidence)::numeric * 100, 1) AS avg_confidence_pct
FROM prediction_records
GROUP BY disease_type
ORDER BY total_predictions DESC;

-- Daily trend view (last 14 days)
CREATE OR REPLACE VIEW daily_trend AS
SELECT
  DATE(created_at) AS day,
  COUNT(*) AS predictions,
  COUNT(*) FILTER (WHERE risk_category IN ('high','critical')) AS high_risk
FROM prediction_records
WHERE created_at >= NOW() - INTERVAL '14 days'
GROUP BY DATE(created_at)
ORDER BY day;

SELECT 'Seed data loaded successfully!' AS status,
  (SELECT COUNT(*) FROM users) AS users_total,
  (SELECT COUNT(*) FROM patients) AS patients_total,
  (SELECT COUNT(*) FROM prediction_records) AS predictions_total;
