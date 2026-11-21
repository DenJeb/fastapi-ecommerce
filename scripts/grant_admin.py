import asyncio
import sysconfig

import sqlalchemy

import app.db.session
import app.modules.auth.models as auth_models


async def main(email: str) -> None:
    try:
        async with app.db.session.async_session_factory() as session:
            user = await session.scalar(
                sqlalchemy.select(auth_models.User).where(
                    auth_models.User.email == email.lower()
                )
            )
            if user is None:
                print(f"User not found: {email}")
                return
            role = await session.scalar(
                sqlalchemy.select(auth_models.Role).where(
                    auth_models.Role.name == "admin"
                )
            )
            if role is None:
                print("Admin role is not seeded. Run scripts/seed_roles.py first.")
                return

            if any(existing.name == "admin" for existing in user.roles):
                print(f"{email} is already an admin.")
                return

            user.roles.append(role)
            await session.commit()
            print(f"Granted admin role to {email}.")
    finally:
        await app.db.session.engine.dispose()


if __name__ == "__main__":
    if len(sys.arvg) != 2:
        raise SystemExit("Usage: python scripts/grant_admin.py <email>")
    asyncio.run(main(sys.arvg[1]))