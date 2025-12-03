
--grant create on database conversa to app;

--create schema conversaConfig;
--create schema conversaAccesses; 
--create schema conversaThirdParty;
--create schema conversaApp;
--create schema conversaScoring;

--CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS conversaApp.conversations (
    user_id            UUID                NOT NULL,
    conversation_id    UUID DEFAULT uuid_generate_v4() NOT NULL,
    start_timestamp   TIMESTAMP         NULL,
    end_timestamp     TIMESTAMP         NULL,
    status            VARCHAR(50)         NULL,
    created_at        TIMESTAMP         NOT NULL DEFAULT now(),
    updated_at        TIMESTAMP         NOT NULL DEFAULT now(),
    PRIMARY KEY (conversation_id),
    CHECK (end_timestamp IS NULL OR start_timestamp IS NULL OR end_timestamp >= start_timestamp)
);

CREATE TABLE conversaApp.messages (
	id uuid DEFAULT uuid_generate_v4() NOT NULL,
	user_id UUID NULL,
	conversation_id uuid NOT NULL,
	"role" text NOT NULL,
	"content" text NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL,
	CONSTRAINT messages_pkey PRIMARY KEY (id),
	CONSTRAINT messages_role_check CHECK ((role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text, 'query'::text]))),
	CONSTRAINT messages_conversation_id_fkey FOREIGN key ( conversation_id) REFERENCES conversaApp.conversations(conversation_id) ON DELETE CASCADE
);



CREATE TABLE IF NOT EXISTS conversaConfig.user_info (
  user_id     UUID        NOT NULL DEFAULT uuid_generate_v4(),
  company_id  TEXT        NULL, -- optional FK to companies(id); add FK below if you have a companies table
  name        TEXT        NOT NULL,
  user_type   VARCHAR(32) NOT NULL DEFAULT 'user', -- e.g. 'user', 'admin', 'service', 'guest'
  email       TEXT        NOT NULL,
  password    TEXT        NOT NULL, -- will store bcrypt hash (not plaintext) thanks to trigger below
  api_key     TEXT    	  NULL,
  is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMP NOT NULL DEFAULT now(),
  updated_at  TIMESTAMP NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS conversaConfig.company_info (
  company_id    TEXT            NOT NULL,
  company_type          VARCHAR(64)     NULL,                
  contact_email TEXT            NULL,
  created_at    TIMESTAMP     NOT NULL DEFAULT now(),
  updated_at    TIMESTAMP     NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id)
);

/*
Back-end tables
Log conversation
Primary keys: Conver_id
Columns: Timestamp, user, status*/

CREATE TABLE IF NOT EXISTS conversaConfig.log_session (
  session_id      UUID                     NOT NULL DEFAULT uuid_generate_v4(),
  event_timestamp TIMESTAMP              NOT NULL DEFAULT now(),
  user_id         UUID                     NOT NULL,               
  status          TEXT,
  message_log     TEXT,
  PRIMARY KEY (session_id)
);

CREATE TABLE IF NOT EXISTS conversaScoring.user_profile (
  user_id       UUID             NOT NULL,                     -- PK & FK to user_info
  event_timestamp   TIMESTAMP      NOT NULL DEFAULT now(),      -- your "Time"
  general_score     NUMERIC(5,2)     NULL CHECK (general_score >= 0 AND general_score <= 100),
  profile_type       TEXT            NULL
);

CREATE TABLE IF NOT EXISTS conversaScoring.conversations_scoring (
  user_id     UUID            NOT NULL,                     -- FK -> user_info.user_id
  conversation_id   UUID            NOT NULL,                     -- conversation id
  course_id   UUID            NULL,                         -- FK -> courses(course_id) (optional)
  event_timestamp TIMESTAMP     NOT NULL DEFAULT now(),       -- your "time"
  general_score   NUMERIC(6,3)    NULL CHECK (general_score >= 0),  -- optional numeric KPI (scale up to you)
  comments       TEXT            null,
  PRIMARY KEY (user_id, conversation_id)
);

