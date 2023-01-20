UPDATE Meta SET value='0.3' WHERE name='Dyfi-Schema-Version';

ALTER TABLE DYFIReport ADD _last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE DYFIReport ADD time_confidenceLevel DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD time_pdf_variable_content BLOB;
ALTER TABLE DYFIReport ADD time_pdf_probability_content BLOB;
ALTER TABLE DYFIReport ADD time_pdf_used TINYINT(1) NOT NULL DEFAULT '0';

ALTER TABLE DYFIReport ADD latitude_confidenceLevel DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD latitude_pdf_variable_content BLOB;
ALTER TABLE DYFIReport ADD latitude_pdf_probability_content BLOB;
ALTER TABLE DYFIReport ADD latitude_pdf_used TINYINT(1) NOT NULL DEFAULT '0';

ALTER TABLE DYFIReport ADD longitude_confidenceLevel DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD longitude_pdf_variable_content BLOB;
ALTER TABLE DYFIReport ADD longitude_pdf_probability_content BLOB;
ALTER TABLE DYFIReport ADD longitude_pdf_used TINYINT(1) NOT NULL DEFAULT '0';

ALTER TABLE DYFIReport ADD intensity_confidenceLevel DOUBLE UNSIGNED;
ALTER TABLE DYFIReport ADD intensity_pdf_variable_content BLOB;
ALTER TABLE DYFIReport ADD intensity_pdf_probability_content BLOB;
ALTER TABLE DYFIReport ADD intensity_pdf_used TINYINT(1) NOT NULL DEFAULT '0';

ALTER TABLE DYFIReport CHANGE type type VARCHAR(64) NOT NULL DEFAULT '';


ALTER TABLE DYFIReport RENAME TO FeltReport; 
