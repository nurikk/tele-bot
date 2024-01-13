from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        TRUNCATE "holidays";
        ALTER TABLE "holidays" ADD "url" TEXT NOT NULL;
        ALTER TABLE "holidays" ADD "description" TEXT NOT NULL;
        ALTER TABLE "holidays" ADD "date" DATE NOT NULL;
        ALTER TABLE "holidays" DROP COLUMN "day";
        ALTER TABLE "holidays" DROP COLUMN "month";"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "holidays" ADD "day" INT NOT NULL;
        ALTER TABLE "holidays" ADD "month" INT NOT NULL;
        ALTER TABLE "holidays" DROP COLUMN "url";
        ALTER TABLE "holidays" DROP COLUMN "description";
        ALTER TABLE "holidays" DROP COLUMN "date";"""
