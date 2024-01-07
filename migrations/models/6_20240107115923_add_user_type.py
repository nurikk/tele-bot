from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "telebotusers" ADD "user_type" VARCHAR(6) NOT NULL  DEFAULT 'User';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "telebotusers" DROP COLUMN "user_type";"""
