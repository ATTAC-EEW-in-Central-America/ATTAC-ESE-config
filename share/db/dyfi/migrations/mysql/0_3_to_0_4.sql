UPDATE Meta SET value='0.4' WHERE name='Dyfi-Schema-Version';

ALTER TABLE FeltReport CHANGE floorLevel location VARCHAR(64);

CREATE INDEX publicID ON FeltReport(publicID);
