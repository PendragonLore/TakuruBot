CREATE TABLE IF NOT EXISTS memes
(
  guild_id BIGINT        NOT NULL,
  name     varchar(128)  NOT NULL,
  content  varchar(2000) NOT NULL,
  owner_id BIGINT        NOT NULL,
  count    INT           NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS memes_guild_id_name_uindex ON memes (guild_id, name);

CREATE TABLE IF NOT EXISTS prefixes
(
  guild_id BIGINT      NOT NULL,
  prefix   VARCHAR(32) NOT NULL UNIQUE
);
