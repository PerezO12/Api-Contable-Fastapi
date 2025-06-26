"""
NFe Bulk Import Service for processing multiple NFe XML files in batch.
Handles validation, processing, and invoice creation for up to 1000 NFe files.
"""
import uuid
import asyncio
import logging
from pathlib import Path
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import tempfile
import zipfile
import os

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile

from app.models.nfe import NFe, NFeItem, NFeStatus, NFeType
from app.models.invoice import Invoice, InvoiceType, InvoiceStatus, InvoiceLine
from app.models.third_party import ThirdParty, ThirdPartyType
from app.models.product import Product
from app.models.journal import Journal
from app.models.journal_entry import JournalEntry, JournalEntryLine, JournalEntryStatus
from app.models.account import Account

from app.services.nfe_xml_parser import NFeXMLParser
from app.services.nfe_validation_service import NFeValidationService
from app.services.invoice_service import InvoiceService

logger = logging.getLogger(__name__)


class NFeBulkImportResult:
    """Resultado do processamento em lote de NFe"""
    
    def __init__(self):
        self.total_files = 0
        self.processed_successfully = 0
        self.processed_with_errors = 0
        self.skipped = 0
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.created_invoices: List[uuid.UUID] = []
        self.created_third_parties: List[uuid.UUID] = []
        self.created_products: List[uuid.UUID] = []
        self.processing_time_seconds: float = 0
        
    def add_error(self, file_name: str, error_message: str, details: Optional[Dict] = None):
        """Adiciona erro ao resultado"""
        self.errors.append({
            'file_name': file_name,
            'error_message': error_message,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def add_warning(self, file_name: str, warning_message: str, details: Optional[Dict] = None):
        """Adiciona aviso ao resultado"""
        self.warnings.append({
            'file_name': file_name,
            'warning_message': warning_message,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte resultado para dicionário"""
        return {
            'summary': {
                'total_files': self.total_files,
                'processed_successfully': self.processed_successfully,
                'processed_with_errors': self.processed_with_errors,
                'skipped': self.skipped,
                'success_rate': round((self.processed_successfully / max(self.total_files, 1)) * 100, 2),
                'processing_time_seconds': self.processing_time_seconds
            },
            'created_entities': {
                'invoices': len(self.created_invoices),
                'third_parties': len(self.created_third_parties),
                'products': len(self.created_products)
            },
            'errors': self.errors,
            'warnings': self.warnings
        }


class NFeBulkImportService:
    """Serviço para importação em lote de NFe"""
    
    def __init__(self, db: Session):
        self.db = db
        self.xml_parser = NFeXMLParser()
        self.validation_service = NFeValidationService(db)
        self.invoice_service = InvoiceService(db)
        
    async def process_bulk_import(
        self,
        files: List[UploadFile],
        user_id: uuid.UUID,
        config: Optional[Dict[str, Any]] = None
    ) -> NFeBulkImportResult:
        """
        Processa importação em lote de arquivos NFe
        
        Args:
            files: Lista de arquivos XML ou ZIP
            user_id: ID do usuário
            config: Configuração do processamento
            
        Returns:
            Resultado do processamento
        """
        start_time = datetime.utcnow()
        result = NFeBulkImportResult()
        config = config or {}
        
        try:
            # Validar limites
            if len(files) > 1000:
                raise ValueError("Máximo de 1000 arquivos permitidos por lote")
            
            # Extrair arquivos XML
            xml_files = await self._extract_xml_files(files)
            result.total_files = len(xml_files)
            
            if result.total_files == 0:
                raise ValueError("Nenhum arquivo XML válido encontrado")
            
            # Processar arquivos em lotes menores para otimizar memória
            batch_size = config.get('batch_size', 50)
            
            for i in range(0, len(xml_files), batch_size):
                batch_files = xml_files[i:i + batch_size]
                await self._process_batch(batch_files, user_id, config, result)
                
                # Commit em lotes para evitar transações muito longas
                try:
                    self.db.commit()
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Erro ao fazer commit do lote {i//batch_size + 1}: {str(e)}")
                    for file_info in batch_files:
                        result.add_error(file_info['name'], f"Erro na transação: {str(e)}")
                        result.processed_with_errors += 1
            
        except Exception as e:
            logger.error(f"Erro no processamento em lote: {str(e)}")
            result.add_error("BATCH_PROCESSING", str(e))
            self.db.rollback()
        
        finally:
            # Calcular tempo de processamento
            end_time = datetime.utcnow()
            result.processing_time_seconds = (end_time - start_time).total_seconds()
        
        return result
    
    async def _extract_xml_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Extrai arquivos XML de uploads (pode incluir ZIPs)"""
        xml_files = []
        
        for file in files:
            try:
                if not file.filename:
                    continue
                    
                content = await file.read()
                await file.seek(0)  # Reset para próxima leitura se necessário
                
                if file.filename.lower().endswith('.zip'):
                    # Extrair XMLs do ZIP
                    extracted = await self._extract_from_zip(content, file.filename)
                    xml_files.extend(extracted)
                    
                elif file.filename.lower().endswith('.xml'):
                    # Arquivo XML direto
                    xml_files.append({
                        'name': file.filename,
                        'content': content.decode('utf-8'),
                        'size': len(content)
                    })
                else:
                    logger.warning(f"Arquivo ignorado (formato não suportado): {file.filename}")
                    
            except Exception as e:
                logger.error(f"Erro ao processar arquivo {file.filename}: {str(e)}")
        
        return xml_files
    
    async def _extract_from_zip(self, zip_content: bytes, zip_name: str) -> List[Dict[str, Any]]:
        """Extrai arquivos XML de um ZIP"""
        xml_files = []
        
        try:
            logger.info(f"Processando ZIP: {zip_name}, tamanho: {len(zip_content)} bytes")
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(zip_content)
                temp_file.flush()
                
                logger.info(f"Arquivo temporário criado: {temp_file.name}")
                
                with zipfile.ZipFile(temp_file.name, 'r') as zip_file:
                    file_list = zip_file.infolist()
                    xml_file_list = [f for f in file_list if f.filename.lower().endswith('.xml')]
                    
                    logger.info(f"Arquivos no ZIP: {len(file_list)}, XMLs encontrados: {len(xml_file_list)}")
                    
                    for file_info in xml_file_list:
                        try:
                            xml_content = zip_file.read(file_info)
                            xml_text = xml_content.decode('utf-8')
                            
                            xml_files.append({
                                'name': f"{zip_name}:{file_info.filename}",
                                'content': xml_text,
                                'size': file_info.file_size
                            })
                            
                            logger.debug(f"Extraído com sucesso: {file_info.filename}")
                            
                        except Exception as e:
                            logger.error(f"Erro ao extrair {file_info.filename} de {zip_name}: {str(e)}")
            
            # Limpar arquivo temporário
            try:
                import os
                os.unlink(temp_file.name)
            except:
                pass
                            
        except zipfile.BadZipFile as e:
            logger.error(f"Arquivo ZIP inválido: {zip_name} - {str(e)}")
        except Exception as e:
            logger.error(f"Erro ao processar ZIP {zip_name}: {str(e)}")
        
        logger.info(f"Total de XMLs extraídos do ZIP {zip_name}: {len(xml_files)}")
        return xml_files
    
    async def _process_batch(
        self, 
        xml_files: List[Dict[str, Any]], 
        user_id: uuid.UUID,
        config: Dict[str, Any],
        result: NFeBulkImportResult
    ) -> None:
        """Processa um lote de arquivos XML"""
        
        for file_info in xml_files:
            # Processar cada arquivo em sua própria sub-transação
            savepoint = self.db.begin_nested()
            try:
                await self._process_single_nfe(file_info, user_id, config, result)
                savepoint.commit()
                result.processed_successfully += 1
                
            except Exception as e:
                savepoint.rollback()
                logger.error(f"Erro ao processar {file_info['name']}: {str(e)}")
                result.add_error(file_info['name'], str(e))
                result.processed_with_errors += 1
    
    async def _process_single_nfe(
        self,
        file_info: Dict[str, Any],
        user_id: uuid.UUID,
        config: Dict[str, Any],
        result: NFeBulkImportResult
    ) -> None:
        """Processa uma única NFe"""
        
        file_name = file_info['name']
        xml_content = file_info['content']
        
        # 1. Parse do XML
        try:
            nfe_data = self.xml_parser.parse_xml_content(xml_content)
        except Exception as e:
            raise ValueError(f"Erro no parse do XML: {str(e)}")
        
        # 2. Verificar se já foi processada
        chave_nfe = nfe_data['chave_nfe']
        if not self.validation_service.validate_nfe_uniqueness(chave_nfe):
            if config.get('skip_duplicates', True):
                result.skipped += 1
                result.add_warning(file_name, f"NFe já processada: {chave_nfe}")
                return
            else:
                raise ValueError(f"NFe já processada: {chave_nfe}")
        
        # 3. Validar e normalizar dados
        try:
            validated_data = self.validation_service.validate_and_normalize_nfe_data(
                nfe_data, user_id, config
            )
        except Exception as e:
            raise ValueError(f"Erro na validação: {str(e)}")
        
        # 4. Criar/atualizar terceiros e produtos se necessário
        self._handle_entity_creation(validated_data, result)
        
        # 5. Criar NFe
        nfe = self._create_nfe_record(validated_data, user_id)
        
        # 6. Criar fatura se configurado
        if config.get('create_invoices', True):
            invoice = await self._create_invoice_from_nfe(nfe, validated_data, user_id, config)
            if invoice:
                result.created_invoices.append(invoice.id)
                
                # 7. Criar lançamento contábil se configurado
                if config.get('create_journal_entries', True):
                    # Por enquanto, apenas logar a intenção
                    logger.info(f"Lançamento contábil seria criado para fatura {invoice.number}")
    
    def _handle_entity_creation(self, validated_data: Dict[str, Any], result: NFeBulkImportResult):
        """Trata criação de entidades (terceiros e produtos)"""
        
        # Coletar terceiros criados
        emitente_data = validated_data.get('emitente_data', {})
        destinatario_data = validated_data.get('destinatario_data', {})
        
        if emitente_data.get('is_new'):
            result.created_third_parties.append(emitente_data['third_party_id'])
            
        if destinatario_data.get('is_new'):
            result.created_third_parties.append(destinatario_data['third_party_id'])
        
        # Coletar produtos criados
        for item_data in validated_data.get('items_data', []):
            product_data = item_data.get('product_data', {})
            if product_data.get('is_new'):
                result.created_products.append(product_data['product_id'])
    
    def _create_nfe_record(self, validated_data: Dict[str, Any], user_id: uuid.UUID) -> NFe:
        """Cria registro da NFe no banco"""
        
        emitente_data = validated_data.get('emitente_data', {})
        destinatario_data = validated_data.get('destinatario_data', {})
        
        nfe = NFe(
            chave_nfe=validated_data['chave_nfe'],
            numero_nfe=validated_data['numero_nfe'],
            serie=validated_data['serie'],
            data_emissao=validated_data['data_emissao'],
            data_saida_entrada=validated_data.get('data_saida_entrada'),
            tipo_nfe=NFeType(validated_data['tipo_nfe']),
            natureza_operacao=validated_data['natureza_operacao'],
            finalidade_nfe=validated_data.get('finalidade_nfe'),
            
            cnpj_emitente=validated_data['cnpj_emitente'],
            nome_emitente=validated_data['nome_emitente'],
            fantasia_emitente=validated_data.get('fantasia_emitente'),
            
            cnpj_destinatario=validated_data.get('cnpj_destinatario'),
            cpf_destinatario=validated_data.get('cpf_destinatario'),
            nome_destinatario=validated_data['nome_destinatario'],
            
            valor_total_produtos=validated_data['valor_total_produtos'],
            valor_total_icms=validated_data['valor_total_icms'],
            valor_total_ipi=validated_data['valor_total_ipi'],
            valor_total_pis=validated_data['valor_total_pis'],
            valor_total_cofins=validated_data['valor_total_cofins'],
            valor_total_nfe=validated_data['valor_total_nfe'],
            
            xml_content=validated_data['xml_content'],
            xml_metadata=validated_data.get('xml_metadata'),
            
            emitente_third_party_id=emitente_data.get('third_party_id'),
            destinatario_third_party_id=destinatario_data.get('third_party_id'),
            
            status=NFeStatus.PROCESSING,
            created_by_id=user_id
        )
        
        #self.db.add(nfe)
        #self.db.flush()  # Para obter ID
        
        #todo: comentado
        # Criar itens
        for item_data in validated_data.get('items_data', []):
            nfe_item = NFeItem(
                nfe_id=nfe.id,
                numero_item=item_data['numero_item'],
                codigo_produto=item_data['codigo_produto'],
                descricao_produto=item_data['descricao_produto'],
                ncm=item_data.get('ncm'),
                cfop=item_data['cfop'],
                unidade_comercial=item_data['unidade_comercial'],
                quantidade_comercial=item_data['quantidade_comercial'],
                valor_unitario_comercial=item_data['valor_unitario_comercial'],
                valor_total_produto=item_data['valor_total_produto'],
                valor_icms=item_data['valor_icms'],
                valor_ipi=item_data['valor_ipi'],
                valor_pis=item_data['valor_pis'],
                valor_cofins=item_data['valor_cofins'],
                product_id=item_data.get('product_data', {}).get('product_id'),
                xml_metadata=item_data.get('xml_metadata')
            )
            #self.db.add(nfe_item) 
        
        return nfe
    
    async def _create_invoice_from_nfe(
        self,
        nfe: NFe,
        validated_data: Dict[str, Any],
        user_id: uuid.UUID,
        config: Dict[str, Any]
    ) -> Optional[Invoice]:
        """Cria fatura a partir da NFe"""
        
        try:
            # Determinar tipo de fatura
            invoice_type = self._determine_invoice_type(nfe.tipo_nfe, config)
            
            # Obter terceiro principal (cliente ou fornecedor)
            third_party_id = self._get_main_third_party_id(nfe, invoice_type)
            if not third_party_id:
                logger.warning(f"NFe {nfe.chave_nfe}: Terceiro não encontrado para criação de fatura")
                return None
            
            # Obter diário padrão
            journal = self._get_default_journal(invoice_type, config)
            
            # Gerar número de fatura
            invoice_number = self._generate_invoice_number(nfe, journal)
            
            # Criar fatura
            invoice = Invoice(
                number=invoice_number,
                external_reference=f"NFe-{nfe.numero_nfe}",
                invoice_type=invoice_type,
                status=InvoiceStatus.DRAFT,
                third_party_id=third_party_id,
                invoice_date=nfe.data_emissao.date(),
                due_date=nfe.data_emissao.date(),  # Ajustar conforme regras de negócio
                subtotal=nfe.valor_total_produtos,
                tax_amount=nfe.valor_total_icms + nfe.valor_total_ipi + nfe.valor_total_pis + nfe.valor_total_cofins,
                total_amount=nfe.valor_total_nfe,
                outstanding_amount=nfe.valor_total_nfe,
                journal_id=journal.id if journal else None,
                description=f"NFe {nfe.numero_nfe} - {nfe.natureza_operacao}",
                created_by_id=user_id
            )
            
            self.db.add(invoice)
            self.db.flush()
            
            # Criar linhas da fatura
            await self._create_invoice_lines(invoice, nfe, config, user_id, validated_data)
            
            # Atualizar NFe com referência à fatura
            nfe.invoice_id = invoice.id
            nfe.status = NFeStatus.PROCESSED
            nfe.processed_by_id = user_id
            nfe.processed_at = datetime.utcnow()
            
            return invoice
            
        except Exception as e:
            logger.error(f"Erro ao criar fatura para NFe {nfe.chave_nfe}: {str(e)}")
            nfe.status = NFeStatus.ERROR
            nfe.error_message = f"Erro na criação da fatura: {str(e)}"
            raise
    
    def _determine_invoice_type(self, nfe_type: NFeType, config: Dict[str, Any]) -> InvoiceType:
        """Determina tipo de fatura baseado no tipo de NFe"""
        if nfe_type == NFeType.ENTRADA:
            return InvoiceType.SUPPLIER_INVOICE
        else:
            return InvoiceType.CUSTOMER_INVOICE
    
    def _get_main_third_party_id(self, nfe: NFe, invoice_type: InvoiceType) -> Optional[uuid.UUID]:
        """Obtém ID do terceiro principal para a fatura"""
        if invoice_type == InvoiceType.SUPPLIER_INVOICE:
            return nfe.emitente_third_party_id
        else:
            return nfe.destinatario_third_party_id
    
    def _get_default_journal(self, invoice_type: InvoiceType, config: Dict[str, Any]) -> Optional[Journal]:
        """Obtém diário padrão para o tipo de fatura"""
        if invoice_type == InvoiceType.CUSTOMER_INVOICE:
            journal_code = config.get('default_sales_journal')
        else:
            journal_code = config.get('default_purchase_journal')
        
        if journal_code:
            return self.db.query(Journal).filter(Journal.code == journal_code).first()
        
        return None
    
    def _generate_invoice_number(self, nfe: NFe, journal: Optional[Journal]) -> str:
        """Gera número da fatura"""
        prefix = journal.code if journal else "INV"
        return f"{prefix}-NFe-{nfe.numero_nfe}-{nfe.serie}"
    
    async def _create_invoice_lines(
        self,
        invoice: Invoice,
        nfe: NFe,
        config: Dict[str, Any],
        user_id: uuid.UUID,
        validated_data: Dict[str, Any]  # Añadimos este parámetro
    ) -> None:
        """Crea linhas da fatura baseadas nos itens da NFe"""
        
        # Obter conta padrão para produtos
        default_account_id = self._get_default_product_account(invoice.invoice_type, config)
        
        sequence = 1
        # Usamos items_data del validated_data en lugar de nfe.items
        for item_data in validated_data.get('items_data', []):
            invoice_line = InvoiceLine(
                invoice_id=invoice.id,
                sequence=sequence,
                product_id=item_data.get('product_data', {}).get('product_id'),
                description=item_data['descricao_produto'],
                quantity=item_data['quantidade_comercial'],
                unit_price=item_data['valor_unitario_comercial'],
                subtotal=item_data['valor_total_produto'],
                tax_amount=(
                    item_data['valor_icms'] + 
                    item_data['valor_ipi'] + 
                    item_data['valor_pis'] + 
                    item_data['valor_cofins']
                ),
                total_amount=item_data['valor_total_produto'],
                account_id=default_account_id,
                created_by_id=user_id
            )
            
            self.db.add(invoice_line)
            sequence += 1
    
    def _get_default_product_account(self, invoice_type: InvoiceType, config: Dict[str, Any]) -> Optional[uuid.UUID]:
        """Obtém conta padrão para produtos"""
        if invoice_type == InvoiceType.CUSTOMER_INVOICE:
            account_code = config.get('default_revenue_account')
        else:
            account_code = config.get('default_expense_account')
        
        if account_code:
            account = self.db.query(Account).filter(Account.code == account_code).first()
            return account.id if account else None
        
        return None
    
        return None
