import sqlalchemy

import app.db.session


class MigrationTest(app.db.session.Base):
    __tablename__ = "migration_test"

    id: sqlalchemy.orm.Mapped[int] = sqlalchemy.orm.mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    name: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        sqlalchemy.String(100),
        nullable=False,
    )