CREATE EXTENSION IF NOT EXISTS pgcrypto;

------------------------------
-- Tabla: user_types
------------------------------
CREATE TABLE IF NOT EXISTS conversaConfig.user_types (
  user_type   VARCHAR(64)    NOT NULL,   -- p.ej. 'student','teacher','admin'
  description TEXT           NULL,
  is_active   BOOLEAN        NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMP    NOT NULL DEFAULT now(),
  updated_at  TIMESTAMP    NOT NULL DEFAULT now(),
  PRIMARY KEY (user_type)
);

------------------------------
-- Tabla: master_courses
------------------------------
CREATE TABLE IF NOT EXISTS conversaConfig.master_courses (
  course_id    UUID           NOT NULL DEFAULT gen_random_uuid(),
  name         TEXT           NOT NULL,
  description  TEXT           NULL,
  image_src    VARCHAR(256)           NULL,                    -- referencia opcional a recursos/archivos
  created_on   TIMESTAMP   NOT NULL DEFAULT now(),
  updated_at   TIMESTAMP    NOT NULL DEFAULT now(),
  is_active    BOOLEAN        NOT NULL DEFAULT TRUE,
  PRIMARY KEY (course_id)
);

------------------------------
-- Tabla: user_type_relations
-- (relación entre user_type y course_id)
------------------------------
drop table conversaConfig.user_type_relations;
CREATE TABLE IF NOT EXISTS conversaConfig.user_type_relations (
  user_type   VARCHAR(64)     NOT NULL,
  course_id   UUID            NOT NULL,
  event_time  TIMESTAMP     NOT NULL DEFAULT now(),  -- "time"
  metrics     JSONB           NULL,                    -- flexible: {"score": 95, "progress": 0.6}
  notes       TEXT            NULL,
  created_at  TIMESTAMP     NOT NULL DEFAULT now(),
  updated_at  TIMESTAMP    NOT NULL DEFAULT now(),
  PRIMARY KEY (user_type, course_id),
  CONSTRAINT utr_user_type_fk FOREIGN KEY (user_type)
    REFERENCES conversaConfig.user_types(user_type)
    ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT utr_course_fkey FOREIGN KEY (course_id)
    REFERENCES conversaConfig.master_courses(course_id)
    ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS conversaconfig.course_stages (
  stage_id uuid DEFAULT gen_random_uuid() NOT NULL,
  course_id uuid NOT NULL REFERENCES conversaconfig.master_courses(course_id) ON DELETE CASCADE,
  stage_order integer NOT NULL,
  stage_name text NOT NULL,
  stage_description text NULL,
  created_on timestamp DEFAULT now() NOT NULL,
  updated_at timestamp DEFAULT now() NOT NULL,
  CONSTRAINT course_stages_pkey PRIMARY KEY (stage_id)
);

CREATE TABLE IF NOT EXISTS conversaconfig.course_contents (
  content_id uuid DEFAULT gen_random_uuid() NOT NULL,
  course_id uuid NOT NULL REFERENCES conversaconfig.master_courses(course_id) ON DELETE CASCADE,
  stage_id uuid NULL REFERENCES conversaconfig.course_stages(stage_id) ON DELETE SET NULL,
  position integer NULL,
  title text NOT NULL,
  body text NULL,
  resource_url text NULL,
  created_on timestamp DEFAULT now() NOT NULL,
  updated_at timestamp DEFAULT now() NOT NULL,
  CONSTRAINT course_contents_pkey PRIMARY KEY (content_id)
);

CREATE INDEX IF NOT EXISTS idx_course_stages_course ON conversaconfig.course_stages(course_id, stage_order);
CREATE INDEX IF NOT EXISTS idx_course_contents_course_stage ON conversaconfig.course_contents(course_id, stage_id, position);


ALTER TABLE conversaconfig.course_contents ADD COLUMN bot_prompt text NULL;
ALTER TABLE conversaapp.conversations ADD COLUMN stage_id uuid NULL;