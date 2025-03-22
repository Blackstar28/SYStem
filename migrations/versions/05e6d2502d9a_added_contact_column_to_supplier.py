"""Added contact column to supplier

Revision ID: 05e6d2502d9a
Revises: 58fb9824e6fb
Create Date: 2025-03-22 12:27:35.136403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '05e6d2502d9a'
down_revision = '58fb9824e6fb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('delivery_partner')
    op.drop_table('shipment')
    with op.batch_alter_table('supplier', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contact', sa.String(length=100), nullable=False))
        batch_op.alter_column('delivery_time',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.drop_constraint('uq_supplier_email', type_='unique')
        batch_op.drop_column('email')
        batch_op.drop_column('contact_info')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('supplier', schema=None) as batch_op:
        batch_op.add_column(sa.Column('contact_info', sa.VARCHAR(length=200), nullable=True))
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=120), nullable=False))
        batch_op.create_unique_constraint('uq_supplier_email', ['email'])
        batch_op.alter_column('delivery_time',
               existing_type=sa.String(length=50),
               type_=sa.INTEGER(),
               existing_nullable=False)
        batch_op.drop_column('contact')

    op.create_table('shipment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('product_id', sa.INTEGER(), nullable=False),
    sa.Column('supplier_id', sa.INTEGER(), nullable=False),
    sa.Column('quantity', sa.INTEGER(), nullable=False),
    sa.Column('status', sa.VARCHAR(length=50), nullable=True),
    sa.Column('estimated_delivery', sa.DATETIME(), nullable=True),
    sa.Column('actual_delivery', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('delivery_partner',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('contact_info', sa.VARCHAR(length=200), nullable=True),
    sa.Column('tracking_url', sa.VARCHAR(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
