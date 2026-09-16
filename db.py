import aiosqlite

DB_PATH = 'bot.db'


async def init_db(db_path: str = DB_PATH):
    """Database Initialisation when bot starts"""
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute('PRAGMA foreign_keys = ON')
        #schema
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                doc_id INTEGER PRIMARY KEY,
                local_path TEXT NOT NULL,
                filename TEXT,
                downloaded_at TEXT DEFAULT (datetime('now'))
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                recieved_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (doc_id) REFERENCES files(doc_id)
            )
        ''')

        await conn.commit()


async def add_file(doc_id: int, local_path: str, filename: str, db_path: str = DB_PATH):
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            'INSERT OR IGNORE INTO files (doc_id, local_path, filename) VALUES (?, ?, ?)',
            (doc_id, local_path, filename)
        )
        await db.commit()


async def get_file(doc_id: int, db_path: str = DB_PATH):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM files WHERE doc_id = ?', (doc_id,)
        ) as cursor:
            return await cursor.fetchone()


async def add_occurrence(doc_id: int, chat_id: int, message_id: int, user_id: int, db_path: str = DB_PATH) -> int:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            'INSERT INTO occurrences (doc_id, chat_id, message_id, user_id) '
            'VALUES (?, ?,?,?)',
            (doc_id, chat_id, message_id, user_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_occurrence(occurrence_id: int, db_path: str = DB_PATH):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            'SELECT * FROM occurrences WHERE id = ?', (occurrence_id,)
        ) as cursor:
            return await cursor.fetchone()
