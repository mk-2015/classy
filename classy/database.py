import asyncio


class Db:
    def __init__(
        self,
        etype="sqlite",
        connection_string=None,
        config=None
    ):

        self.etype = etype.lower()

        self.connection_string = (
            connection_string or ":memory:"
        )

        self.config = config or {}

        self.pool = None

    async def connect(self):
        if self.etype == "sqlite":

            import aiosqlite

            self.aiosqlite = aiosqlite

            self.pool = await aiosqlite.connect(
                self.connection_string
            )

        elif self.etype == "postgres":

            import asyncpg

            self.asyncpg = asyncpg

            self.pool = await asyncpg.create_pool(
                **self.config
            )

        elif self.etype == "mysql":

            import aiomysql

            self.aiomysql = aiomysql

            self.pool = await aiomysql.create_pool(
                **self.config
            )

        else:
            raise ValueError(
                f"Unsupported database type: {self.etype}"
            )

    async def query(self, sql_string, params=None, fetch_all=True, autocommit=False, rollback=True):

        params = params or ()

        if self.etype == "sqlite":
            try:

                cursor = await self.pool.execute(
                    sql_string,
                    params
                )

                if autocommit:
                    await self.pool.commit()

                if cursor.description:

                    if fetch_all:
                        result = await cursor.fetchall()
                    else:
                        result = await cursor.fetchone()

                    await cursor.close()

                    return result

                await cursor.close()
                return None

            except Exception as exception:
                if rollback:
                    try:
                        await self.pool.rollback()

                    except Exception as rollback_error:

                        print(f"Rollback failed: {rollback_error}")
                raise exception

        elif self.etype == "postgres":
            async with self.pool.acquire() as conn:
                transaction = conn.transaction()

                await transaction.start()

                try:
                    if sql_string.strip().lower().startswith(
                        "select"
                    ):
                        
                        rows = await conn.fetch(
                            sql_string,
                            *params
                        )

                        if fetch_all:
                            result = [
                                dict(row)
                                for row in rows
                            ]
                        else:
                            result = (
                                dict(rows[0])
                                if rows else None
                            )
                    else:
                        result = await conn.execute(
                            sql_string,
                            *params
                        )
                        
                    if autocommit:
                        await transaction.commit()
                    return result

                except Exception as exception:

                    if rollback:
                        await transaction.rollback()

                    raise exception

        elif self.etype == "mysql":
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    try:
                        await cursor.execute(
                            sql_string,
                            params
                        )
                        
                        if autocommit:
                            await conn.commit()
                        
                        if cursor.description:
                            if fetch_all:
                                result = (
                                    await cursor.fetchall()
                                )
                            else:
                                result = (
                                    await cursor.fetchone()
                                )
                            return result
                        
                        return None
                    except Exception as exception:
                        if rollback:
                            try:
                                await conn.rollback()
                            except Exception as rollback_error:
                                print(
                                    f"Rollback failed: "
                                    f"{rollback_error}"
                                )

                        raise exception

    async def query_amrq(
        self,
        queries,
        fetch_all=True,
        autocommit=False,
        rollback=True,
        return_exceptions=False
    ):

        tasks = []

        for query_data in queries:
            sql = query_data[0]

            params = ()

            if len(query_data) > 1:
                params = query_data[1]

            tasks.append(
                self.query(
                    sql,
                    params=params,
                    fetch_all=fetch_all,
                    autocommit=autocommit,
                    rollback=rollback
                )
            )

        return await asyncio.gather(
            *tasks,
            return_exceptions=return_exceptions
        )

    async def close(self):

        if self.etype == "sqlite":
            await self.pool.close()
        else:
            self.pool.close()
            await self.pool.wait_closed()