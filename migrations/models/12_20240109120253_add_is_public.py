from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "cardrequests" ADD "is_public" BOOL NOT NULL  DEFAULT False;
        ALTER TABLE "telebotusers" DROP COLUMN "user_type";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "cardrequests" DROP COLUMN "is_public";
        ALTER TABLE "telebotusers" ADD "user_type" VARCHAR(6) NOT NULL  DEFAULT 'User';"""
