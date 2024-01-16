from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "cardshareevent" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "request_id" INT NOT NULL REFERENCES "cardrequests" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "telebotusers" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_cardshareev_request_8d1130" ON "cardshareevent" ("request_id");
CREATE INDEX IF NOT EXISTS "idx_cardshareev_user_id_4f1b09" ON "cardshareevent" ("user_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "cardshareevent";"""
