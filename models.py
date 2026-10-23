from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    versions: Mapped[list['DocumentVersion']] = relationship(back_populates='document', cascade='all, delete-orphan')

class DocumentVersion(Base):
    __tablename__ = 'document_versions'
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id'))
    version_number: Mapped[int] = mapped_column(Integer)
    source_name: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    document: Mapped[Document] = relationship(back_populates='versions')
    nodes: Mapped[list['Node']] = relationship(back_populates='version', cascade='all, delete-orphan')
    __table_args__ = (UniqueConstraint('document_id','version_number'),)

class Node(Base):
    __tablename__ = 'nodes'
    id: Mapped[int] = mapped_column(primary_key=True)
    logical_key: Mapped[str] = mapped_column(String(500))
    version_id: Mapped[int] = mapped_column(ForeignKey('document_versions.id'))
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey('nodes.id'), nullable=True)
    heading: Mapped[str] = mapped_column(String(500))
    level: Mapped[int] = mapped_column(Integer)
    ordinal: Mapped[int] = mapped_column(Integer)
    body_text: Mapped[str] = mapped_column(Text, default='')
    content_hash: Mapped[str] = mapped_column(String(64))
    node_type: Mapped[str] = mapped_column(String(30), default='section')
    version: Mapped[DocumentVersion] = relationship(back_populates='nodes')
    children: Mapped[list['Node']] = relationship(back_populates='parent', cascade='all, delete-orphan')
    parent: Mapped[Optional['Node']] = relationship(back_populates='children', remote_side=[id])

class Selection(Base):
    __tablename__ = 'selections'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    items: Mapped[list['SelectionItem']] = relationship(cascade='all, delete-orphan')

class SelectionItem(Base):
    __tablename__ = 'selection_items'
    id: Mapped[int] = mapped_column(primary_key=True)
    selection_id: Mapped[int] = mapped_column(ForeignKey('selections.id'))
    node_id: Mapped[int] = mapped_column(ForeignKey('nodes.id'))
    version_id: Mapped[int] = mapped_column(ForeignKey('document_versions.id'))
    content_hash: Mapped[str] = mapped_column(String(64))

class Generation(Base):
    __tablename__ = 'generations'
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    selection_id: Mapped[int] = mapped_column(ForeignKey('selections.id'))
    prompt_version: Mapped[str] = mapped_column(String(30), default='v1')
    status: Mapped[str] = mapped_column(String(30), default='complete')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    input_snapshot: Mapped[str] = mapped_column(Text)
    output_json: Mapped[str] = mapped_column(Text)
    stale: Mapped[bool] = mapped_column(Boolean, default=False)
