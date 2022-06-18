-- upgrade --
CREATE TABLE IF NOT EXISTS "book" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "book_author" VARCHAR(255) NOT NULL,
    "book_title" TEXT NOT NULL,
    "isbn_code" BIGINT  UNIQUE
);
CREATE TABLE IF NOT EXISTS "user" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(255),
    "city" VARCHAR(255),
    "is_active" BOOL NOT NULL  DEFAULT True
);
COMMENT ON COLUMN "user"."username" IS 'Actual name of the client';
CREATE TABLE IF NOT EXISTS "library" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "swap_status" BOOL NOT NULL  DEFAULT False,
    "book_id" INT NOT NULL REFERENCES "book" ("id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "user" ("user_id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
