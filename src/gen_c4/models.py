from typing import List, Optional

from sqlalchemy import ForeignKey, ForeignKeyConstraint, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class ComponentTech(Base):
    __tablename__ = 'TB_COMPONENT_TECH'

    CODE: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    NAME: Mapped[Optional[str]] = mapped_column(Text)


class ComponentType(Base):
    __tablename__ = 'TB_COMPONENT_TYPE'

    code: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)

    TB_COMPONENT: Mapped[List['Component']] = relationship('Component', back_populates='TB_COMPONENT_TYPE')


class Domain(Base):
    __tablename__ = 'TB_DOMAIN'

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parent_code: Mapped[Optional[str]] = mapped_column(ForeignKey('TB_DOMAIN.code'))

    TB_DOMAIN: Mapped['Domain'] = relationship('Domain', remote_side=[code], back_populates='TB_DOMAIN_reverse')
    TB_DOMAIN_reverse: Mapped[List['Domain']] = relationship('Domain', remote_side=[parent_code], back_populates='TB_DOMAIN')
    TB_COMPONENT: Mapped[List['Component']] = relationship('Component', back_populates='TB_DOMAIN')


class ObjectType(Base):
    __tablename__ = 'TB_OBJECT_TYPE'

    code: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)

    TB_CODE_OBJECT: Mapped[List['CodeObject']] = relationship('CodeObject', back_populates='TB_OBJECT_TYPE')


class Component(Base):
    __tablename__ = 'TB_COMPONENT'

    code: Mapped[Optional[str]] = mapped_column(Text, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    domain_code: Mapped[Optional[str]] = mapped_column(ForeignKey('TB_DOMAIN.code'))
    type: Mapped[Optional[str]] = mapped_column(ForeignKey('TB_COMPONENT_TYPE.code'))
    PARENT_CODE: Mapped[Optional[str]] = mapped_column(ForeignKey('TB_COMPONENT.code'))

    TB_COMPONENT: Mapped['Component'] = relationship('Component', remote_side=[code], back_populates='TB_COMPONENT_reverse')
    TB_COMPONENT_reverse: Mapped[List['Component']] = relationship('Component', remote_side=[PARENT_CODE], back_populates='TB_COMPONENT')
    TB_DOMAIN: Mapped['Domain'] = relationship('Domain', back_populates='TB_COMPONENT')
    TB_COMPONENT_TYPE: Mapped['ComponentType'] = relationship('ComponentType', back_populates='TB_COMPONENT')
    TB_CODE_OBJECT: Mapped[List['CodeObject']] = relationship('CodeObject', back_populates='TB_COMPONENT')


class CodeObject(Base):
    __tablename__ = 'TB_CODE_OBJECT'

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(ForeignKey('TB_OBJECT_TYPE.code'))
    system_component_code: Mapped[str] = mapped_column(ForeignKey('TB_COMPONENT.code'))
    source_file: Mapped[Optional[str]] = mapped_column(Text)

    TB_COMPONENT: Mapped['Component'] = relationship('Component', back_populates='TB_CODE_OBJECT')
    TB_OBJECT_TYPE: Mapped['ObjectType'] = relationship('ObjectType', back_populates='TB_CODE_OBJECT')
    TB_MAP: Mapped[List['MapObject']] = relationship('MapObject', back_populates='TB_CODE_OBJECT')


class MapObject(Base):
    __tablename__ = 'TB_MAP'
    __table_args__ = (
        ForeignKeyConstraint(['FROM', 'TO'], ['TB_CODE_OBJECT.code', 'TB_CODE_OBJECT.code']),
    )

    CODE: Mapped[str] = mapped_column(Text, primary_key=True)
    FROM: Mapped[int] = mapped_column(Integer)
    TO: Mapped[str] = mapped_column(Text)
    MAP_TYPE: Mapped[int] = mapped_column(Integer)
    DB_OPERATION: Mapped[Optional[str]] = mapped_column(Text)
    INTEGRATION_STYLE: Mapped[Optional[str]] = mapped_column(Text)
    INTEGRATION_VOLUME: Mapped[Optional[int]] = mapped_column(Integer)
    START_TIME: Mapped[Optional[str]] = mapped_column(Text)
    DURATION: Mapped[Optional[int]] = mapped_column(Integer)
    LINE_TEXT: Mapped[Optional[int]] = mapped_column(Integer)
    LINE_NUMER: Mapped[Optional[int]] = mapped_column(Integer)

    TB_CODE_OBJECT: Mapped['CodeObject'] = relationship('CodeObject', back_populates='TB_MAP')
