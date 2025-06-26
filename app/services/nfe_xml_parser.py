"""
NFe XML Parser for extracting data from Brazilian electronic invoices (NFe).
Handles parsing of NFe XML files and extraction of relevant data.
"""
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
import re


class NFeXMLParser:
    """Parser para XMLs de NFe (Nota Fiscal Eletrônica)"""
    
    # Namespaces comuns em NFe
    NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe'
    }
    
    def __init__(self):
        pass
    
    def parse_xml_file(self, xml_path: str) -> Dict[str, Any]:
        """
        Parse um arquivo XML de NFe
        
        Args:
            xml_path: Caminho para o arquivo XML
            
        Returns:
            Dict com dados extraídos da NFe
        """
        with open(xml_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        
        return self.parse_xml_content(xml_content)
    
    def parse_xml_content(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse do conteúdo XML de NFe
        
        Args:
            xml_content: String com conteúdo XML
            
        Returns:
            Dict com dados extraídos da NFe
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Encontrar o elemento NFe
            nfe_element = self._find_nfe_element(root)
            if nfe_element is None:
                raise ValueError("Elemento NFe não encontrado no XML")
            
            # Extrair dados principais
            nfe_data = self._extract_nfe_data(nfe_element, xml_content)
            
            return nfe_data
            
        except ET.ParseError as e:
            raise ValueError(f"Erro ao fazer parse do XML: {str(e)}")
        except Exception as e:
            raise ValueError(f"Erro inesperado ao processar XML: {str(e)}")
    
    def _find_nfe_element(self, root: ET.Element) -> Optional[ET.Element]:
        """Encontra o elemento NFe no XML"""
        # Tentar diferentes caminhos para encontrar NFe
        paths = [
            './/nfe:NFe',
            './/NFe',
            './{http://www.portalfiscal.inf.br/nfe}NFe'
        ]
        
        for path in paths:
            nfe = root.find(path, self.NAMESPACES)
            if nfe is not None:
                return nfe
        
        return None
    
    def _extract_nfe_data(self, nfe_element: ET.Element, xml_content: str) -> Dict[str, Any]:
        """Extrai dados principais da NFe"""
        
        # Encontrar infNFe
        inf_nfe = nfe_element.find('.//nfe:infNFe', self.NAMESPACES)
        if inf_nfe is None:
            inf_nfe = nfe_element.find('.//infNFe')
        
        if inf_nfe is None:
            raise ValueError("Elemento infNFe não encontrado")
        
        # Extrair chave da NFe do atributo Id
        chave_nfe = self._extract_chave_nfe(inf_nfe)
        
        # Extrair dados de identificação
        ide_data = self._extract_ide_data(inf_nfe)
        
        # Extrair dados do emitente
        emit_data = self._extract_emit_data(inf_nfe)
        
        # Extrair dados do destinatário
        dest_data = self._extract_dest_data(inf_nfe)
        
        # Extrair totais
        totals_data = self._extract_totals_data(inf_nfe)
        
        # Extrair itens
        items_data = self._extract_items_data(inf_nfe)
        
        # Montar dados completos
        nfe_data = {
            'chave_nfe': chave_nfe,
            'xml_content': xml_content,
            **ide_data,
            **emit_data,
            **dest_data,
            **totals_data,
            'items': items_data,
            'xml_metadata': {
                'total_items': len(items_data),
                'parsed_at': datetime.utcnow().isoformat()
            }
        }
        
        return nfe_data
    
    def _extract_chave_nfe(self, inf_nfe: ET.Element) -> str:
        """Extrai a chave da NFe do atributo Id"""
        id_attr = inf_nfe.get('Id', '')
        # Remove 'NFe' do início se presente
        chave = id_attr.replace('NFe', '') if id_attr.startswith('NFe') else id_attr
        
        if len(chave) != 44:
            raise ValueError(f"Chave NFe inválida: {chave}")
        
        return chave
    
    def _extract_ide_data(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Extrai dados de identificação da NFe"""
        ide = inf_nfe.find('.//nfe:ide', self.NAMESPACES)
        if ide is None:
            ide = inf_nfe.find('.//ide')
        
        if ide is None:
            raise ValueError("Elemento ide não encontrado")
        
        return {
            'numero_nfe': self._get_element_text(ide, 'nNF'),
            'serie': self._get_element_text(ide, 'serie'),
            'data_emissao': self._parse_datetime(self._get_element_text(ide, 'dhEmi')),
            'data_saida_entrada': self._parse_datetime(self._get_element_text(ide, 'dhSaiEnt')),
            'tipo_nfe': self._get_element_text(ide, 'tpNF'),
            'natureza_operacao': self._get_element_text(ide, 'natOp'),
            'finalidade_nfe': self._get_element_text(ide, 'finNFe'),
        }
    
    def _extract_emit_data(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Extrai dados do emitente"""
        emit = inf_nfe.find('.//nfe:emit', self.NAMESPACES)
        if emit is None:
            emit = inf_nfe.find('.//emit')
        
        if emit is None:
            raise ValueError("Elemento emit não encontrado")
        
        return {
            'cnpj_emitente': self._get_element_text(emit, 'CNPJ'),
            'nome_emitente': self._get_element_text(emit, 'xNome'),
            'fantasia_emitente': self._get_element_text(emit, 'xFant'),
        }
    
    def _extract_dest_data(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Extrai dados do destinatário"""
        dest = inf_nfe.find('.//nfe:dest', self.NAMESPACES)
        if dest is None:
            dest = inf_nfe.find('.//dest')
        
        if dest is None:
            # NFe pode não ter destinatário (ex: NFe para consumidor final)
            return {
                'cnpj_destinatario': None,
                'cpf_destinatario': None,
                'nome_destinatario': 'CONSUMIDOR FINAL',
            }
        
        return {
            'cnpj_destinatario': self._get_element_text(dest, 'CNPJ'),
            'cpf_destinatario': self._get_element_text(dest, 'CPF'),
            'nome_destinatario': self._get_element_text(dest, 'xNome') or 'CONSUMIDOR FINAL',
        }
    
    def _extract_totals_data(self, inf_nfe: ET.Element) -> Dict[str, Any]:
        """Extrai dados de totais"""
        total = inf_nfe.find('.//nfe:total', self.NAMESPACES)
        if total is None:
            total = inf_nfe.find('.//total')
        
        if total is None:
            raise ValueError("Elemento total não encontrado")
        
        icms_tot = total.find('.//nfe:ICMSTot', self.NAMESPACES)
        if icms_tot is None:
            icms_tot = total.find('.//ICMSTot')
        
        if icms_tot is None:
            raise ValueError("Elemento ICMSTot não encontrado")
        
        return {
            'valor_total_produtos': self._parse_decimal(self._get_element_text(icms_tot, 'vProd')),
            'valor_total_icms': self._parse_decimal(self._get_element_text(icms_tot, 'vICMS')),
            'valor_total_ipi': self._parse_decimal(self._get_element_text(icms_tot, 'vIPI')),
            'valor_total_pis': self._parse_decimal(self._get_element_text(icms_tot, 'vPIS')),
            'valor_total_cofins': self._parse_decimal(self._get_element_text(icms_tot, 'vCOFINS')),
            'valor_total_nfe': self._parse_decimal(self._get_element_text(icms_tot, 'vNF')),
        }
    
    def _extract_items_data(self, inf_nfe: ET.Element) -> List[Dict[str, Any]]:
        """Extrai dados dos itens da NFe"""
        items = []
        
        # Buscar todos os elementos det (detalhes)
        det_elements = inf_nfe.findall('.//nfe:det', self.NAMESPACES)
        if not det_elements:
            det_elements = inf_nfe.findall('.//det')
        
        for det in det_elements:
            item_data = self._extract_single_item_data(det)
            if item_data:
                items.append(item_data)
        
        return items
    
    def _extract_single_item_data(self, det: ET.Element) -> Optional[Dict[str, Any]]:
        """Extrai dados de um item específico"""
        try:
            # Número do item
            numero_item = int(det.get('nItem', '0'))
            
            # Dados do produto
            prod = det.find('.//nfe:prod', self.NAMESPACES)
            if prod is None:
                prod = det.find('.//prod')
            
            if prod is None:
                return None
            
            # Dados de impostos
            imposto = det.find('.//nfe:imposto', self.NAMESPACES)
            if imposto is None:
                imposto = det.find('.//imposto')
            
            # Extrair valores de impostos
            icms_value = self._extract_icms_value(imposto)
            ipi_value = self._extract_ipi_value(imposto)
            pis_value = self._extract_pis_value(imposto)
            cofins_value = self._extract_cofins_value(imposto)
            
            return {
                'numero_item': numero_item,
                'codigo_produto': self._get_element_text(prod, 'cProd'),
                'descricao_produto': self._get_element_text(prod, 'xProd'),
                'ncm': self._get_element_text(prod, 'NCM'),
                'cfop': self._get_element_text(prod, 'CFOP'),
                'unidade_comercial': self._get_element_text(prod, 'uCom'),
                'quantidade_comercial': self._parse_decimal(self._get_element_text(prod, 'qCom')),
                'valor_unitario_comercial': self._parse_decimal(self._get_element_text(prod, 'vUnCom')),
                'valor_total_produto': self._parse_decimal(self._get_element_text(prod, 'vProd')),
                'valor_icms': icms_value,
                'valor_ipi': ipi_value,
                'valor_pis': pis_value,
                'valor_cofins': cofins_value,
                'xml_metadata': {
                    'ean': self._get_element_text(prod, 'cEAN'),
                    'ean_tributavel': self._get_element_text(prod, 'cEANTrib'),
                    'unidade_tributavel': self._get_element_text(prod, 'uTrib'),
                    'quantidade_tributavel': self._get_element_text(prod, 'qTrib'),
                    'valor_unitario_tributavel': self._get_element_text(prod, 'vUnTrib'),
                }
            }
            
        except Exception as e:
            print(f"Erro ao extrair item {det.get('nItem', 'N/A')}: {str(e)}")
            return None
    
    def _extract_icms_value(self, imposto: Optional[ET.Element]) -> Decimal:
        """Extrai valor do ICMS"""
        if imposto is None:
            return Decimal('0')
        
        # Buscar diferentes situações de ICMS
        icms_paths = [
            './/nfe:ICMS//nfe:vICMS',
            './/ICMS//vICMS',
            './/nfe:ICMS00//nfe:vICMS',
            './/ICMS00//vICMS',
            './/nfe:ICMS10//nfe:vICMS',
            './/ICMS10//vICMS',
        ]
        
        for path in icms_paths:
            element = imposto.find(path, self.NAMESPACES)
            if element is not None and element.text:
                return self._parse_decimal(element.text)
        
        return Decimal('0')
    
    def _extract_ipi_value(self, imposto: Optional[ET.Element]) -> Decimal:
        """Extrai valor do IPI"""
        if imposto is None:
            return Decimal('0')
        
        ipi_paths = [
            './/nfe:IPI//nfe:vIPI',
            './/IPI//vIPI',
        ]
        
        for path in ipi_paths:
            element = imposto.find(path, self.NAMESPACES)
            if element is not None and element.text:
                return self._parse_decimal(element.text)
        
        return Decimal('0')
    
    def _extract_pis_value(self, imposto: Optional[ET.Element]) -> Decimal:
        """Extrai valor do PIS"""
        if imposto is None:
            return Decimal('0')
        
        pis_paths = [
            './/nfe:PIS//nfe:vPIS',
            './/PIS//vPIS',
        ]
        
        for path in pis_paths:
            element = imposto.find(path, self.NAMESPACES)
            if element is not None and element.text:
                return self._parse_decimal(element.text)
        
        return Decimal('0')
    
    def _extract_cofins_value(self, imposto: Optional[ET.Element]) -> Decimal:
        """Extrai valor do COFINS"""
        if imposto is None:
            return Decimal('0')
        
        cofins_paths = [
            './/nfe:COFINS//nfe:vCOFINS',
            './/COFINS//vCOFINS',
        ]
        
        for path in cofins_paths:
            element = imposto.find(path, self.NAMESPACES)
            if element is not None and element.text:
                return self._parse_decimal(element.text)
        
        return Decimal('0')
    
    def _get_element_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """Obtém texto de um elemento filho"""
        element = parent.find(f'.//nfe:{tag}', self.NAMESPACES)
        if element is None:
            element = parent.find(f'.//{tag}')
        
        return element.text.strip() if element is not None and element.text else None
    
    def _parse_decimal(self, value: Optional[str]) -> Decimal:
        """Converte string para Decimal"""
        if not value:
            return Decimal('0')
        
        try:
            # Remove espaços e substitui vírgula por ponto se necessário
            clean_value = value.strip().replace(',', '.')
            return Decimal(clean_value)
        except:
            return Decimal('0')
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Converte string ISO para datetime"""
        if not value:
            return None
        
        try:
            # Remove timezone info se presente e faz parse
            clean_value = re.sub(r'[+-]\d{2}:\d{2}$', '', value.strip())
            
            # Tentar diferentes formatos
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(clean_value, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
