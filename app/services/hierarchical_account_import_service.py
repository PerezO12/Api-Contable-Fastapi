"""
Servicio para la importación jerárquica de cuentas contables.
Maneja las dependencias padre-hijo automáticamente.
"""

import logging
import uuid
from typing import List, Dict, Set, Any, Optional, Tuple
from collections import defaultdict, deque
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.account import Account, AccountType


logger = logging.getLogger(__name__)


class HierarchicalAccountImportService:
    """
    Servicio especializado para importar cuentas con relaciones jerárquicas.
    Implementa ordenamiento topológico para procesar las cuentas padre antes que las hijas.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.created_accounts_cache: Dict[str, Account] = {}
        
    async def import_accounts_hierarchically(
        self, 
        account_data_list: List[Dict[str, Any]], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Importa una lista de cuentas respetando la jerarquía padre-hijo.
        
        Args:
            account_data_list: Lista de diccionarios con los datos de las cuentas
            user_id: ID del usuario que ejecuta la importación
            
        Returns:
            Diccionario con el resultado de la importación
        """
        logger.info(f"Iniciando importación jerárquica de {len(account_data_list)} cuentas")
        
        # Paso 1: Cargar cuentas existentes en la base de datos
        await self._load_existing_accounts()
        
        # Paso 2: Validar y preparar los datos
        validated_accounts = await self._validate_account_data(account_data_list)
        
        # Paso 3: Analizar dependencias y ordenar topológicamente
        ordered_accounts = self._topological_sort(validated_accounts)
        
        # Paso 4: Importar las cuentas en el orden correcto
        result = await self._import_accounts_in_order(ordered_accounts, user_id)
        
        logger.info(f"Importación jerárquica completada: {result}")
        return result
    
    async def _load_existing_accounts(self):
        """
        Carga todas las cuentas existentes en la base de datos al caché.
        """
        query = select(Account)
        result = await self.db.execute(query)
        existing_accounts = result.scalars().all()
        
        for account in existing_accounts:
            self.created_accounts_cache[account.code] = account
            
        logger.info(f"Cargadas {len(existing_accounts)} cuentas existentes al caché")
    
    async def _validate_account_data(self, account_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Valida los datos básicos de las cuentas antes de procesar las dependencias.
        """
        validated_accounts = []
        codes_in_import = set()
        
        for i, account_data in enumerate(account_data_list):
            # Validaciones básicas
            if not account_data.get('code'):
                raise ValueError(f"Fila {i + 1}: El código de cuenta es requerido")
            
            if not account_data.get('name'):
                raise ValueError(f"Fila {i + 1}: El nombre de cuenta es requerido")
            
            if not account_data.get('account_type'):
                raise ValueError(f"Fila {i + 1}: El tipo de cuenta es requerido")
            
            code = account_data['code']
            
            # Verificar códigos duplicados en el archivo de importación
            if code in codes_in_import:
                raise ValueError(f"Fila {i + 1}: El código '{code}' está duplicado en el archivo de importación")
            
            codes_in_import.add(code)
            
            # Validar tipo de cuenta
            try:
                AccountType(account_data['account_type'])
            except ValueError:
                valid_types = [t.value for t in AccountType]
                raise ValueError(f"Fila {i + 1}: Tipo de cuenta inválido '{account_data['account_type']}'. Tipos válidos: {valid_types}")
            
            validated_accounts.append(account_data)
        
        logger.info(f"Validados {len(validated_accounts)} registros de cuentas")
        return validated_accounts
    
    def _topological_sort(self, account_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ordena las cuentas topológicamente para que las cuentas padre se procesen antes que las hijas.
        """
        logger.info("Iniciando ordenamiento topológico de cuentas")
        
        # Crear mapas para el algoritmo
        code_to_data = {acc['code']: acc for acc in account_data_list}
        
        # Construir grafo de dependencias
        dependencies = defaultdict(list)  # parent_code -> [child_codes]
        dependents = defaultdict(int)     # child_code -> count of dependencies
        
        # Identificar todas las cuentas que no tienen padre (raíces)
        roots = []
        
        for account_data in account_data_list:
            code = account_data['code']
            parent_code = account_data.get('parent_code')
            
            if parent_code:
                # Esta cuenta tiene padre
                dependencies[parent_code].append(code)
                dependents[code] += 1
                
                # Verificar que el padre existe (en BD o en archivo de importación)
                if parent_code not in self.created_accounts_cache and parent_code not in code_to_data:
                    raise ValueError(f"Cuenta padre '{parent_code}' no encontrada para la cuenta '{code}'")
            else:
                # Esta cuenta no tiene padre (es raíz)
                roots.append(code)
        
        # Algoritmo de ordenamiento topológico usando Kahn's algorithm
        queue = deque(roots)
        ordered_codes = []
        
        while queue:
            current_code = queue.popleft()
            ordered_codes.append(current_code)
            
            # Procesar todas las cuentas hijas del código actual
            for child_code in dependencies[current_code]:
                dependents[child_code] -= 1
                
                # Si esta cuenta hija ya no tiene dependencias pendientes, agregarla a la cola
                if dependents[child_code] == 0:
                    queue.append(child_code)
        
        # Verificar si hay dependencias circulares
        if len(ordered_codes) != len(account_data_list):
            remaining_codes = set(code_to_data.keys()) - set(ordered_codes)
            raise ValueError(f"Dependencias circulares detectadas en las cuentas: {list(remaining_codes)}")
        
        # Reordenar los datos según el orden topológico
        ordered_accounts = [code_to_data[code] for code in ordered_codes]
        
        logger.info(f"Ordenamiento topológico completado. Orden de procesamiento: {ordered_codes}")
        return ordered_accounts
    
    async def _import_accounts_in_order(
        self, 
        ordered_accounts: List[Dict[str, Any]], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Importa las cuentas en el orden topológico correcto.
        """
        created_count = 0
        updated_count = 0
        failed_count = 0
        errors = []
        
        for i, account_data in enumerate(ordered_accounts):
            try:
                # Verificar si la cuenta ya existe
                code = account_data['code']
                
                if code in self.created_accounts_cache:
                    # La cuenta ya existe, considerar actualización
                    existing_account = self.created_accounts_cache[code]
                    logger.info(f"Cuenta '{code}' ya existe, saltando creación")
                    continue
                
                # Resolver el parent_id si hay parent_code
                parent_id = None
                if account_data.get('parent_code'):
                    parent_code = account_data['parent_code']
                    parent_account = self.created_accounts_cache.get(parent_code)
                    
                    if not parent_account:
                        raise ValueError(f"Cuenta padre '{parent_code}' no encontrada en caché")
                    
                    parent_id = parent_account.id
                    
                    # Validar que el tipo de cuenta sea compatible con el padre
                    if account_data['account_type'] != parent_account.account_type.value:
                        raise ValueError(f"La cuenta '{code}' debe ser del mismo tipo que su padre '{parent_code}'")
                
                # Crear la nueva cuenta
                new_account = Account(
                    code=code,
                    name=account_data['name'],
                    description=account_data.get('description'),
                    account_type=AccountType(account_data['account_type']),
                    category=account_data.get('category'),
                    parent_id=parent_id,
                    level=self._calculate_level(parent_id),
                    is_active=account_data.get('is_active', True),
                    allows_movements=account_data.get('allows_movements', True),
                    requires_third_party=account_data.get('requires_third_party', False),
                    requires_cost_center=account_data.get('requires_cost_center', False),
                    allows_reconciliation=account_data.get('allows_reconciliation', False),
                    notes=account_data.get('notes'),
                    created_by_id=user_id
                )
                
                # Guardar en la base de datos
                self.db.add(new_account)
                await self.db.flush()  # Para obtener el ID generado
                
                # Agregar al caché inmediatamente para que esté disponible para las cuentas hijas
                self.created_accounts_cache[code] = new_account
                created_count += 1
                
                logger.debug(f"Cuenta '{code}' creada exitosamente (nivel {new_account.level})")
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Error procesando cuenta '{account_data.get('code', 'UNKNOWN')}': {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Confirmar todas las transacciones si todo salió bien
        if failed_count == 0:
            await self.db.commit()
            logger.info("Todas las cuentas fueron creadas exitosamente")
        else:
            await self.db.rollback()
            logger.error(f"Se revirtieron los cambios debido a {failed_count} errores")
        
        return {
            "accounts_created": created_count,
            "accounts_updated": updated_count,
            "accounts_failed": failed_count,
            "total_processed": len(ordered_accounts),
            "errors": errors,
            "success": failed_count == 0
        }
    
    def _calculate_level(self, parent_id: Optional[uuid.UUID]) -> int:
        """
        Calcula el nivel jerárquico de una cuenta basado en su padre.
        """
        if not parent_id:
            return 1
        
        # Buscar el padre en el caché
        parent_account = None
        for account in self.created_accounts_cache.values():
            if account.id == parent_id:
                parent_account = account
                break
        
        if parent_account:
            return parent_account.level + 1
        else:
            return 1  # Fallback si no se encuentra el padre
