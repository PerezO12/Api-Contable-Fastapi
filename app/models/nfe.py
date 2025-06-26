"""
NFe (Nota Fiscal Eletrônica) models for managing Brazilian electronic invoices.
Stores NFe data and links to the accounting system.
"""
import uuid
from decimal import Decimal
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, ForeignKey, Numeric, DateTime, Date, 
    Enum as SQLEnum, Integer, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.third_party import ThirdParty
    from app.models.product import Product


class NFeStatus(str, Enum):
    """Estados de procesamiento de NFe"""
    PENDING = "PENDING"           # Pendiente de procesamiento
    PROCESSING = "PROCESSING"     # En procesamiento
    PROCESSED = "PROCESSED"       # Procesada exitosamente
    ERROR = "ERROR"               # Error en el procesamiento
    CANCELLED = "CANCELLED"       # Cancelada
    UNLINKED = "UNLINKED"         # Desvinculada de factura eliminada


class NFeType(str, Enum):
    """Tipos de NFe"""
    ENTRADA = "0"     # Entrada (compra)
    SAIDA = "1"       # Saída (venta)


class NFe(Base):
    """
    Modelo para almacenar NFe (Notas Fiscais Eletrônicas)
    Mantiene la información original del XML y la vincula al sistema contable
    """
    __tablename__ = "nfes"

    # Información básica de la NFe
    chave_nfe: Mapped[str] = mapped_column(String(44), unique=True, nullable=False, index=True,
                                          comment="Chave de acceso de 44 dígitos")
    numero_nfe: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    serie: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Fechas
    data_emissao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                  comment="Data de emissão da NFe")
    data_saida_entrada: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True,
                                                                  comment="Data de saída/entrada")
    
    # Tipo e natureza
    tipo_nfe: Mapped[NFeType] = mapped_column(SQLEnum(NFeType), nullable=False,
                                             comment="0=Entrada, 1=Saída")
    natureza_operacao: Mapped[str] = mapped_column(String(500), nullable=False)
    finalidade_nfe: Mapped[str] = mapped_column(String(10), nullable=True,
                                               comment="Finalidade: 1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução")
    
    # Emitente
    cnpj_emitente: Mapped[str] = mapped_column(String(14), nullable=False, index=True)
    nome_emitente: Mapped[str] = mapped_column(String(500), nullable=False)
    fantasia_emitente: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Destinatário
    cnpj_destinatario: Mapped[Optional[str]] = mapped_column(String(14), nullable=True, index=True)
    cpf_destinatario: Mapped[Optional[str]] = mapped_column(String(11), nullable=True, index=True)
    nome_destinatario: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Totais
    valor_total_produtos: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_total_icms: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_total_ipi: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_total_pis: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_total_cofins: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_total_nfe: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Status de procesamiento
    status: Mapped[NFeStatus] = mapped_column(SQLEnum(NFeStatus), default=NFeStatus.PENDING, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # XML original
    xml_content: Mapped[str] = mapped_column(Text, nullable=False, comment="Contenido XML completo")
    xml_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True,
                                                        comment="Metadatos extraídos del XML")
    
    # Vinculación con sistema contable
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("invoices.id"), nullable=True,
                                                           comment="Factura generada")
    emitente_third_party_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("third_parties.id"), nullable=True,
                                                                         comment="Tercero emitente")
    destinatario_third_party_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("third_parties.id"), nullable=True,
                                                                             comment="Tercero destinatario")
    
    # Auditoría
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    processed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice")
    emitente_third_party: Mapped[Optional["ThirdParty"]] = relationship("ThirdParty", 
                                                                        foreign_keys=[emitente_third_party_id])
    destinatario_third_party: Mapped[Optional["ThirdParty"]] = relationship("ThirdParty", 
                                                                            foreign_keys=[destinatario_third_party_id])
    
    items: Mapped[List["NFeItem"]] = relationship("NFeItem", back_populates="nfe", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<NFe(chave='{self.chave_nfe}', numero='{self.numero_nfe}', status='{self.status}')>"


class NFeItem(Base):
    """
    Modelo para itens de NFe
    Detalhe de produtos/serviços na NFe
    """
    __tablename__ = "nfe_items"

    # Relação com NFe
    nfe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nfes.id"), nullable=False, index=True)
    
    # Sequência
    numero_item: Mapped[int] = mapped_column(Integer, nullable=False, comment="Número sequencial do item")
    
    # Produto
    codigo_produto: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao_produto: Mapped[str] = mapped_column(String(1000), nullable=False)
    ncm: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    cfop: Mapped[str] = mapped_column(String(4), nullable=False)
    unidade_comercial: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Quantidades e valores
    quantidade_comercial: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=4), nullable=False)
    valor_unitario_comercial: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=6), nullable=False)
    valor_total_produto: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    
    # Impostos
    valor_icms: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_ipi: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_pis: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    valor_cofins: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=0, nullable=False)
    
    # Vinculación con sistema contable
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("products.id"), nullable=True,
                                                           comment="Produto cadastrado no sistema")
    
    # Metadados do XML
    xml_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True,
                                                        comment="Metadados do item extraídos do XML")

    # Relationships
    nfe: Mapped["NFe"] = relationship("NFe", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")

    def __repr__(self) -> str:
        return f"<NFeItem(nfe_id='{self.nfe_id}', item={self.numero_item}, codigo='{self.codigo_produto}')>"
