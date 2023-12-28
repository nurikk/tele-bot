from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "telebotusers" ADD "remaining_cards" INT NOT NULL  DEFAULT 5;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "telebotusers" DROP COLUMN "remaining_cards";"""
