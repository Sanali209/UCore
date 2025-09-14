# examples/api_with_db/main.py
import sys
from sqlalchemy import Column, Integer, String, Boolean, select
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import web

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.http import HttpServer
from framework.db import SQLAlchemyAdapter, Base
from framework.di import Depends

# 1. Define a SQLAlchemy Model
class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, index=True)
    completed = Column(Boolean, default=False)

# 2. Define a dependency provider for the database session
def get_db_session(adapter: SQLAlchemyAdapter):
    return adapter.get_session()

# 3. Application Factory
def create_api_app():
    app = App(name="TodoAPI")

    # Register core components
    http_server = HttpServer(app)
    db_adapter = SQLAlchemyAdapter(app)
    app.register_component(lambda: http_server)
    app.register_component(lambda: db_adapter)

    # --- Define API Endpoints ---

    @http_server.route("/todos", "POST")
    async def create_todo(request: web.Request, db: AsyncSession = Depends(lambda: get_db_session(db_adapter))):
        data = await request.json()
        new_todo = Todo(text=data['text'], completed=data.get('completed', False))
        db.add(new_todo)
        await db.commit()
        await db.refresh(new_todo)
        return web.json_response({"id": new_todo.id, "text": new_todo.text, "completed": new_todo.completed}, status=201)

    @http_server.route("/todos", "GET")
    async def get_todos(db: AsyncSession = Depends(lambda: get_db_session(db_adapter))):
        result = await db.execute(select(Todo))
        todos = result.scalars().all()
        return web.json_response([{"id": t.id, "text": t.text, "completed": t.completed} for t in todos])

    @http_server.route("/todos/{id}", "GET")
    async def get_todo(request: web.Request, db: AsyncSession = Depends(lambda: get_db_session(db_adapter))):
        todo_id = int(request.match_info['id'])
        todo = await db.get(Todo, todo_id)
        if todo is None:
            return web.json_response({"error": "Todo not found"}, status=404)
        return web.json_response({"id": todo.id, "text": todo.text, "completed": todo.completed})

    # A function to create DB tables, to be run at startup
    async def create_tables():
        async with db_adapter.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        app.logger.info("Database tables created.")

    # We can hook into the app's startup sequence to run this
    # A more robust solution would be a formal event system.
    original_start = app.start
    async def new_start():
        await original_start()
        await create_tables()
    app.start = new_start
    
    return app

if __name__ == "__main__":
    api_app = create_api_app()
    api_app.run()
