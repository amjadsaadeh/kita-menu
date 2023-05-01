from sqlalchemy.types import Date
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    pass

class MenuItem(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250))
    
    def __repr__(self) -> str:
        return f"MenuItem(id={self.id!r}, name={self.name!r})"
