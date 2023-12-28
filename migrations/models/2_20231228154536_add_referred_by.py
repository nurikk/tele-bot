from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "telebotusers" ADD "referred_by_id" INT;
        CREATE INDEX "idx_telebotuser_referre_46c5b6" ON "telebotusers" ("referred_by_id");
        ALTER TABLE "telebotusers" ADD CONSTRAINT "fk_telebotu_telebotu_066619b7" FOREIGN KEY ("referred_by_id") REFERENCES "telebotusers" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "telebotusers" DROP CONSTRAINT "fk_telebotu_telebotu_066619b7";
        DROP INDEX "idx_telebotuser_referre_46c5b6";
        ALTER TABLE "telebotusers" DROP COLUMN "referred_by_id";"""
