from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from .config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(120)
    )

    age: Mapped[int] = mapped_column(
        Integer
    )

    weight: Mapped[float] = mapped_column(
        Float
    )

    goal: Mapped[str] = mapped_column(
        String(80)
    )

    intensity: Mapped[str] = mapped_column(
        String(20)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    plans: Mapped[list["Plan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True
    )

    original_plan: Mapped[str] = mapped_column(
        Text
    )

    original_tip: Mapped[str] = mapped_column(
        Text
    )

    updated_plan: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    updated_tip: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    feedback: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    user: Mapped[User] = relationship(
        back_populates="plans"
    )


connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False


engine = create_engine(
    settings.database_url,
    connect_args=connect_args
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def save_user(
    user_id: str,
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str
) -> User:

    with SessionLocal() as db:

        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        if user:

            user.name = name
            user.age = age
            user.weight = weight
            user.goal = goal
            user.intensity = intensity

        else:

            user = User(
                user_id=user_id,
                name=name,
                age=age,
                weight=weight,
                goal=goal,
                intensity=intensity
            )

            db.add(user)

        db.commit()
        db.refresh(user)

        return user


def save_plan(
    user_pk: int,
    original_plan: str,
    original_tip: str
) -> Plan:

    with SessionLocal() as db:

        plan = Plan(
            user_id=user_pk,
            original_plan=original_plan,
            original_tip=original_tip
        )

        db.add(plan)

        db.commit()
        db.refresh(plan)

        return plan


def get_user(
    user_id: str
) -> Optional[User]:

    with SessionLocal() as db:

        return (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )


def get_latest_plan(
    user_id: str
) -> Optional[Plan]:

    with SessionLocal() as db:

        return (
            db.query(Plan)
            .join(User)
            .filter(User.user_id == user_id)
            .order_by(Plan.created_at.desc())
            .first()
        )


def update_plan(
    plan_id: int,
    feedback: str,
    updated_plan: str,
    updated_tip: str
) -> Optional[Plan]:

    with SessionLocal() as db:

        plan = db.get(Plan, plan_id)

        if not plan:
            return None

        plan.feedback = feedback
        plan.updated_plan = updated_plan
        plan.updated_tip = updated_tip
        plan.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(plan)

        return plan


def get_all_users_with_plans():

    with SessionLocal() as db:

        users = (
            db.query(User)
            .order_by(User.created_at.desc())
            .all()
        )

        return [
            (user, list(user.plans))
            for user in users
        ]


def delete_user(
    user_id: str
) -> bool:

    with SessionLocal() as db:

        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        if not user:
            return False

        db.delete(user)
        db.commit()

        return True