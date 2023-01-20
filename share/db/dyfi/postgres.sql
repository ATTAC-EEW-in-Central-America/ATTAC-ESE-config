DROP TABLE FeltReport;
DROP SEQUENCE FeltReport_seq;


CREATE SEQUENCE FeltReport_seq;
CREATE TABLE FeltReport (
	_oid BIGINT DEFAULT NEXTVAL('FeltReport_seq') NOT NULL,
	_last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	m_publicID VARCHAR(255) NOT NULL,
	m_time_value TIMESTAMP NOT NULL,
	m_time_value_ms INTEGER NOT NULL,
	m_time_uncertainty DOUBLE PRECISION,
	m_time_lowerUncertainty DOUBLE PRECISION,
	m_time_upperUncertainty DOUBLE PRECISION,
	m_time_confidenceLevel DOUBLE PRECISION,
	m_time_pdf_variable_content BYTEA,
	m_time_pdf_probability_content BYTEA,
	m_time_pdf_used BOOLEAN NOT NULL DEFAULT '0',
	m_latitude_value DOUBLE PRECISION NOT NULL,
	m_latitude_uncertainty DOUBLE PRECISION,
	m_latitude_lowerUncertainty DOUBLE PRECISION,
	m_latitude_upperUncertainty DOUBLE PRECISION,
	m_latitude_confidenceLevel DOUBLE PRECISION,
	m_latitude_pdf_variable_content BYTEA,
	m_latitude_pdf_probability_content BYTEA,
	m_latitude_pdf_used BOOLEAN NOT NULL DEFAULT '0',
	m_longitude_value DOUBLE PRECISION NOT NULL,
	m_longitude_uncertainty DOUBLE PRECISION,
	m_longitude_lowerUncertainty DOUBLE PRECISION,
	m_longitude_upperUncertainty DOUBLE PRECISION,
	m_longitude_confidenceLevel DOUBLE PRECISION,
	m_longitude_pdf_variable_content BYTEA,
	m_longitude_pdf_probability_content BYTEA,
	m_longitude_pdf_used BOOLEAN NOT NULL DEFAULT '0',
	m_location VARCHAR(64),
	m_intensity_value DOUBLE PRECISION NOT NULL,
	m_intensity_uncertainty DOUBLE PRECISION,
	m_intensity_lowerUncertainty DOUBLE PRECISION,
	m_intensity_upperUncertainty DOUBLE PRECISION,
	m_intensity_confidenceLevel DOUBLE PRECISION,
	m_intensity_pdf_variable_content BYTEA,
	m_intensity_pdf_probability_content BYTEA,
	m_intensity_pdf_used BOOLEAN NOT NULL DEFAULT '0',
	m_eventID VARCHAR(255),
	m_type VARCHAR(255),
	m_appID VARCHAR(255),
	m_ip VARCHAR(255),
	m_creationInfo_agencyID VARCHAR(64),
	m_creationInfo_agencyURI VARCHAR(255),
	m_creationInfo_author VARCHAR(128),
	m_creationInfo_authorURI VARCHAR(255),
	m_creationInfo_creationTime TIMESTAMP,
	m_creationInfo_creationTime_ms INTEGER,
	m_creationInfo_modificationTime TIMESTAMP,
	m_creationInfo_modificationTime_ms INTEGER,
	m_creationInfo_version VARCHAR(64),
	m_creationInfo_used BOOLEAN NOT NULL DEFAULT '0',
	m_evaluationStatus VARCHAR(64),
	PRIMARY KEY(_oid)
);

CREATE INDEX FeltReport_m_publicID ON FeltReport(m_publicID);
CREATE INDEX FeltReport_m_eventID ON FeltReport(m_eventID);

CREATE TRIGGER FeltReport_update BEFORE UPDATE ON FeltReport FOR EACH ROW EXECUTE PROCEDURE update_modified();


CREATE TABLE IF NOT EXISTS Meta (
    name CHAR(80) NOT NULL,
    value VARCHAR(255) NOT NULL,
    PRIMARY KEY(name)
) ENGINE=INNODB;

INSERT INTO Meta(name,value) VALUES ('Dyfi-Schema-Version', '0.4');
INSERT INTO Meta(name,value) VALUES ('Dyfi-Creation-Time', CURRENT_TIMESTAMP);
