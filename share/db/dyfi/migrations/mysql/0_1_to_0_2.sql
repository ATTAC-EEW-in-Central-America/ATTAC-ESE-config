UPDATE Meta SET value='0.2' WHERE name='Dyfi-Schema-Version';

ALTER TABLE DYFIReport CHANGE id _oid BIGINT(20) AUTO_INCREMENT;
ALTER TABLE DYFIReport ADD publicID VARCHAR(255) NOT NULL;

ALTER TABLE DYFIReport CHANGE time time_value DATETIME NOT NULL;
ALTER TABLE DYFIReport ADD time_value_ms INTEGER NOT NULL;
ALTER TABLE DYFIReport ADD time_uncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD time_lowerUncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD time_upperUncertainty DOUBLE UNSIGNED;

ALTER TABLE DYFIReport CHANGE latitude latitude_value DOUBLE NOT NULL;
ALTER TABLE DYFIReport ADD latitude_uncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD latitude_lowerUncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD latitude_upperUncertainty DOUBLE UNSIGNED;

ALTER TABLE DYFIReport CHANGE longitude longitude_value DOUBLE NOT NULL;
ALTER TABLE DYFIReport ADD longitude_uncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD longitude_lowerUncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD longitude_upperUncertainty DOUBLE UNSIGNED;

ALTER TABLE DYFIReport ADD floorLevel INTEGER;

ALTER TABLE DYFIReport CHANGE intensity intensity_value DOUBLE NOT NULL;
ALTER TABLE DYFIReport ADD intensity_uncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD intensity_lowerUncertainty DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD intensity_upperUncertainty DOUBLE UNSIGNED;

ALTER TABLE DYFIReport ADD type VARCHAR(64);
ALTER TABLE DYFIReport ADD evaluationStatus VARCHAR(64);

ALTER TABLE DYFIReport CHANGE contributor creationInfo_agencyID VARCHAR(64);
ALTER TABLE DYFIReport ADD creationInfo_agencyURI VARCHAR(255);
ALTER TABLE DYFIReport ADD creationInfo_author VARCHAR(128);
ALTER TABLE DYFIReport ADD creationInfo_authorURI VARCHAR(255);
ALTER TABLE DYFIReport ADD creationInfo_creationTime DATETIME;
ALTER TABLE DYFIReport ADD creationInfo_creationTime_ms INTEGER;
ALTER TABLE DYFIReport ADD creationInfo_modificationTime DATETIME;
ALTER TABLE DYFIReport ADD creationInfo_modificationTime_ms INTEGER;
ALTER TABLE DYFIReport ADD creationInfo_version VARCHAR(64);
ALTER TABLE DYFIReport ADD creationInfo_used TINYINT(1) NOT NULL DEFAULT '0';

ALTER TABLE DYFIReport CHANGE event_id eventID VARCHAR(255);
ALTER TABLE DYFIReport CHANGE app_id appID VARCHAR(255);

UPDATE DYFIReport SET creationInfo_used=1;

UPDATE DYFIReport SET creationInfo_creationTime=created;
UPDATE DYFIReport SET creationInfo_creationTime_ms=0;

UPDATE DYFIReport SET publicID=CONCAT('DYFIReport/', _oid);

DROP INDEX time on DYFIReport;
DROP INDEX created on DYFIReport;
DROP INDEX event_id on DYFIReport;
DROP INDEX app_id on DYFIReport;

ALTER TABLE DYFIReport DROP elevation;
ALTER TABLE DYFIReport DROP created;

CREATE INDEX publicID on DYFIReport(publicID);
CREATE INDEX eventID ON DYFIReport(eventID);
