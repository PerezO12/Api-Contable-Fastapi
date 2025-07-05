"""
Sistema de fallback para el chat AI cuando OpenAI no está disponible
"""
import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class FallbackAIClient:
    """Cliente de fallback mejorado con respuestas específicas de contabilidad"""
    
    def __init__(self):
        self.response_patterns = {
            # Preguntas sobre el sistema (más específicas)
            r'(qué es|what is|o que é|que trata|what does|como funciona el sistema|about the system|sobre el sistema)': {
                'es': 'Este es un sistema integral de contabilidad que te ayuda a gestionar facturas, registros contables, reportes financieros y análisis empresarial. Incluye funciones para crear facturas automáticamente, seguimiento de gastos, generación de estados financieros y cumplimiento fiscal.',
                'en': 'This is a comprehensive accounting system that helps you manage invoices, accounting records, financial reports and business analysis. It includes features for automatic invoice creation, expense tracking, financial statement generation and tax compliance.',
                'pt': 'Este é um sistema abrangente de contabilidade que ajuda você a gerenciar faturas, registros contábeis, relatórios financeiros e análise empresarial. Inclui recursos para criação automática de faturas, rastreamento de despesas, geração de demonstrações financeiras e conformidade fiscal.'
            },
            
            # Pruebas y testing
            r'(probando|testing|test|prueba|funciona|works|funciona esto|how does this work|cómo funciona esto)': {
                'es': '¡Perfecto! El sistema de chat está funcionando correctamente. Estoy aquí para ayudarte con todas tus consultas contables. Puedes preguntarme sobre facturas, reportes, contabilidad básica, o cualquier función del sistema. ¿Qué te gustaría saber?',
                'en': 'Perfect! The chat system is working correctly. I\'m here to help you with all your accounting queries. You can ask me about invoices, reports, basic accounting, or any system function. What would you like to know?',
                'pt': 'Perfeito! O sistema de chat está funcionando corretamente. Estou aqui para ajudar com todas as suas consultas contábeis. Você pode me perguntar sobre faturas, relatórios, contabilidade básica ou qualquer função do sistema. O que você gostaria de saber?'
            },
            
            # Preguntas sobre partida doble
            r'(partida doble|double entry|partidas dobradas|bookkeeping)': {
                'es': 'La partida doble es el principio fundamental de la contabilidad moderna. Cada transacción debe afectar al menos dos cuentas: por cada débito debe haber un crédito equivalente. Esto mantiene la ecuación contable equilibrada: Activos = Pasivos + Patrimonio.',
                'en': 'Double-entry bookkeeping is the fundamental principle of modern accounting. Each transaction must affect at least two accounts: for every debit there must be an equivalent credit. This keeps the accounting equation balanced: Assets = Liabilities + Equity.',
                'pt': 'A contabilidade de partidas dobradas é o princípio fundamental da contabilidade moderna. Cada transação deve afetar pelo menos duas contas: para cada débito deve haver um crédito equivalente. Isso mantém a equação contábil equilibrada: Ativos = Passivos + Patrimônio.'
            },
            
            # Preguntas sobre facturas
            r'(factura|invoice|fatura|crear|create|generar)': {
                'es': 'Para crear una factura necesitas: ID del cliente, fecha, lista de productos/servicios con cantidades y precios. El sistema calculará automáticamente subtotales, impuestos y el total final. También puedes agregar descuentos y notas adicionales.',
                'en': 'To create an invoice you need: customer ID, date, list of products/services with quantities and prices. The system will automatically calculate subtotals, taxes and final total. You can also add discounts and additional notes.',
                'pt': 'Para criar uma fatura você precisa: ID do cliente, data, lista de produtos/serviços com quantidades e preços. O sistema calculará automaticamente subtotais, impostos e total final. Você também pode adicionar descontos e notas adicionais.'
            },
            
            # Preguntas sobre reportes
            r'(reporte|report|relatório|balance|estado|statement|flujo|cash flow)': {
                'es': 'El sistema genera múltiples reportes financieros: Balance General (situación patrimonial), Estado de Resultados (ingresos y gastos), Flujo de Caja (movimientos de efectivo), reportes de ventas, análisis de gastos y reportes fiscales para cumplimiento tributario.',
                'en': 'The system generates multiple financial reports: Balance Sheet (financial position), Income Statement (revenues and expenses), Cash Flow (cash movements), sales reports, expense analysis and tax reports for compliance.',
                'pt': 'O sistema gera múltiplos relatórios financeiros: Balanço Patrimonial (posição financeira), Demonstração de Resultados (receitas e despesas), Fluxo de Caixa (movimentos de caixa), relatórios de vendas, análise de despesas e relatórios fiscais para conformidade.'
            },
            
            # Preguntas sobre cuentas y categorización
            r'(cuenta|account|categoria|categorize|gasto|expense|ingreso|revenue)': {
                'es': 'Para categorizar transacciones, el sistema utiliza un plan de cuentas estructurado. Los gastos se clasifican en categorías como: gastos operativos, administrativos, ventas, etc. Los ingresos se dividen en: ventas, servicios, ingresos financieros, etc. Cada cuenta tiene un código único para facilitar la organización.',
                'en': 'To categorize transactions, the system uses a structured chart of accounts. Expenses are classified into categories like: operational, administrative, sales expenses, etc. Income is divided into: sales, services, financial income, etc. Each account has a unique code for easy organization.',
                'pt': 'Para categorizar transações, o sistema usa um plano de contas estruturado. As despesas são classificadas em categorias como: gastos operacionais, administrativos, vendas, etc. As receitas são divididas em: vendas, serviços, receitas financeiras, etc. Cada conta tem um código único para facilitar a organização.'
            },
            
            # Saludos y preguntas generales de ayuda (MÁS ESPECÍFICO PRIMERO)
            r'(hola|hello|olá|ayudarme|ayuda general|help me|ajuda|que puedes hacer|what can you do|como puedes ayudar)': {
                'es': '¡Hola! Soy tu asistente de contabilidad. Te puedo ayudar con: 1) Explicar conceptos contables, 2) Guiarte en la creación de facturas, 3) Explicar cómo categorizar gastos e ingresos, 4) Ayudarte con reportes financieros, 5) Resolver dudas sobre el sistema. ¿Qué necesitas específicamente?',
                'en': 'Hello! I\'m your accounting assistant. I can help you with: 1) Explaining accounting concepts, 2) Guiding you through invoice creation, 3) Explaining how to categorize expenses and income, 4) Helping with financial reports, 5) Resolving system questions. What do you need specifically?',
                'pt': 'Olá! Sou seu assistente de contabilidade. Posso ajudar você com: 1) Explicar conceitos contábeis, 2) Orientar na criação de faturas, 3) Explicar como categorizar despesas e receitas, 4) Ajudar com relatórios financeiros, 5) Resolver dúvidas sobre o sistema. O que você precisa especificamente?'
            },
            
            # Preguntas sobre facturas (antes de preguntas generales)
            r'(factura|invoice|fatura|crear factura|create invoice|nueva factura|new invoice)': {
                'es': 'Para crear una factura necesitas: ID del cliente, fecha, lista de productos/servicios con cantidades y precios. El sistema calculará automáticamente subtotales, impuestos y el total final. También puedes agregar descuentos y notas adicionales.',
                'en': 'To create an invoice you need: customer ID, date, list of products/services with quantities and prices. The system will automatically calculate subtotals, taxes and final total. You can also add discounts and additional notes.',
                'pt': 'Para criar uma fatura você precisa: ID do cliente, data, lista de produtos/serviços com quantidades e preços. O sistema calculará automaticamente subtotais, impostos e total final. Você também pode adicionar descontos e notas adicionais.'
            },
            
            # Preguntas sobre partida doble
            r'(partida doble|double entry|partidas dobradas|bookkeeping)': {
                'es': 'La partida doble es el principio fundamental de la contabilidad moderna. Cada transacción debe afectar al menos dos cuentas: por cada débito debe haber un crédito equivalente. Esto mantiene la ecuación contable equilibrada: Activos = Pasivos + Patrimonio.',
                'en': 'Double-entry bookkeeping is the fundamental principle of modern accounting. Each transaction must affect at least two accounts: for every debit there must be an equivalent credit. This keeps the accounting equation balanced: Assets = Liabilities + Equity.',
                'pt': 'A contabilidade de partidas dobradas é o princípio fundamental da contabilidade moderna. Cada transação deve afetar pelo menos duas contas: para cada débito deve haver um crédito equivalente. Isso mantém a equação contábil equilibrada: Ativos = Passivos + Patrimônio.'
            },
            
            # Preguntas sobre reportes
            r'(reporte|report|relatório|balance|estado|statement|flujo|cash flow)': {
                'es': 'El sistema genera múltiples reportes financieros: Balance General (situación patrimonial), Estado de Resultados (ingresos y gastos), Flujo de Caja (movimientos de efectivo), reportes de ventas, análisis de gastos y reportes fiscales para cumplimiento tributario.',
                'en': 'The system generates multiple financial reports: Balance Sheet (financial position), Income Statement (revenues and expenses), Cash Flow (cash movements), sales reports, expense analysis and tax reports for compliance.',
                'pt': 'O sistema gera múltiplos relatórios financeiros: Balanço Patrimonial (posição financeira), Demonstração de Resultados (receitas e despesas), Fluxo de Caixa (movimentos de caixa), relatórios de vendas, análise de despesas e relatórios fiscais para conformidade.'
            },
            
            # Preguntas sobre cuentas y categorización
            r'(cuenta|account|categoria|categorize|gasto|expense|ingreso|revenue)': {
                'es': 'Para categorizar transacciones, el sistema utiliza un plan de cuentas estructurado. Los gastos se clasifican en categorías como: gastos operativos, administrativos, ventas, etc. Los ingresos se dividen en: ventas, servicios, ingresos financieros, etc. Cada cuenta tiene un código único para facilitar la organización.',
                'en': 'To categorize transactions, the system uses a structured chart of accounts. Expenses are classified into categories like: operational, administrative, sales expenses, etc. Income is divided into: sales, services, financial income, etc. Each account has a unique code for easy organization.',
                'pt': 'Para categorizar transações, o sistema usa um plano de contas estruturado. As despesas são classificadas em categorias como: gastos operacionais, administrativos, vendas, etc. As receitas são divididas em: vendas, serviços, receitas financeiras, etc. Cada conta tem um código único para facilitar a organização.'
            },
        }
        
        self.default_responses = {
            'es': '¡Hola! Soy tu asistente de contabilidad. Te puedo ayudar con: crear facturas, explicar conceptos contables, categorizar transacciones, generar reportes financieros, y resolver dudas sobre contabilidad en general. ¿Sobre qué tema te gustaría que conversemos?',
            'en': 'Hello! I\'m your accounting assistant. I can help you with: creating invoices, explaining accounting concepts, categorizing transactions, generating financial reports, and resolving general accounting questions. What topic would you like to discuss?',
            'pt': 'Olá! Sou seu assistente de contabilidade. Posso ajudar você com: criar faturas, explicar conceitos contábeis, categorizar transações, gerar relatórios financeiros, e resolver dúvidas sobre contabilidade em geral. Sobre que tema você gostaria de conversar?'
        }
    
    async def generate_response(self, prompt: str) -> Optional[str]:
        """
        Genera una respuesta usando patrones predefinidos
        
        Args:
            prompt: Prompt del usuario
            
        Returns:
            Respuesta basada en patrones de contabilidad
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        logger.info("Solicitud de chat fallback rechazada - servicios de IA desactivados")
        return "Los servicios de inteligencia artificial están temporalmente desactivados. Por favor, contacte al administrador del sistema para asistencia."
    
    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto de forma simple"""
        text_lower = text.lower()
        
        # Palabras específicas y únicas del español
        if any(word in text_lower for word in ['qué', 'cómo', 'explícame', 'probando', 'esto', 'funciona esto']):
            return 'es'
        
        # Palabras específicas del portugués
        if any(word in text_lower for word in ['você', 'não', 'é', 'olá', 'em que pode']):
            return 'pt'
        
        # Palabras específicas del inglés
        if any(word in text_lower for word in ['hello', 'what can', 'how can', 'you help']):
            return 'en'
        
        # Palabras clave en español (más específicas)
        spanish_keywords = ['que', 'qué', 'como', 'cómo', 'es', 'del', 'la', 'el', 'de', 'en', 'por', 'para', 'con', 'trata', 'sistema', 'hola', 'ayudarme', 'puedes', 'puede', 'ayuda']
        # Palabras clave en portugués
        portuguese_keywords = ['que', 'como', 'é', 'do', 'da', 'de', 'em', 'por', 'para', 'com', 'não', 'você', 'sistema', 'olá', 'ajudar']
        # Palabras clave en inglés
        english_keywords = ['what', 'how', 'is', 'the', 'of', 'in', 'for', 'with', 'you', 'can', 'do', 'does', 'system', 'about', 'hello', 'help']
        
        spanish_count = sum(1 for word in spanish_keywords if word in text_lower)
        portuguese_count = sum(1 for word in portuguese_keywords if word in text_lower)
        english_count = sum(1 for word in english_keywords if word in text_lower)
        
        logger.info(f"Conteo de palabras - ES: {spanish_count}, PT: {portuguese_count}, EN: {english_count}")
        
        if spanish_count >= portuguese_count and spanish_count >= english_count:
            return 'es'
        elif portuguese_count >= english_count:
            return 'pt'
        else:
            return 'en'
    
    async def generate_with_retry(self, prompt: str, max_retries: int = 1) -> Optional[str]:
        """
        Genera respuesta con reintentos (simplificado para fallback)
        
        Args:
            prompt: Prompt del usuario
            max_retries: Número de reintentos (no usado en fallback)
            
        Returns:
            Respuesta generada
        """
        return await self.generate_response(prompt)
    
    def test_connection(self) -> bool:
        """
        El fallback siempre está "conectado"
        
        Returns:
            Siempre True
        """
        # DESACTIVADO TEMPORALMENTE: Servicios de IA deshabilitados
        return False


# Instancia global del cliente fallback
fallback_client = FallbackAIClient()
