from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Index, Integer, Table, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

class Base(DeclarativeBase):
    pass


class ComponentTech(Base):
    __tablename__ = 'TB_COMPONENT_TECH'

    code: Mapped[str] = Column(Text, primary_key=True)
    name: Mapped[str] = Column(Text)


class ComponentType(Base):
    __tablename__ = 'TB_COMPONENT_TYPE'

    code: Mapped[str] = Column(Text, primary_key=True)
    name: Mapped[str] = Column(Text)

    components: Mapped[list['Component']] = relationship('Component', back_populates='component_type')


class Domain(Base):
    __tablename__ = 'TB_DOMAIN'

    code: Mapped[str] = Column(Text, primary_key=True)
    name: Mapped[str] = Column(Text)
    description: Mapped[str | None] = Column(Text)
    parent_code: Mapped[str | None] = Column(ForeignKey('TB_DOMAIN.code'))

    children: Mapped['Domain'] = relationship('Domain', remote_side=[code], back_populates='parent')
    parent: Mapped[list['Domain']] = relationship('Domain', remote_side=[parent_code], back_populates='children')
    components: Mapped[list['Component']] = relationship('Component', back_populates='domain')


class ObjectType(Base):
    __tablename__ = 'TB_OBJECT_TYPE'

    code: Mapped[str | None] = Column(Text, primary_key=True)
    name: Mapped[str | None] = Column(Text)

    code_objects: Mapped[list['CodeObject']] = relationship('CodeObject', back_populates='object_type')


class Component(Base):
    __tablename__ = 'TB_COMPONENT'

    code: Mapped[str | None] = Column(Text, primary_key=True)
    name: Mapped[str | None] = Column(Text)
    domain_code: Mapped[str | None] = Column(ForeignKey('TB_DOMAIN.code'))
    type_code: Mapped[str | None] = Column(ForeignKey('TB_COMPONENT_TYPE.code'))
    parent_code: Mapped[str | None] = Column(ForeignKey('TB_COMPONENT.code'))

    parent: Mapped['Component'] = relationship('Component', remote_side=[code], back_populates='children')
    children: Mapped[list['Component']] = relationship('Component', remote_side=[parent_code], back_populates='parent')
    domain: Mapped['Domain'] = relationship('Domain', back_populates='components')
    component_type: Mapped['ComponentType'] = relationship('ComponentType', back_populates='components')
    code_objects: Mapped[list['CodeObject']] = relationship('CodeObject', back_populates='component')


class CodeObject(Base):
    __tablename__ = 'TB_CODE_OBJECT'

    code: Mapped[str] = Column(Text, primary_key=True)
    name: Mapped[str] = Column(Text)
    object_type_code: Mapped[str] = Column(ForeignKey('TB_OBJECT_TYPE.code'))
    component_code: Mapped[str] = Column(ForeignKey('TB_COMPONENT.code'))
    source_file: Mapped[str | None] = Column(Text)

    component: Mapped['Component'] = relationship('Component', back_populates='code_objects')
    object_type: Mapped['ObjectType'] = relationship('ObjectType', back_populates='code_objects')
    object_maps: Mapped[list['ObjectMap']] = relationship('ObjectMap', back_populates='code_object')


class ObjectMap(Base):
    __tablename__ = 'TB_MAP'
    __table_args__ = (
        ForeignKeyConstraint(['from_code'], ['TB_CODE_OBJECT.code'], name='fk_map_from'),
        ForeignKeyConstraint(['to_code'], ['TB_CODE_OBJECT.code'], name='fk_map_to'),

        Index('idx_map', 'from_code', 'to_code')
    )

    code: Mapped[str] = Column(Text, primary_key=True)
    from_code: Mapped[int] = Column(Integer)
    to_code: Mapped[str] = Column(Text)
    map_type: Mapped[str] = Column(Text)
    db_operation: Mapped[str | None] = Column(Text)
    integration_style: Mapped[str | None] = Column(Text)
    integration_volume: Mapped[int | None] = Column(Integer)
    start_time: Mapped[str | None] = Column(Text)
    duration: Mapped[int | None] = Column(Integer)
    line_text: Mapped[int | None] = Column(Integer)
    line_number: Mapped[int | None] = Column(Integer, primary_key=True)
    file_path: Mapped[str | None] = Column(Text, primary_key=True)
    file_name: Mapped[str | None] = Column(Text, primary_key=True)

    code_object: Mapped['CodeObject'] = relationship('CodeObject', back_populates='object_maps')
