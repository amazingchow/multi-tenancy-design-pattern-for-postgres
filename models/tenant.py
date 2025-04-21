# -*- coding: utf-8 -*-
from models.base import Base

import sqlalchemy
import sqlalchemy.orm as sqlalchemy_orm


class Order(Base):
    __tablename__ = "orders"
    # __table_args__ = {"schema": "tenant_example"}  # 注意：这些模型没有指定 schema，它们将存在于当前 search_path 指向的租户 schema 中

    id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    product_id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id"))
    owner_id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    # owner: sqlalchemy_orm.Mapped["User"] = sqlalchemy_orm.relationship(back_populates="orders")
    quantity: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, nullable=False)

    def __repr__(self):
        return f"<Order(id={self.id}, product_id={self.product_id}, user_id={self.user_id})>"


class Product(Base):
    __tablename__ = "products"
    # __table_args__ = {"schema": "tenant_example"}  # 注意：这些模型没有指定 schema，它们将存在于当前 search_path 指向的租户 schema 中

    id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    name: sqlalchemy_orm.Mapped[str] = sqlalchemy_orm.mapped_column(sqlalchemy.String, index=True, nullable=False)
    description: sqlalchemy_orm.Mapped[str | None] = sqlalchemy_orm.mapped_column(sqlalchemy.String)
    price: sqlalchemy_orm.Mapped[float] = sqlalchemy_orm.mapped_column(sqlalchemy.Float, nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"


class User(Base):
    __tablename__ = "users"
    # __table_args__ = {"schema": "tenant_example"}  # 注意：这些模型没有指定 schema，它们将存在于当前 search_path 指向的租户 schema 中

    id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    name: sqlalchemy_orm.Mapped[str] = sqlalchemy_orm.mapped_column(sqlalchemy.String, index=True, nullable=False)
    email: sqlalchemy_orm.Mapped[str] = sqlalchemy_orm.mapped_column(sqlalchemy.String, unique=True, index=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.email}')>"


class Company(Base):
    __tablename__ = "companies"
    # __table_args__ = {"schema": "tenant_example"}  # 注意：这些模型没有指定 schema，它们将存在于当前 search_path 指向的租户 schema 中

    id: sqlalchemy_orm.Mapped[int] = sqlalchemy_orm.mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    name: sqlalchemy_orm.Mapped[str] = sqlalchemy_orm.mapped_column(sqlalchemy.String, index=True, nullable=False)
    description: sqlalchemy_orm.Mapped[str | None] = sqlalchemy_orm.mapped_column(sqlalchemy.String)

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}')>"
