import uuid

from decimal import Decimal

from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    String,
    Text,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


# -----------------------
# Association Tables
# -----------------------

movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("director_id", ForeignKey("directors.id", ondelete="CASCADE"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("star_id", ForeignKey("stars.id", ondelete="CASCADE"), primary_key=True),
)


# -----------------------
# Genre
# -----------------------

class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
    )


# -----------------------
# Star
# -----------------------

class Star(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_stars,
        back_populates="stars",
    )


# -----------------------
# Director
# -----------------------

class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_directors,
        back_populates="directors",
    )


# -----------------------
# Certification
# -----------------------

class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    movies: Mapped[list["Movie"]] = relationship(
        back_populates="certification"
    )


# -----------------------
# Movie
# -----------------------

class Movie(Base):
    __tablename__ = "movies"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "year",
            "time",
            name="uq_movie_name_year_time",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(250))

    year: Mapped[int]

    time: Mapped[int]

    imdb: Mapped[float]

    votes: Mapped[int]

    meta_score: Mapped[float | None]

    gross: Mapped[float | None]

    description: Mapped[str] = mapped_column(Text)

    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2)
    )

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id")
    )

    certification: Mapped["Certification"] = relationship(
        back_populates="movies"
    )

    genres: Mapped[list["Genre"]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
    )

    directors: Mapped[list["Director"]] = relationship(
        secondary=movie_directors,
        back_populates="movies",
    )

    stars: Mapped[list["Star"]] = relationship(
        secondary=movie_stars,
        back_populates="movies",
    )
