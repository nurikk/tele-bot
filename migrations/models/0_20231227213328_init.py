from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "cardrequests" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "generated_prompt" TEXT,
    "revised_prompt" TEXT,
    "user_id" INT NOT NULL REFERENCES "telebotusers" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_cardrequest_user_id_2b6900" ON "cardrequests" ("user_id");
        CREATE TABLE IF NOT EXISTS "cardrequestsanswers" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "language_code" TEXT NOT NULL,
    "question" VARCHAR(12) NOT NULL,
    "answer" TEXT NOT NULL,
    "request_id" INT NOT NULL REFERENCES "cardrequests" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_cardrequest_questio_4aebc5" ON "cardrequestsanswers" ("question");
CREATE INDEX IF NOT EXISTS "idx_cardrequest_request_c17f74" ON "cardrequestsanswers" ("request_id");
COMMENT ON COLUMN "cardrequestsanswers"."question" IS 'REASON: reason\nRELATIONSHIP: relationship\nDESCRIPTION: description\nDEPICTION: depiction\nSTYLE: style';
        CREATE TABLE IF NOT EXISTS "telebotusers" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "last_seen" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "telegram_id" BIGINT NOT NULL UNIQUE,
    "full_name" TEXT,
    "username" TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS "idx_telebotuser_telegra_d6f8f1" ON "telebotusers" ("telegram_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "cardrequests";
        DROP TABLE IF EXISTS "cardrequestsanswers";
        DROP TABLE IF EXISTS "telebotusers";"""
