CREATE TABLE account_location (
	account_id INTEGER,
	CONSTRAINT FK_account_account_location
		FOREIGN KEY(account_id)
			REFERENCES account(id)
				ON DELETE CASCADE,
	location_id INTEGER,
	CONSTRAINT FK_location_account_location
		FOREIGN KEY(location_id)
			REFERENCES location(location_id)
				ON DELETE CASCADE,
	PRIMARY KEY (account_id, location_id),
	created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
)
