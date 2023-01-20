CREATE TABLE IF NOT EXISTS Meta (
	name CHAR(80) NOT NULL,
	value VARCHAR(255) NOT NULL,
	PRIMARY KEY(name)
) ENGINE=INNODB;

INSERT INTO Meta(name,value) VALUES ('Dyfi-Schema-Version', '0.1');
INSERT INTO Meta(name,value) VALUES ('Dyfi-Creation-Time', CURRENT_TIMESTAMP);

ALTER TABLE DYFIReport ADD contributor VARCHAR(255)
