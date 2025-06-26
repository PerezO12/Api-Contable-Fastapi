"""
NFe Validation Service for validating and normalizing NFe data before processing.
Handles data validation, third party creation, product creation, and account determination.
"""
import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.nfe import NFe, NFeItem, NFeStatus, NFeType
from app.models.third_party import ThirdParty, ThirdPartyType, DocumentType
from app.models.product import Product, ProductType, ProductStatus, MeasurementUnit
from app.models.invoice import Invoice, InvoiceType, InvoiceStatus
from app.models.account import Account


class NFeValidationService:
    """Serviço para validação e normalização de dados de NFe"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_and_normalize_nfe_data(
        self, 
        nfe_data: Dict[str, Any], 
        user_id: uuid.UUID,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Valida e normaliza dados de NFe antes do processamento
        
        Args:
            nfe_data: Dados extraídos do XML
            user_id: ID do usuário que está processando
            config: Configurações para processamento
            
        Returns:
            Dict com dados validados e normalizados
        """
        config = config or {}
        
        # Validar dados básicos
        self._validate_basic_data(nfe_data)
        
        # Validar e normalizar terceiros
        emitente_data = self._validate_and_normalize_third_party(
            nfe_data, 'emitente', user_id, config
        )
        
        destinatario_data = self._validate_and_normalize_third_party(
            nfe_data, 'destinatario', user_id, config
        )
        
        # Validar e normalizar produtos
        items_data = self._validate_and_normalize_items(
            nfe_data.get('items', []), user_id, config
        )
        
        # Montar dados normalizados
        normalized_data = {
            **nfe_data,
            'emitente_data': emitente_data,
            'destinatario_data': destinatario_data,
            'items_data': items_data,
            'validation_metadata': {
                'validated_at': datetime.utcnow().isoformat(),
                'validator_version': '1.0.0',
                'user_id': str(user_id)
            }
        }
        
        return normalized_data
    
    def _validate_basic_data(self, nfe_data: Dict[str, Any]) -> None:
        """Valida dados básicos da NFe"""
        required_fields = [
            'chave_nfe', 'numero_nfe', 'serie', 'data_emissao',
            'natureza_operacao', 'cnpj_emitente', 'nome_emitente'
        ]
        
        for field in required_fields:
            if not nfe_data.get(field):
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        # Validar chave NFe
        chave = nfe_data['chave_nfe']
        if not re.match(r'^\d{44}$', chave):
            raise ValueError(f"Chave NFe inválida: {chave}")
        
        # Validar CNPJ emitente
        cnpj_emitente = nfe_data['cnpj_emitente']
        if not re.match(r'^\d{14}$', cnpj_emitente):
            raise ValueError(f"CNPJ emitente inválido: {cnpj_emitente}")
        
        # Validar tipo NFe
        tipo_nfe = nfe_data.get('tipo_nfe')
        if tipo_nfe not in ['0', '1']:
            raise ValueError(f"Tipo NFe inválido: {tipo_nfe}")
        
        # Validar valores totais
        valor_total = nfe_data.get('valor_total_nfe', 0)
        if valor_total <= 0:
            raise ValueError("Valor total da NFe deve ser maior que zero")
    
    def _validate_and_normalize_third_party(
        self, 
        nfe_data: Dict[str, Any], 
        party_type: str,  # 'emitente' ou 'destinatario'
        user_id: uuid.UUID,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida e normaliza dados de terceiros (emitente/destinatário)"""
        
        if party_type == 'emitente':
            cnpj = nfe_data.get('cnpj_emitente')
            cpf = None
            nome = nfe_data.get('nome_emitente')
            fantasia = nfe_data.get('fantasia_emitente')
            tp_terceiro = ThirdPartyType.SUPPLIER  # Emitente é fornecedor para NFe de entrada
            
        elif party_type == 'destinatario':
            cnpj = nfe_data.get('cnpj_destinatario')
            cpf = nfe_data.get('cpf_destinatario')
            nome = nfe_data.get('nome_destinatario')
            fantasia = None
            tp_terceiro = ThirdPartyType.CUSTOMER  # Destinatário é cliente para NFe de saída
            
        else:
            raise ValueError(f"Tipo de terceiro inválido: {party_type}")
        
        # Se for consumidor final, pode não ter dados completos
        if nome == 'CONSUMIDOR FINAL':
            return {
                'third_party_id': None,
                'is_consumer': True,
                'document_number': cpf or cnpj,
                'name': nome
            }
        
        # Validar documento
        if not cnpj and not cpf:
            raise ValueError(f"CNPJ ou CPF obrigatório para {party_type}")
        
        document_number = cnpj or cpf
        if not document_number:
            raise ValueError(f"Documento inválido para {party_type}")
            
        if not nome:
            raise ValueError(f"Nome obrigatório para {party_type}")
            
        document_type = DocumentType.CUIT if cnpj else DocumentType.DNI  # Adaptar conforme país
        
        # Buscar terceiro existente
        existing_third_party = self._find_existing_third_party(document_number, nome)
        
        if existing_third_party:
            return {
                'third_party_id': existing_third_party.id,
                'is_existing': True,
                'document_number': document_number,
                'name': nome
            }
        
        # Criar novo terceiro se configurado
        auto_create = config.get('auto_create_third_parties', True)
        if auto_create:
            new_third_party = self._create_third_party(
                document_number=document_number,
                document_type=document_type,
                name=nome,
                commercial_name=fantasia,
                third_party_type=tp_terceiro,
                user_id=user_id
            )
            
            return {
                'third_party_id': new_third_party.id,
                'is_new': True,
                'document_number': document_number,
                'name': nome
            }
        
        # Se não deve criar automaticamente
        return {
            'third_party_id': None,
            'needs_creation': True,
            'document_number': document_number,
            'name': nome,
            'suggested_data': {
                'document_number': document_number,
                'document_type': document_type,
                'name': nome,
                'commercial_name': fantasia,
                'third_party_type': tp_terceiro
            }
        }
    
    def _validate_and_normalize_items(
        self, 
        items: List[Dict[str, Any]], 
        user_id: uuid.UUID,
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Valida e normaliza itens da NFe"""
        
        if not items:
            raise ValueError("NFe deve ter pelo menos um item")
        
        normalized_items = []
        
        for item in items:
            normalized_item = self._validate_and_normalize_single_item(item, user_id, config)
            normalized_items.append(normalized_item)
        
        return normalized_items
    
    def _validate_and_normalize_single_item(
        self, 
        item: Dict[str, Any], 
        user_id: uuid.UUID,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida e normaliza um item específico"""
        
        # Validar campos obrigatórios
        required_fields = [
            'numero_item', 'codigo_produto', 'descricao_produto',
            'quantidade_comercial', 'valor_unitario_comercial', 'valor_total_produto'
        ]
        
        for field in required_fields:
            if item.get(field) is None:
                raise ValueError(f"Campo obrigatório ausente no item {item.get('numero_item', 'N/A')}: {field}")
        
        # Validar valores
        if item['quantidade_comercial'] <= 0:
            raise ValueError(f"Quantidade deve ser maior que zero no item {item['numero_item']}")
        
        if item['valor_total_produto'] <= 0:
            raise ValueError(f"Valor total deve ser maior que zero no item {item['numero_item']}")
        
        # Buscar produto existente
        existing_product = self._find_existing_product(item['codigo_produto'])
        
        if existing_product:
            product_data = {
                'product_id': existing_product.id,
                'is_existing': True
            }
        else:
            # Criar produto se configurado
            auto_create = config.get('auto_create_products', True)
            if auto_create:
                new_product = self._create_product(item, user_id)
                product_data = {
                    'product_id': new_product.id,
                    'is_new': True
                }
            else:
                product_data = {
                    'product_id': None,
                    'needs_creation': True,
                    'suggested_data': {
                        'code': item['codigo_produto'],
                        'name': item['descricao_produto'],
                        'measurement_unit': self._normalize_measurement_unit(item.get('unidade_comercial', 'unit'))
                    }
                }
        
        return {
            **item,
            'product_data': product_data
        }
    
    def _find_existing_third_party(self, document_number: str, name: Optional[str] = None) -> Optional[ThirdParty]:
        """Busca terceiro existente por documento ou nome"""
        query = self.db.query(ThirdParty)
        
        # Buscar por documento
        if document_number:
            existing = query.filter(ThirdParty.document_number == document_number).first()
            if existing:
                return existing
        
        # Buscar por nome se não encontrou por documento
        if name:
            existing = query.filter(ThirdParty.name == name).first()
            if existing:
                return existing
                
        return None
    
    def _create_third_party(
        self,
        document_number: str,
        document_type: DocumentType,
        name: str,
        commercial_name: Optional[str],
        third_party_type: ThirdPartyType,
        user_id: uuid.UUID
    ) -> ThirdParty:
        """Cria novo terceiro"""
        
        # Gerar código único
        code = self._generate_third_party_code(document_number)
        
        third_party = ThirdParty(
            code=code,
            name=name,
            commercial_name=commercial_name,
            third_party_type=third_party_type,
            document_type=document_type,
            document_number=document_number,
            is_active=True
        )
        
        self.db.add(third_party)
        self.db.flush()  # Para obter o ID
        
        return third_party
    
    def _find_existing_product(self, code: str) -> Optional[Product]:
        """Busca produto existente por código"""
        return self.db.query(Product).filter(
            Product.code == code
        ).first()
    
    def _create_product(self, item_data: Dict[str, Any], user_id: uuid.UUID) -> Product:
        """Cria novo produto baseado nos dados do item"""
        
        code = item_data['codigo_produto']
        name = item_data['descricao_produto']
        
        # Normalizar unidade de medida
        unit = self._normalize_measurement_unit(item_data.get('unidade_comercial', 'unit'))
        
        product = Product(
            code=code,
            name=name,
            product_type=ProductType.PRODUCT,
            status=ProductStatus.ACTIVE,
            measurement_unit=unit
        )
        
        self.db.add(product)
        self.db.flush()  # Para obter o ID
        
        return product
    
    def _normalize_measurement_unit(self, unit: str) -> MeasurementUnit:
        """Normaliza unidade de medida"""
        unit_lower = unit.lower().strip()
        
        unit_mapping = {
            'un': MeasurementUnit.UNIT,
            'unit': MeasurementUnit.UNIT,
            'unid': MeasurementUnit.UNIT,
            'pç': MeasurementUnit.UNIT,
            'pc': MeasurementUnit.UNIT,
            'peca': MeasurementUnit.UNIT,
            'kg': MeasurementUnit.KG,
            'kilo': MeasurementUnit.KG,
            'quilograma': MeasurementUnit.KG,
            'g': MeasurementUnit.GRAM,
            'grama': MeasurementUnit.GRAM,
            'l': MeasurementUnit.LITER,
            'litro': MeasurementUnit.LITER,
            'lt': MeasurementUnit.LITER,
            'm': MeasurementUnit.METER,
            'metro': MeasurementUnit.METER,
            'cm': MeasurementUnit.CM,
            'centimetro': MeasurementUnit.CM,
            'm2': MeasurementUnit.M2,
            'm²': MeasurementUnit.M2,
            'm3': MeasurementUnit.M3,
            'm³': MeasurementUnit.M3,
            'h': MeasurementUnit.HOUR,
            'hora': MeasurementUnit.HOUR,
            'hrs': MeasurementUnit.HOUR,
            'fc': MeasurementUnit.UNIT,  # Frasco - tratar como unidade
            'cx': MeasurementUnit.BOX,
            'caixa': MeasurementUnit.BOX,
            'pct': MeasurementUnit.PACK,
            'pacote': MeasurementUnit.PACK,
        }
        
        return unit_mapping.get(unit_lower, MeasurementUnit.UNIT)
    
    def _generate_third_party_code(self, document_number: str) -> str:
        """Gera código único para terceiro"""
        base_code = f"TP{document_number[:8]}"
        
        # Verificar se já existe
        counter = 1
        code = base_code
        
        while self.db.query(ThirdParty).filter(ThirdParty.code == code).first():
            code = f"{base_code}_{counter}"
            counter += 1
        
        return code
    
    def get_default_accounts(self, config: Dict[str, Any]) -> Dict[str, Optional[uuid.UUID]]:
        """Obtém contas padrão para contabilização"""
        
        default_accounts = {}
        
        # Conta de receita/vendas
        revenue_account_code = config.get('default_revenue_account')
        if revenue_account_code:
            revenue_account = self.db.query(Account).filter(
                Account.code == revenue_account_code
            ).first()
            default_accounts['revenue_account_id'] = revenue_account.id if revenue_account else None
        
        # Conta de clientes
        customer_account_code = config.get('default_customer_account')
        if customer_account_code:
            customer_account = self.db.query(Account).filter(
                Account.code == customer_account_code
            ).first()
            default_accounts['customer_account_id'] = customer_account.id if customer_account else None
        
        # Conta de fornecedores
        supplier_account_code = config.get('default_supplier_account')
        if supplier_account_code:
            supplier_account = self.db.query(Account).filter(
                Account.code == supplier_account_code
            ).first()
            default_accounts['supplier_account_id'] = supplier_account.id if supplier_account else None
        
        return default_accounts
    
    def validate_nfe_uniqueness(self, chave_nfe: str) -> bool:
        """Verifica se a NFe já foi processada"""
        existing_nfe = self.db.query(NFe).filter(
            NFe.chave_nfe == chave_nfe
        ).first()
        
        return existing_nfe is None
