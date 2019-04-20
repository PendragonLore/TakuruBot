CREATE TABLE IF NOT EXISTS memes
(
  guild_id BIGINT        NOT NULL,
  name     varchar(128)  NOT NULL,
  content  varchar(2000) NOT NULL,
  owner_id BIGINT        NOT NULL,
  count    INT           NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS prefixes
(
  guild_id BIGINT      NOT NULL,
  prefix   VARCHAR(32) NOT NULL
);
