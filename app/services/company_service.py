"""
Servicio para manejo de información de la empresa
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit import CompanyInfo


class CompanyService:
    """Servicio para operaciones con información de la empresa"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_active_company_info(self) -> Optional[CompanyInfo]:
        """Obtener la información de empresa activa"""
        query = select(CompanyInfo).where(CompanyInfo.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_company_name(self) -> str:
        """Obtener el nombre de la empresa activa o un valor por defecto"""
        company_info = await self.get_active_company_info()
        if company_info and company_info.name:
            return company_info.name
        return "Sistema Contable"  # Valor por defecto
