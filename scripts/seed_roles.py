import asyncio

import app.db.session
import app.modules.auth.seed


async def main() -> None:
    async with app.db.session.async_session_factory() as session:
        await app.modules.auth.seed.ensure_default_roles(session)
        await session.commit()
        print("Default roles are ready.")

    await app.db.session.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())