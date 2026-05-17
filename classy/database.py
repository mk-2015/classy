import asyncio
import os
from typing import Any, List, Tuple, Union, Dict, Callable, Optional


class Db:
    def __init__(
        self,
        etype: str = "sqlite",
        connection_string: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.etype = etype.lower()
        self.connection_string = connection_string or ":memory:"
        self.config = config or {}
        self.pool = None

    async def connect(self):
        if self.etype == "sqlite":
            import aiosqlite
            self.aiosqlite = aiosqlite
            self.pool = await aiosqlite.connect(self.connection_string)
            await self.pool.execute("PRAGMA journal_mode=WAL;")
            
        elif self.etype == "postgres":
            import asyncpg
            self.asyncpg = asyncpg
            self.pool = await asyncpg.create_pool(**self.config)

        elif self.etype == "mysql":
            import aiomysql
            self.aiomysql = aiomysql
            self.pool = await aiomysql.create_pool(**self.config)
        else:
            raise ValueError(f"Unsupported database type: {self.etype}")

    def _normalize_query(self, sql_string: str, params: Union[tuple, list]) -> Tuple[str, tuple]:
        if self.etype != "postgres":
            return sql_string, tuple(params)
        
        new_sql = []
        param_index = 1
        for char in sql_string:
            if char == '?':
                new_sql.append(f"${param_index}")
                param_index += 1
            else:
                new_sql.append(char)
        return "".join(new_sql), tuple(params)

    async def query(
        self, 
        sql_string: str, 
        params: Optional[Union[tuple, list]] = None, 
        fetch_all: bool = True, 
        autocommit: bool = False, 
        rollback: bool = True,
        retexpt: bool = False
    ) -> Any:
        raw_params = params or ()
        sql_string, normalized_params = self._normalize_query(sql_string, raw_params)

        if self.etype == "sqlite":
            try:
                cursor = await self.pool.execute(sql_string, normalized_params)
                
                if autocommit:
                    await self.pool.commit()

                if cursor.description:
                    result = await cursor.fetchall() if fetch_all else await cursor.fetchone()
                    await cursor.close()
                    return result
                
                await cursor.close()
                return None
            except Exception as exception:
                if rollback:
                    try:
                        await self.pool.rollback()
                    except Exception as rb_err:
                        print(f"SQLite Rollback failed: {rb_err}")
                        
                        if not retexpt: raise exception

                        if retexpt:
                            return exception
            
        elif self.etype == "postgres":
            async with self.pool.acquire() as conn:
                try:
                    if not autocommit:
                        async with conn.transaction():
                            is_select = sql_string.strip().lower().startswith("select")
                            if is_select:
                                rows = await conn.fetch(sql_string, *normalized_params)
                                return [dict(row) for row in rows] if fetch_all else (dict(rows[0]) if rows else None)
                            else:
                                return await conn.execute(sql_string, *normalized_params)
                    else:
                        is_select = sql_string.strip().lower().startswith("select")
                        if is_select:
                            rows = await conn.fetch(sql_string, *normalized_params)
                            return [dict(row) for row in rows] if fetch_all else (dict(rows[0]) if rows else None)
                        else:
                            return await conn.execute(sql_string, *normalized_params)
                except Exception as exception:
                    if rollback:
                        if not retexpt: raise exception

                        if retexpt:
                            return exception
                
        elif self.etype == "mysql":
            async with self.pool.acquire() as conn:
                async with conn.cursor(self.aiomysql.cursors.DictCursor) as cursor:
                    try:
                        exec_params = normalized_params if normalized_params else None
                        await cursor.execute(sql_string, exec_params)
                        
                        if autocommit:
                            await conn.commit()
                            
                        if cursor.description:
                            result = await cursor.fetchall() if fetch_all else await cursor.fetchone()
                            return result
                        return None
                    except Exception as exception:
                        if rollback:
                            try:
                                await conn.rollback()
                            except Exception as rb_err:
                                print(f"MySQL Rollback failed: {rb_err}")
                        if not retexpt: raise exception

                        if retexpt:
                            return exception

    async def query_amrq(
        self,
        queries: Dict[str, Union[str, Tuple[str], Tuple[str, Union[tuple, list]]]],
        fetch_all: bool = True,
        autocommit: bool = False,
        rollback: bool = True,
        return_exceptions: bool = False
    ) -> Dict[str, Any]:
        labels = list(queries.keys())
        tasks = []
        
        for label in labels:
            query_data = queries[label]
            
            if isinstance(query_data, str):
                sql = query_data
                params = ()
            elif isinstance(query_data, (tuple, list)):
                if not query_data:
                    continue
                sql = query_data[0]
                params = query_data[1] if len(query_data) > 1 else ()
            else:
                raise TypeError(f"Query under label '{label}' must be a string or sequence pair.")

            tasks.append(
                self.query(
                    sql_string=sql,
                    params=params,
                    fetch_all=fetch_all,
                    autocommit=autocommit,
                    rollback=rollback,
                    retexpt=return_exceptions
                )
            )
            
        raw_results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
        
        return dict(zip(labels, raw_results))

    async def close(self):
        if self.etype == "sqlite":
            await self.pool.close()
        elif self.etype == "postgres":
            await self.pool.close()
        elif self.etype == "mysql":
            self.pool.close()
            await self.pool.wait_closed()