from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "cardresult" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "result_image" TEXT,
    "request_id" INT NOT NULL REFERENCES "cardrequests" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_cardresult_request_41fdb6" ON "cardresult" ("request_id");
INSERT INTO "cardresult" ("request_id", "result_image") 
(
    select id as request_id, result_image from "cardrequests"
);
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "cardresult";"""
