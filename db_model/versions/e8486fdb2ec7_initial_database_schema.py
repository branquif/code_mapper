"""initial database schema

Revision ID: e8486fdb2ec7
Revises: 
Create Date: 2023-12-05 09:32:33.350607

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector



# revision identifiers, used by Alembic.
revision: str = 'e8486fdb2ec7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:


    op.create_table('TB_COMPONENT_TECH',
                    sa.Column('code', sa.Text(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('code')
                    )

    op.create_table('TB_COMPONENT_TYPE',
                    sa.Column('code', sa.Text(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('code')
                    )

    op.create_table('TB_DOMAIN',
                    sa.Column('code', sa.Text(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('parent_code', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['parent_code'], ['TB_DOMAIN.code'], name="fk_domain_parent_code"),
                    sa.PrimaryKeyConstraint('code')
                    )

    op.create_table('TB_OBJECT_TYPE',
                    sa.Column('code', sa.Text(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('code')
                    )

    op.create_table('TB_COMPONENT',
                    sa.Column('code', sa.Text(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('domain_code', sa.Text(), nullable=False),
                    sa.Column('type_code', sa.Text(), nullable=True),
                    sa.Column('parent_code', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['domain_code'], ['TB_DOMAIN.code'], name="fk_component_domain_code"),
                    sa.ForeignKeyConstraint(['parent_code'], ['TB_COMPONENT.code'], name="fk_component_parent_code"),
                    sa.ForeignKeyConstraint(['type_code'], ['TB_COMPONENT_TYPE.code'], name="fk_component_type_code"),
                    sa.PrimaryKeyConstraint('code')
                    )

    op.create_table('TB_CODE_OBJECT',
                    sa.Column('code', sa.Text(), nullable=False),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('type_code', sa.Text(), nullable=False),
                    sa.Column('source_file', sa.Text(), nullable=True),
                    sa.Column('component_code', sa.Text(), nullable=False),
                    sa.ForeignKeyConstraint(['component_code'], ['TB_COMPONENT.code'], name="fk_code_object_component_code"),
                    sa.ForeignKeyConstraint(['type_code'], ['TB_OBJECT_TYPE.code'], name="fk_code_object_type_code"),
                    sa.PrimaryKeyConstraint('code')
                    )

    op.create_table('TB_MAP',
                    sa.Column('from_code', sa.Text(), nullable=False),
                    sa.Column('to_code', sa.Text(), nullable=False),
                    sa.Column('map_type', sa.Text(), nullable=False),
                    sa.Column('db_operation', sa.Text(), nullable=True),
                    sa.Column('integration_style', sa.Text(), nullable=True),
                    sa.Column('integration_volume', sa.Text(), nullable=True),
                    sa.Column('start_time', sa.Text(), nullable=True),
                    sa.Column('duration', sa.Integer(), nullable=True),
                    sa.Column('line_text', sa.Text(), nullable=True),
                    sa.Column('line_number', sa.Integer(), nullable=True),
                    sa.Column('file_path', sa.Text(), nullable=True),
                    sa.Column('file_name', sa.Text(), nullable=True),
                    sa.ForeignKeyConstraint(['from_code'], ['TB_CODE_OBJECT.code'], name="fk_map_from_code"),
                    sa.ForeignKeyConstraint(['to_code'], ['TB_CODE_OBJECT.code'], name="fk_map_to_code"),
                    sa.PrimaryKeyConstraint('from_code', 'to_code')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    tables_to_drop = ['TB_MAP', 'TB_CODE_OBJECT', 'TB_COMPONENT', 'TB_OBJECT_TYPE', 'TB_DOMAIN', 'TB_COMPONENT_TYPE',
                      'TB_COMPONENT_TECH']

    for table in tables_to_drop:
        if table in inspector.get_table_names():
            op.drop_table(table)
