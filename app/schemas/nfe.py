"""
NFe schemas for API requests and responses.
"""
import uuid
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class NFeBulkImportConfig(BaseModel):
    """Configuração para importação em lote de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    # Configurações de processamento
    batch_size: int = Field(default=50, ge=1, le=100, description="Tamanho do lote para processamento")
    skip_duplicates: bool = Field(default=True, description="Pular NFe já processadas")
    
    # Criação automática de entidades
    auto_create_third_parties: bool = Field(default=True, description="Criar terceiros automaticamente")
    auto_create_products: bool = Field(default=True, description="Criar produtos automaticamente")
    
    # Criação de documentos contábeis
    create_invoices: bool = Field(default=True, description="Criar faturas a partir das NFe")
    create_journal_entries: bool = Field(default=False, description="Criar lançamentos contábeis")
    
    # Contas padrão para contabilização
    default_revenue_account: Optional[str] = Field(default=None, description="Conta padrão de receita (código)")
    default_expense_account: Optional[str] = Field(default=None, description="Conta padrão de despesa (código)")
    default_customer_account: Optional[str] = Field(default=None, description="Conta padrão de clientes (código)")
    default_supplier_account: Optional[str] = Field(default=None, description="Conta padrão de fornecedores (código)")
    
    # Diários padrão
    default_sales_journal: Optional[str] = Field(default=None, description="Diário padrão de vendas (código)")
    default_purchase_journal: Optional[str] = Field(default=None, description="Diário padrão de compras (código)")
    
    # Configurações adicionais
    currency_code: str = Field(default="BRL", description="Código da moeda")
    time_zone: str = Field(default="America/Sao_Paulo", description="Fuso horário")


class NFeBulkImportRequest(BaseModel):
    """Request para importação em lote de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    config: Optional[NFeBulkImportConfig] = Field(default=None, description="Configuração do processamento")


class NFeBulkImportError(BaseModel):
    """Erro no processamento de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    file_name: str = Field(description="Nome do arquivo com erro")
    error_message: str = Field(description="Mensagem de erro")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalhes adicionais do erro")
    timestamp: str = Field(description="Timestamp do erro")


class NFeBulkImportWarning(BaseModel):
    """Aviso no processamento de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    file_name: str = Field(description="Nome do arquivo")
    warning_message: str = Field(description="Mensagem de aviso")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detalhes adicionais")
    timestamp: str = Field(description="Timestamp do aviso")


class NFeBulkImportSummary(BaseModel):
    """Resumo do processamento em lote"""
    model_config = ConfigDict(from_attributes=True)
    
    total_files: int = Field(description="Total de arquivos processados")
    processed_successfully: int = Field(description="Arquivos processados com sucesso")
    processed_with_errors: int = Field(description="Arquivos processados com erros")
    skipped: int = Field(description="Arquivos ignorados")
    success_rate: float = Field(description="Taxa de sucesso (%)")
    processing_time_seconds: float = Field(description="Tempo de processamento em segundos")


class NFeBulkImportCreatedEntities(BaseModel):
    """Entidades criadas durante o processamento"""
    model_config = ConfigDict(from_attributes=True)
    
    invoices: int = Field(description="Número de faturas criadas")
    third_parties: int = Field(description="Número de terceiros criados")
    products: int = Field(description="Número de produtos criados")


class NFeBulkImportResponse(BaseModel):
    """Response da importação em lote de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    summary: NFeBulkImportSummary = Field(description="Resumo do processamento")
    created_entities: NFeBulkImportCreatedEntities = Field(description="Entidades criadas")
    errors: List[NFeBulkImportError] = Field(default_factory=list, description="Lista de erros")
    warnings: List[NFeBulkImportWarning] = Field(default_factory=list, description="Lista de avisos")


# Schemas para consulta de NFe individuais

class NFeItemResponse(BaseModel):
    """Response para item de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    numero_item: int
    codigo_produto: str
    descricao_produto: str
    ncm: Optional[str]
    cfop: str
    unidade_comercial: str
    quantidade_comercial: Decimal
    valor_unitario_comercial: Decimal
    valor_total_produto: Decimal
    valor_icms: Decimal
    valor_ipi: Decimal
    valor_pis: Decimal
    valor_cofins: Decimal
    product_id: Optional[uuid.UUID]


class NFeResponse(BaseModel):
    """Response para NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chave_nfe: str
    numero_nfe: str
    serie: str
    data_emissao: datetime
    data_saida_entrada: Optional[datetime]
    tipo_nfe: str
    natureza_operacao: str
    finalidade_nfe: Optional[str]
    
    cnpj_emitente: str
    nome_emitente: str
    fantasia_emitente: Optional[str]
    
    cnpj_destinatario: Optional[str]
    cpf_destinatario: Optional[str]
    nome_destinatario: str
    
    valor_total_produtos: Decimal
    valor_total_icms: Decimal
    valor_total_ipi: Decimal
    valor_total_pis: Decimal
    valor_total_cofins: Decimal
    valor_total_nfe: Decimal
    
    status: str
    error_message: Optional[str]
    
    invoice_id: Optional[uuid.UUID]
    emitente_third_party_id: Optional[uuid.UUID]
    destinatario_third_party_id: Optional[uuid.UUID]
    
    created_at: datetime
    processed_at: Optional[datetime]
    
    items: List[NFeItemResponse] = Field(default_factory=list)


class NFeListResponse(BaseModel):
    """Response para lista de NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chave_nfe: str
    numero_nfe: str
    serie: str
    data_emissao: datetime
    tipo_nfe: str
    nome_emitente: str
    nome_destinatario: str
    valor_total_nfe: Decimal
    status: str
    created_at: datetime


class NFeSearchParams(BaseModel):
    """Parâmetros de busca para NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    chave_nfe: Optional[str] = Field(default=None, description="Chave da NFe")
    numero_nfe: Optional[str] = Field(default=None, description="Número da NFe")
    cnpj_emitente: Optional[str] = Field(default=None, description="CNPJ do emitente")
    nome_emitente: Optional[str] = Field(default=None, description="Nome do emitente")
    status: Optional[str] = Field(default=None, description="Status da NFe")
    data_emissao_inicio: Optional[datetime] = Field(default=None, description="Data início")
    data_emissao_fim: Optional[datetime] = Field(default=None, description="Data fim")
    
    # Paginação
    page: int = Field(default=1, ge=1, description="Página")
    page_size: int = Field(default=20, ge=1, le=100, description="Itens por página")


class NFePaginatedResponse(BaseModel):
    """Response paginada para NFe"""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[NFeListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
