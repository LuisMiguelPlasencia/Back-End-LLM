
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




