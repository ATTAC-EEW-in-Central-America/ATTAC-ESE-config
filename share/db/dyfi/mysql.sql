DROP TABLE IF EXISTS FeltReport;


CREATE TABLE FeltReport (
	_oid BIGINT(20) AUTO_INCREMENT,
	_last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	publicID VARCHAR(255) NOT NULL,
	time_value DATETIME NOT NULL,
	time_value_ms INTEGER NOT NULL,
	time_uncertainty DOUBLE UNSIGNED,
	time_lowerUncertainty DOUBLE UNSIGNED,
	time_upperUncertainty DOUBLE UNSIGNED,
	time_confidenceLevel DOUBLE UNSIGNED,
	time_pdf_variable_content BLOB,
	time_pdf_probability_content BLOB,
	time_pdf_used TINYINT(1) NOT NULL DEFAULT '0',
	latitude_value DOUBLE NOT NULL,
	latitude_uncertainty DOUBLE UNSIGNED,
	latitude_lowerUncertainty DOUBLE UNSIGNED,
	latitude_upperUncertainty DOUBLE UNSIGNED,
	latitude_confidenceLevel DOUBLE UNSIGNED,
	latitude_pdf_variable_content BLOB,
	latitude_pdf_probability_content BLOB,
	latitude_pdf_used TINYINT(1) NOT NULL DEFAULT '0',
	longitude_value DOUBLE NOT NULL,
	longitude_uncertainty DOUBLE UNSIGNED,
	longitude_lowerUncertainty DOUBLE UNSIGNED,
	longitude_upperUncertainty DOUBLE UNSIGNED,
	longitude_confidenceLevel DOUBLE UNSIGNED,
	longitude_pdf_variable_content BLOB,
	longitude_pdf_probability_content BLOB,
	longitude_pdf_used TINYINT(1) NOT NULL DEFAULT '0',
	location VARCHAR(64),
	intensity_value DOUBLE NOT NULL,
	intensity_uncertainty DOUBLE UNSIGNED,
	intensity_lowerUncertainty DOUBLE UNSIGNED,
	intensity_upperUncertainty DOUBLE UNSIGNED,
	intensity_confidenceLevel DOUBLE UNSIGNED,
	intensity_pdf_variable_content BLOB,
	intensity_pdf_probability_content BLOB,
	intensity_pdf_used TINYINT(1) NOT NULL DEFAULT '0',
	eventID VARCHAR(255),
	type VARCHAR(255),
	appID VARCHAR(255),
	ip VARCHAR(255),
	creationInfo_agencyID VARCHAR(64),
	creationInfo_agencyURI VARCHAR(255),
	creationInfo_author VARCHAR(128),
	creationInfo_authorURI VARCHAR(255),
	creationInfo_creationTime DATETIME,
	creationInfo_creationTime_ms INTEGER,
	creationInfo_modificationTime DATETIME,
	creationInfo_modificationTime_ms INTEGER,
	creationInfo_version VARCHAR(64),
	creationInfo_used TINYINT(1) NOT NULL DEFAULT '0',
	evaluationStatus VARCHAR(64),
	PRIMARY KEY(_oid),
	INDEX(publicID),
	INDEX(eventID)
) ENGINE=INNODB;

CREATE TABLE IF NOT EXISTS Meta (
    name CHAR(80) NOT NULL,
    value VARCHAR(255) NOT NULL,
    PRIMARY KEY(name)
) ENGINE=INNODB;

INSERT INTO Meta(name,value) VALUES ('Dyfi-Schema-Version', '0.4');
INSERT INTO Meta(name,value) VALUES ('Dyfi-Creation-Time', CURRENT_TIMESTAMP);
