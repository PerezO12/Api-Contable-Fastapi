"""
Tests para la importación genérica de nuevos modelos:
- Centros de Costo
- Diarios Contables  
- Términos de Pago
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.cost_center import CostCenter
from app.models.journal import Journal, JournalType
from app.models.payment_terms import PaymentTerms, PaymentSchedule
from app.services.generic_import_validators import (
    validate_cost_center_data,
    validate_journal_data,
    validate_payment_terms_data
)


class TestCostCenterImportValidation:
    """Tests para validación de centros de costo"""
    
    @pytest.mark.asyncio
    async def test_validate_cost_center_data_valid(self, db_session: AsyncSession):
        """Test validación exitosa de centro de costo"""
        data = {
            "code": "TEST001",
            "name": "Centro de Prueba",
            "description": "Centro de costo para pruebas",
            "is_active": True
        }
        
        errors = await validate_cost_center_data(data, db_session, 1)
        assert len(errors) == 0
    
    @pytest.mark.asyncio 
    async def test_validate_cost_center_duplicate_code(self, db_session: AsyncSession):
        """Test validación de código duplicado"""
        # Crear centro de costo existente
        existing_center = CostCenter(
            code="DUP001",
            name="Centro Existente"
        )
        db_session.add(existing_center)
        await db_session.commit()
        
        # Intentar crear otro con el mismo código
        data = {
            "code": "DUP001", 
            "name": "Centro Nuevo"
        }
        
        errors = await validate_cost_center_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "code"
        assert errors[0].error_type == "duplicate_value"
    
    @pytest.mark.asyncio
    async def test_validate_cost_center_parent_not_found(self, db_session: AsyncSession):
        """Test validación de centro padre inexistente"""
        data = {
            "code": "CHILD001",
            "name": "Centro Hijo", 
            "parent_code": "NONEXISTENT"
        }
        
        errors = await validate_cost_center_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "parent_code"
        assert errors[0].error_type == "reference_not_found"


class TestJournalImportValidation:
    """Tests para validación de diarios"""
    
    @pytest.mark.asyncio
    async def test_validate_journal_data_valid(self, db_session: AsyncSession):
        """Test validación exitosa de diario"""
        data = {
            "name": "Diario de Prueba",
            "code": "TEST",
            "type": "sale",
            "sequence_prefix": "TST",
            "sequence_padding": 4
        }
        
        errors = await validate_journal_data(data, db_session, 1)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_journal_invalid_type(self, db_session: AsyncSession):
        """Test validación de tipo de diario inválido"""
        data = {
            "name": "Diario de Prueba",
            "code": "TEST",
            "type": "invalid_type",
            "sequence_prefix": "TST"
        }
        
        errors = await validate_journal_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "type"
        assert errors[0].error_type == "invalid_choice"
    
    @pytest.mark.asyncio
    async def test_validate_journal_duplicate_code(self, db_session: AsyncSession):
        """Test validación de código duplicado"""
        # Crear diario existente
        existing_journal = Journal(
            name="Diario Existente",
            code="DUP",
            type=JournalType.SALE,
            sequence_prefix="EXISTING"
        )
        db_session.add(existing_journal)
        await db_session.commit()
        
        # Intentar crear otro con el mismo código
        data = {
            "name": "Diario Nuevo",
            "code": "DUP",
            "type": "purchase",
            "sequence_prefix": "NEW"
        }
        
        errors = await validate_journal_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "code"
        assert errors[0].error_type == "duplicate_value"
    
    @pytest.mark.asyncio
    async def test_validate_journal_invalid_sequence_padding(self, db_session: AsyncSession):
        """Test validación de relleno de secuencia inválido"""
        data = {
            "name": "Diario de Prueba",
            "code": "TEST",
            "type": "sale",
            "sequence_prefix": "TST",
            "sequence_padding": 15  # Fuera del rango válido (1-10)
        }
        
        errors = await validate_journal_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "sequence_padding"
        assert errors[0].error_type == "value_out_of_range"


class TestPaymentTermsImportValidation:
    """Tests para validación de términos de pago"""
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_valid(self, db_session: AsyncSession):
        """Test validación exitosa de términos de pago"""
        data = {
            "code": "NET30",
            "name": "Neto 30 días",
            "payment_schedule_days": "30",
            "payment_schedule_percentages": "100.0"
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_multiple_periods(self, db_session: AsyncSession):
        """Test validación de múltiples períodos de pago"""
        data = {
            "code": "30-60-90",
            "name": "Tres cuotas",
            "payment_schedule_days": "30,60,90",
            "payment_schedule_percentages": "33.33,33.33,33.34"
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_invalid_total(self, db_session: AsyncSession):
        """Test validación de porcentajes que no suman 100%"""
        data = {
            "code": "INVALID",
            "name": "Términos Inválidos",
            "payment_schedule_days": "30,60",
            "payment_schedule_percentages": "50.0,40.0"  # Suma 90%, no 100%
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "payment_schedule_percentages"
        assert errors[0].error_type == "invalid_total"
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_mismatched_lengths(self, db_session: AsyncSession):
        """Test validación de longitudes diferentes entre días y porcentajes"""
        data = {
            "code": "MISMATCH",
            "name": "Longitudes Diferentes",
            "payment_schedule_days": "30,60,90",         # 3 elementos
            "payment_schedule_percentages": "50.0,50.0"  # 2 elementos
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "payment_schedule_percentages"
        assert errors[0].error_type == "length_mismatch"
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_negative_days(self, db_session: AsyncSession):
        """Test validación de días negativos"""
        data = {
            "code": "NEGATIVE",
            "name": "Días Negativos",
            "payment_schedule_days": "-10,30",
            "payment_schedule_percentages": "50.0,50.0"
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "payment_schedule_days"
        assert errors[0].error_type == "invalid_value"
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_unordered_days(self, db_session: AsyncSession):
        """Test validación de días no ordenados"""
        data = {
            "code": "UNORDERED",
            "name": "Días Desordenados",
            "payment_schedule_days": "60,30,90",  # No están en orden ascendente
            "payment_schedule_percentages": "33.33,33.33,33.34"
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "payment_schedule_days"
        assert errors[0].error_type == "invalid_order"
    
    @pytest.mark.asyncio
    async def test_validate_payment_terms_duplicate_code(self, db_session: AsyncSession):
        """Test validación de código duplicado"""
        # Crear términos de pago existentes
        existing_terms = PaymentTerms(
            code="DUP",
            name="Términos Existentes"
        )
        db_session.add(existing_terms)
        await db_session.commit()
        
        # Intentar crear otros con el mismo código
        data = {
            "code": "DUP",
            "name": "Términos Nuevos",
            "payment_schedule_days": "30",
            "payment_schedule_percentages": "100.0"
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 1
        assert errors[0].field_name == "code"
        assert errors[0].error_type == "duplicate_value"


class TestIntegratedImportScenarios:
    """Tests de escenarios integrados de importación"""
    
    @pytest.mark.asyncio
    async def test_cost_center_hierarchy_import(self, db_session: AsyncSession):
        """Test importación de jerarquía de centros de costo"""
        # Crear centro padre
        parent_data = {
            "code": "PARENT",
            "name": "Centro Padre"
        }
        parent_errors = await validate_cost_center_data(parent_data, db_session, 1)
        assert len(parent_errors) == 0
        
        # Crear el centro padre en la base de datos
        parent_center = CostCenter(**parent_data)
        db_session.add(parent_center)
        await db_session.commit()
        
        # Validar centro hijo
        child_data = {
            "code": "CHILD",
            "name": "Centro Hijo",
            "parent_code": "PARENT"
        }
        child_errors = await validate_cost_center_data(child_data, db_session, 2)
        assert len(child_errors) == 0
    
    @pytest.mark.asyncio
    async def test_payment_terms_complex_schedule(self, db_session: AsyncSession):
        """Test validación de cronograma complejo de términos de pago"""
        data = {
            "code": "COMPLEX",
            "name": "Cronograma Complejo",
            "payment_schedule_days": "0,15,30,45,60",
            "payment_schedule_percentages": "20.0,20.0,20.0,20.0,20.0",
            "payment_schedule_descriptions": "Anticipo|Quincena 1|Mes 1|45 días|Final"
        }
        
        errors = await validate_payment_terms_data(data, db_session, 1)
        assert len(errors) == 0
