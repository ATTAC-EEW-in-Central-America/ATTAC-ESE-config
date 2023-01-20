DROP TABLE IF EXISTS FeltReport;


CREATE TABLE FeltReport (
	_oid INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	_last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	publicID VARCHAR(255) NOT NULL,
	time_value DATETIME NOT NULL,
	time_value_ms INTEGER NOT NULL,
	time_uncertainty DOUBLE UNSIGNED,
	time_lowerUncertainty DOUBLE UNSIGNED,
	time_upperUncertainty DOUBLE UNSIGNED,
	time_confidenceLevel DOUBLE UNSIGNED,
	time_pdf_variable_content BLOB,
	time_pdf_probability_content BLOB,
	time_pdf_used INTEGER(1) NOT NULL DEFAULT '0',
	latitude_value DOUBLE NOT NULL,
	latitude_uncertainty DOUBLE UNSIGNED,
	latitude_lowerUncertainty DOUBLE UNSIGNED,
	latitude_upperUncertainty DOUBLE UNSIGNED,
	latitude_confidenceLevel DOUBLE UNSIGNED,
	latitude_pdf_variable_content BLOB,
	latitude_pdf_probability_content BLOB,
	latitude_pdf_used INTEGER(1) NOT NULL DEFAULT '0',
	longitude_value DOUBLE NOT NULL,
	longitude_uncertainty DOUBLE UNSIGNED,
	longitude_lowerUncertainty DOUBLE UNSIGNED,
	longitude_upperUncertainty DOUBLE UNSIGNED,
	longitude_confidenceLevel DOUBLE UNSIGNED,
	longitude_pdf_variable_content BLOB,
	longitude_pdf_probability_content BLOB,
	longitude_pdf_used INTEGER(1) NOT NULL DEFAULT '0',
	location VARCHAR,
	intensity_value DOUBLE NOT NULL,
	intensity_uncertainty DOUBLE UNSIGNED,
	intensity_lowerUncertainty DOUBLE UNSIGNED,
	intensity_upperUncertainty DOUBLE UNSIGNED,
	intensity_confidenceLevel DOUBLE UNSIGNED,
	intensity_pdf_variable_content BLOB,
	intensity_pdf_probability_content BLOB,
	intensity_pdf_used INTEGER(1) NOT NULL DEFAULT '0',
	eventID VARCHAR,
	type VARCHAR,
	appID VARCHAR,
	ip VARCHAR,
	creationInfo_agencyID VARCHAR,
	creationInfo_agencyURI VARCHAR,
	creationInfo_author VARCHAR,
	creationInfo_authorURI VARCHAR,
	creationInfo_creationTime DATETIME,
	creationInfo_creationTime_ms INTEGER,
	creationInfo_modificationTime DATETIME,
	creationInfo_modificationTime_ms INTEGER,
	creationInfo_version VARCHAR,
	creationInfo_used INTEGER(1) NOT NULL DEFAULT '0',
	evaluationStatus VARCHAR(64)
);

CREATE INDEX FeltReport_publicID ON FeltReport(publicID);
CREATE INDEX FeltReport_eventID ON FeltReport(eventID);

CREATE TRIGGER FeltReportUpdate UPDATE ON FeltReport
BEGIN
  UPDATE FeltReport SET _last_modified=CURRENT_TIMESTAMP WHERE _oid=old._oid;
END;

CREATE TABLE IF NOT EXISTS Meta (
    name CHAR(80) NOT NULL,
    value VARCHAR(255) NOT NULL,
    PRIMARY KEY(name)
);

INSERT INTO Meta(name,value) VALUES ('Dyfi-Schema-Version', '0.4');
INSERT INTO Meta(name,value) VALUES ('Dyfi-Creation-Time', CURRENT_TIMESTAMP);
