"""
NFe API endpoints for bulk import and management of Brazilian electronic invoices.
"""
import uuid
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Form
from fastapi import status as http_status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.api.deps import get_current_user, get_db
from app.database import get_db as get_sync_db
from app.models.user import User
from app.models.nfe import NFe, NFeStatus
from app.schemas.nfe import (
    NFeBulkImportRequest,
    NFeBulkImportResponse,
    NFeBulkImportConfig,
    NFeResponse,
    NFeListResponse,
    NFeSearchParams,
    NFePaginatedResponse,
    NFeItemResponse
)
from app.services.nfe_bulk_import_service import NFeBulkImportService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/bulk-import", response_model=NFeBulkImportResponse)
async def bulk_import_nfe(
    files: List[UploadFile] = File(..., description="Arquivos XML ou ZIP (máximo 1000)"),
    config: str = Form(None, description="Configuração JSON para importação"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Importação em lote de NFe (Notas Fiscais Eletrônicas)
    
    Aceita até 1000 arquivos XML ou ZIP contendo XMLs de NFe.
    
    **Funcionalidades:**
    - Parse automático de XMLs de NFe
    - Validação e normalização de dados
    - Criação automática de terceiros e produtos
    - Geração de faturas e lançamentos contábeis
    - Processamento em lotes para otimização
    - Configuração flexível de contas e diários padrão
    
    **Configurações disponíveis:**
    - `auto_create_third_parties`: Criar terceiros automaticamente
    - `auto_create_products`: Criar produtos automaticamente
    - `create_invoices`: Criar faturas a partir das NFe
    - `create_journal_entries`: Criar lançamentos contábeis
    - `default_revenue_account`: Conta padrão de receita
    - `default_customer_account`: Conta padrão de clientes
    - `skip_duplicates`: Pular NFe já processadas
    
    **Tipos de arquivo aceitos:**
    - XML individual
    - ZIP contendo múltiplos XMLs
    
    **Resposta:**
    - Resumo detalhado do processamento
    - Lista de erros e avisos
    - Contadores de entidades criadas
    - Tempo de processamento
    """
    try:
        # Validar número de arquivos
        if len(files) == 0:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Pelo menos um arquivo deve ser enviado"
            )
        
        if len(files) > 1000:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Máximo de 1000 arquivos permitidos por lote"
            )
        
        # Validar tipos de arquivo
        allowed_extensions = ['.xml', '.zip']
        for file in files:
            if not file.filename:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail="Nome do arquivo é obrigatório"
                )
            
            file_ext = '.' + file.filename.split('.')[-1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Tipo de arquivo não suportado: {file.filename}. Aceitos: XML, ZIP"
                )
        
        # Configuração padrão se não fornecida
        if config is None:
            config = NFeBulkImportConfig()
        
        # Parsear configuração se fornecida
        config_dict = {}
        if config:
            try:
                config_dict = json.loads(config)
                # Validar configuração usando o schema
                config_obj = NFeBulkImportConfig(**config_dict)
                config_dict = config_obj.model_dump()
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Configuração JSON inválida: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Erro na validação da configuração: {str(e)}"
                )
        
        # Inicializar serviço de importação
        import_service = NFeBulkImportService(db)
        
        # Processar importação
        logger.info(f"Iniciando importação de {len(files)} arquivo(s) pelo usuário {current_user.email}")
        
        result = await import_service.process_bulk_import(
            files=files,
            user_id=current_user.id,
            config=config_dict
        )
        
        logger.info(f"Importação concluída: {result.processed_successfully} sucessos, {result.processed_with_errors} erros")
        
        # Converter resultado para response schema
        response_data = result.to_dict()
        
        return NFeBulkImportResponse(
            summary=response_data['summary'],
            created_entities=response_data['created_entities'],
            errors=response_data['errors'],
            warnings=response_data['warnings']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na importação em lote: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no processamento: {str(e)}"
        )


@router.get("/", response_model=NFePaginatedResponse)
async def list_nfes(
    chave_nfe: Optional[str] = Query(None, description="Filtrar por chave NFe"),
    numero_nfe: Optional[str] = Query(None, description="Filtrar por número NFe"),
    cnpj_emitente: Optional[str] = Query(None, description="Filtrar por CNPJ emitente"),
    nome_emitente: Optional[str] = Query(None, description="Filtrar por nome emitente"),
    nfe_status: Optional[str] = Query(None, description="Filtrar por status"),
    page: int = Query(1, ge=1, description="Página"),
    page_size: int = Query(20, ge=1, le=100, description="Itens por página"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Lista NFe com filtros e paginação
    
    **Filtros disponíveis:**
    - Chave NFe (busca exata)
    - Número NFe (busca parcial)
    - CNPJ emitente (busca exata)
    - Nome emitente (busca parcial)
    - Status (PENDING, PROCESSING, PROCESSED, ERROR, CANCELLED)
    
    **Paginação:**
    - Máximo 100 itens por página
    - Ordenação por data de criação (mais recentes primeiro)
    """
    try:
        # Construir query base
        query = db.query(NFe)
        
        # Aplicar filtros
        filters = []
        
        if chave_nfe:
            filters.append(NFe.chave_nfe == chave_nfe)
        
        if numero_nfe:
            filters.append(NFe.numero_nfe.ilike(f"%{numero_nfe}%"))
        
        if cnpj_emitente:
            filters.append(NFe.cnpj_emitente == cnpj_emitente)
        
        if nome_emitente:
            filters.append(NFe.nome_emitente.ilike(f"%{nome_emitente}%"))
        
        if nfe_status:
            try:
                status_enum = NFeStatus(nfe_status)
                filters.append(NFe.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Status inválido: {nfe_status}"
                )
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Contar total
        total = query.count()
        
        # Aplicar ordenação e paginação
        offset = (page - 1) * page_size
        nfes = query.order_by(NFe.created_at.desc()).offset(offset).limit(page_size).all()
        
        # Calcular total de páginas
        total_pages = (total + page_size - 1) // page_size
        
        # Converter para response
        nfe_items = [
            NFeListResponse(
                id=nfe.id,
                chave_nfe=nfe.chave_nfe,
                numero_nfe=nfe.numero_nfe,
                serie=nfe.serie,
                data_emissao=nfe.data_emissao,
                tipo_nfe=nfe.tipo_nfe.value,
                nome_emitente=nfe.nome_emitente,
                nome_destinatario=nfe.nome_destinatario,
                valor_total_nfe=nfe.valor_total_nfe,
                status=nfe.status.value,
                created_at=nfe.created_at
            )
            for nfe in nfes
        ]
        
        return NFePaginatedResponse(
            items=nfe_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar NFe: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar NFe"
        )


@router.get("/{nfe_id}", response_model=NFeResponse)
async def get_nfe(
    nfe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Obtém detalhes de uma NFe específica
    
    **Inclui:**
    - Dados completos da NFe
    - Lista de itens/produtos
    - Informações de vinculação com faturas
    - Status de processamento
    """
    try:
        nfe = db.query(NFe).options(
            joinedload(NFe.items)
        ).filter(NFe.id == nfe_id).first()
        
        if not nfe:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="NFe não encontrada"
            )
        
        # Converter itens
        items = [
            NFeItemResponse(
                id=item.id,
                numero_item=item.numero_item,
                codigo_produto=item.codigo_produto,
                descricao_produto=item.descricao_produto,
                ncm=item.ncm,
                cfop=item.cfop,
                unidade_comercial=item.unidade_comercial,
                quantidade_comercial=item.quantidade_comercial,
                valor_unitario_comercial=item.valor_unitario_comercial,
                valor_total_produto=item.valor_total_produto,
                valor_icms=item.valor_icms,
                valor_ipi=item.valor_ipi,
                valor_pis=item.valor_pis,
                valor_cofins=item.valor_cofins,
                product_id=item.product_id
            )
            for item in nfe.items
        ]
        
        return NFeResponse(
            id=nfe.id,
            chave_nfe=nfe.chave_nfe,
            numero_nfe=nfe.numero_nfe,
            serie=nfe.serie,
            data_emissao=nfe.data_emissao,
            data_saida_entrada=nfe.data_saida_entrada,
            tipo_nfe=nfe.tipo_nfe.value,
            natureza_operacao=nfe.natureza_operacao,
            finalidade_nfe=nfe.finalidade_nfe,
            cnpj_emitente=nfe.cnpj_emitente,
            nome_emitente=nfe.nome_emitente,
            fantasia_emitente=nfe.fantasia_emitente,
            cnpj_destinatario=nfe.cnpj_destinatario,
            cpf_destinatario=nfe.cpf_destinatario,
            nome_destinatario=nfe.nome_destinatario,
            valor_total_produtos=nfe.valor_total_produtos,
            valor_total_icms=nfe.valor_total_icms,
            valor_total_ipi=nfe.valor_total_ipi,
            valor_total_pis=nfe.valor_total_pis,
            valor_total_cofins=nfe.valor_total_cofins,
            valor_total_nfe=nfe.valor_total_nfe,
            status=nfe.status.value,
            error_message=nfe.error_message,
            invoice_id=nfe.invoice_id,
            emitente_third_party_id=nfe.emitente_third_party_id,
            destinatario_third_party_id=nfe.destinatario_third_party_id,
            created_at=nfe.created_at,
            processed_at=nfe.processed_at,
            items=items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar NFe {nfe_id}: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar NFe"
        )


@router.delete("/{nfe_id}")
async def delete_nfe(
    nfe_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Remove uma NFe do sistema
    
    **Atenção:** Esta operação é irreversível.
    Se a NFe gerou fatura, a fatura deve ser removida separadamente.
    """
    try:
        nfe = db.query(NFe).filter(NFe.id == nfe_id).first()
        
        if not nfe:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="NFe não encontrada"
            )
        
        # Verificar se possui fatura vinculada
        if nfe.invoice_id:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="NFe possui fatura vinculada. Remova a fatura primeiro."
            )
        
        db.delete(nfe)
        db.commit()
        
        logger.info(f"NFe {nfe.chave_nfe} removida pelo usuário {current_user.email}")
        
        return {"message": "NFe removida com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao remover NFe {nfe_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao remover NFe"
        )


@router.post("/{nfe_id}/reprocess")
async def reprocess_nfe(
    nfe_id: uuid.UUID,
    config: Optional[NFeBulkImportConfig] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    """
    Reprocessa uma NFe com erro
    
    Útil para tentar novamente o processamento de NFe que falharam
    ou para aplicar novas configurações.
    """
    try:
        nfe = db.query(NFe).filter(NFe.id == nfe_id).first()
        
        if not nfe:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="NFe não encontrada"
            )
        
        if nfe.status == NFeStatus.PROCESSED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="NFe já foi processada com sucesso"
            )
        
        # Configuração padrão se não fornecida
        if config is None:
            config = NFeBulkImportConfig()
        
        # Criar arquivo temporário com o XML
        import tempfile
        import os
        from fastapi import UploadFile
        import io
        
        xml_bytes = nfe.xml_content.encode('utf-8')
        xml_file = UploadFile(
            filename=f"{nfe.chave_nfe}.xml",
            file=io.BytesIO(xml_bytes)
        )
        
        # Reprocessar
        import_service = NFeBulkImportService(db)
        result = await import_service.process_bulk_import(
            files=[xml_file],
            user_id=current_user.id,
            config=config.model_dump()
        )
        
        response_data = result.to_dict()
        
        return {
            "message": "NFe reprocessada",
            "result": response_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reprocessar NFe {nfe_id}: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao reprocessar NFe"
        )
