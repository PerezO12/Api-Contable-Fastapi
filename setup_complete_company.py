#!/usr/bin/env python3
"""
🏢 SCRIPT DE CONFIGURACIÓN COMPLETA DE EMPRESA
===============================================

Este script configura una empresa completa con:
- Plan de cuentas completo (activos, pasivos, patrimonio, ingresos, gastos)
- Diarios contables necesarios
- Configuraciones por defecto
- Cuentas de terceros, bancos, impuestos
- Todo lo necesario para operación real

Ejecutar cuando se quiera una configuración completa desde cero.
"""

import asyncio
import logging
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.account import Account, AccountType, AccountCategory, CashFlowCategory
from app.models.journal import Journal, JournalType
from app.models.user import User

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# PLAN DE CUENTAS COMPLETO
# =====================================================

COMPLETE_CHART_OF_ACCOUNTS = [
    # ==================== ACTIVOS ====================
    
    # 1. ACTIVOS CORRIENTES
    {
        "code": "1",
        "name": "ACTIVOS",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 1
    },
    {
        "code": "11",
        "name": "ACTIVOS CORRIENTES",
        "parent_code": "1",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 2
    },
    
    # Efectivo y Bancos
    {
        "code": "1110",
        "name": "EFECTIVO Y EQUIVALENTES",
        "parent_code": "11",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.CASH_EQUIVALENTS,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "111001",
        "name": "Caja General",
        "parent_code": "1110",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.CASH_EQUIVALENTS,
        "allows_movements": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "111002",
        "name": "Caja Menor",
        "parent_code": "1110",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.CASH_EQUIVALENTS,
        "allows_movements": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "111101",
        "name": "Banco Nacional - Cuenta Corriente",
        "parent_code": "1110",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.CASH_EQUIVALENTS,
        "allows_movements": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "111102",
        "name": "Banco Nacional - Cuenta de Ahorros",
        "parent_code": "1110",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.CASH_EQUIVALENTS,
        "allows_movements": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "111103",
        "name": "Banco Popular - Cuenta Corriente",
        "parent_code": "1110",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.CASH_EQUIVALENTS,
        "allows_movements": True,
        "allows_reconciliation": True,
        "level": 4
    },
    
    # Cuentas por Cobrar
    {
        "code": "1120",
        "name": "CUENTAS POR COBRAR",
        "parent_code": "11",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "112001",
        "name": "Clientes Nacionales",
        "parent_code": "1120",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "112002",
        "name": "Clientes Extranjeros",
        "parent_code": "1120",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "112003",
        "name": "Anticipos a Proveedores",
        "parent_code": "1120",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "level": 4
    },
    {
        "code": "112004",
        "name": "Empleados por Cobrar",
        "parent_code": "1120",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "level": 4
    },
    {
        "code": "112005",
        "name": "Provisión para Cuentas Incobrables",
        "parent_code": "1120",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # Inventarios
    {
        "code": "1130",
        "name": "INVENTARIOS",
        "parent_code": "11",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "113001",
        "name": "Inventario de Productos Terminados",
        "parent_code": "1130",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "113002",
        "name": "Inventario de Materias Primas",
        "parent_code": "1130",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "113003",
        "name": "Inventario en Proceso",
        "parent_code": "1130",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # Gastos Pagados por Anticipado
    {
        "code": "1140",
        "name": "GASTOS PAGADOS POR ANTICIPADO",
        "parent_code": "11",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "114001",
        "name": "Seguros Pagados por Anticipado",
        "parent_code": "1140",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "114002",
        "name": "Arriendos Pagados por Anticipado",
        "parent_code": "1140",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # 2. ACTIVOS NO CORRIENTES
    {
        "code": "12",
        "name": "ACTIVOS NO CORRIENTES",
        "parent_code": "1",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": False,
        "level": 2
    },
    
    # Propiedad, Planta y Equipo
    {
        "code": "1210",
        "name": "PROPIEDAD, PLANTA Y EQUIPO",
        "parent_code": "12",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "121001",
        "name": "Terrenos",
        "parent_code": "1210",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "121002",
        "name": "Edificios",
        "parent_code": "1210",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "121003",
        "name": "Maquinaria y Equipo",
        "parent_code": "1210",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "121004",
        "name": "Vehículos",
        "parent_code": "1210",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "121005",
        "name": "Equipo de Cómputo",
        "parent_code": "1210",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "121006",
        "name": "Muebles y Enseres",
        "parent_code": "1210",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    
    # Depreciación Acumulada
    {
        "code": "1220",
        "name": "DEPRECIACIÓN ACUMULADA",
        "parent_code": "12",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "122002",
        "name": "Depreciación Acumulada - Edificios",
        "parent_code": "1220",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "122003",
        "name": "Depreciación Acumulada - Maquinaria",
        "parent_code": "1220",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "122004",
        "name": "Depreciación Acumulada - Vehículos",
        "parent_code": "1220",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "122005",
        "name": "Depreciación Acumulada - Equipo de Cómputo",
        "parent_code": "1220",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.NON_CURRENT_ASSET,
        "cash_flow_category": CashFlowCategory.INVESTING,
        "allows_movements": True,
        "level": 4
    },
    
    # ==================== PASIVOS ====================
    
    {
        "code": "2",
        "name": "PASIVOS",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 1
    },
    
    # PASIVOS CORRIENTES
    {
        "code": "21",
        "name": "PASIVOS CORRIENTES",
        "parent_code": "2",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 2
    },
    
    # Cuentas por Pagar
    {
        "code": "2110",
        "name": "CUENTAS POR PAGAR",
        "parent_code": "21",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "211001",
        "name": "Proveedores Nacionales",
        "parent_code": "2110",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "211002",
        "name": "Proveedores Extranjeros",
        "parent_code": "2110",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "allows_reconciliation": True,
        "level": 4
    },
    {
        "code": "211003",
        "name": "Acreedores Varios",
        "parent_code": "2110",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "requires_third_party": True,
        "level": 4
    },
    
    # Obligaciones Laborales
    {
        "code": "2120",
        "name": "OBLIGACIONES LABORALES",
        "parent_code": "21",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "212001",
        "name": "Sueldos por Pagar",
        "parent_code": "2120",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "212002",
        "name": "Prestaciones Sociales por Pagar",
        "parent_code": "2120",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "212003",
        "name": "Vacaciones por Pagar",
        "parent_code": "2120",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # Obligaciones Fiscales
    {
        "code": "2130",
        "name": "OBLIGACIONES FISCALES",
        "parent_code": "21",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "213001",
        "name": "IVA por Pagar",
        "parent_code": "2130",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "213002",
        "name": "Retenciones de IVA por Pagar",
        "parent_code": "2130",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "213003",
        "name": "Retenciones de Renta por Pagar",
        "parent_code": "2130",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "213004",
        "name": "Impuesto de Renta por Pagar",
        "parent_code": "2130",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # PASIVOS NO CORRIENTES
    {
        "code": "22",
        "name": "PASIVOS NO CORRIENTES",
        "parent_code": "2",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.NON_CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "2210",
        "name": "OBLIGACIONES FINANCIERAS",
        "parent_code": "22",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.NON_CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "221001",
        "name": "Préstamos Bancarios Largo Plazo",
        "parent_code": "2210",
        "account_type": AccountType.LIABILITY,
        "category": AccountCategory.NON_CURRENT_LIABILITY,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": True,
        "level": 4
    },
    
    # ==================== PATRIMONIO ====================
    
    {
        "code": "3",
        "name": "PATRIMONIO",
        "account_type": AccountType.EQUITY,
        "category": AccountCategory.CAPITAL,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 1
    },
    {
        "code": "31",
        "name": "CAPITAL SOCIAL",
        "parent_code": "3",
        "account_type": AccountType.EQUITY,
        "category": AccountCategory.CAPITAL,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "310001",
        "name": "Capital Autorizado",
        "parent_code": "31",
        "account_type": AccountType.EQUITY,
        "category": AccountCategory.CAPITAL,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": True,
        "level": 3
    },
    {
        "code": "32",
        "name": "UTILIDADES RETENIDAS",
        "parent_code": "3",
        "account_type": AccountType.EQUITY,
        "category": AccountCategory.RETAINED_EARNINGS,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "320001",
        "name": "Utilidades de Ejercicios Anteriores",
        "parent_code": "32",
        "account_type": AccountType.EQUITY,
        "category": AccountCategory.RETAINED_EARNINGS,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": True,
        "level": 3
    },
    {
        "code": "320002",
        "name": "Utilidad del Ejercicio",
        "parent_code": "32",
        "account_type": AccountType.EQUITY,
        "category": AccountCategory.RETAINED_EARNINGS,
        "cash_flow_category": CashFlowCategory.FINANCING,
        "allows_movements": True,
        "level": 3
    },
    
    # ==================== INGRESOS ====================
    
    {
        "code": "4",
        "name": "INGRESOS",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 1
    },
    {
        "code": "41",
        "name": "INGRESOS OPERACIONALES",
        "parent_code": "4",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "4110",
        "name": "VENTAS",
        "parent_code": "41",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "411001",
        "name": "Ventas de Productos",
        "parent_code": "4110",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "411002",
        "name": "Ventas de Servicios",
        "parent_code": "4110",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "42",
        "name": "INGRESOS NO OPERACIONALES",
        "parent_code": "4",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.NON_OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "420001",
        "name": "Ingresos Financieros",
        "parent_code": "42",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.NON_OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 3
    },
    {
        "code": "420002",
        "name": "Otros Ingresos",
        "parent_code": "42",
        "account_type": AccountType.INCOME,
        "category": AccountCategory.NON_OPERATING_INCOME,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 3
    },
    
    # ==================== GASTOS ====================
    
    {
        "code": "5",
        "name": "GASTOS",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 1
    },
    {
        "code": "51",
        "name": "GASTOS OPERACIONALES",
        "parent_code": "5",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 2
    },
    
    # Gastos de Administración
    {
        "code": "5110",
        "name": "GASTOS DE ADMINISTRACIÓN",
        "parent_code": "51",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "511001",
        "name": "Sueldos y Salarios",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "511002",
        "name": "Prestaciones Sociales",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "511003",
        "name": "Arrendamientos",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "511004",
        "name": "Servicios Públicos",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "511005",
        "name": "Seguros",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "511006",
        "name": "Depreciaciones",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "511007",
        "name": "Mantenimiento y Reparaciones",
        "parent_code": "5110",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # Gastos de Ventas
    {
        "code": "5120",
        "name": "GASTOS DE VENTAS",
        "parent_code": "51",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "512001",
        "name": "Comisiones de Ventas",
        "parent_code": "5120",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "512002",
        "name": "Publicidad y Propaganda",
        "parent_code": "5120",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    
    # Gastos No Operacionales
    {
        "code": "52",
        "name": "GASTOS NO OPERACIONALES",
        "parent_code": "5",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.NON_OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "520001",
        "name": "Gastos Financieros",
        "parent_code": "52",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.NON_OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 3
    },
    {
        "code": "520002",
        "name": "Gastos Extraordinarios",
        "parent_code": "52",
        "account_type": AccountType.EXPENSE,
        "category": AccountCategory.NON_OPERATING_EXPENSE,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 3
    },
    
    # ==================== COSTOS ====================
    
    {
        "code": "6",
        "name": "COSTOS",
        "account_type": AccountType.COST,
        "category": AccountCategory.COST_OF_SALES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 1
    },
    {
        "code": "61",
        "name": "COSTO DE VENTAS",
        "parent_code": "6",
        "account_type": AccountType.COST,
        "category": AccountCategory.COST_OF_SALES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 2
    },
    {
        "code": "610001",
        "name": "Costo de Productos Vendidos",
        "parent_code": "61",
        "account_type": AccountType.COST,
        "category": AccountCategory.COST_OF_SALES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 3
    },
    {
        "code": "610002",
        "name": "Costo de Servicios Prestados",
        "parent_code": "61",
        "account_type": AccountType.COST,
        "category": AccountCategory.COST_OF_SALES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 3
    },
    
    # ==================== CUENTAS DE IMPUESTOS ESPECÍFICAS ====================
    
    {
        "code": "1350",
        "name": "IMPUESTOS POR COBRAR",
        "parent_code": "11",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": False,
        "level": 3
    },
    {
        "code": "135001",
        "name": "IVA por Cobrar",
        "parent_code": "1350",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "135002",
        "name": "Retenciones de IVA",
        "parent_code": "1350",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
    {
        "code": "135003",
        "name": "Retenciones de Renta",
        "parent_code": "1350",
        "account_type": AccountType.ASSET,
        "category": AccountCategory.TAXES,
        "cash_flow_category": CashFlowCategory.OPERATING,
        "allows_movements": True,
        "level": 4
    },
]

# =====================================================
# DIARIOS CONTABLES
# =====================================================

COMPANY_JOURNALS = [
    {
        "code": "VEN",
        "name": "Diario de Ventas",
        "type": JournalType.SALE,
        "sequence_prefix": "VEN",
        "default_account_code": "411001",  # Ventas de Productos
        "is_active": True
    },
    {
        "code": "COM",
        "name": "Diario de Compras",
        "type": JournalType.PURCHASE,
        "sequence_prefix": "COM",
        "default_account_code": "610001",  # Costo de Productos Vendidos
        "is_active": True
    },
    {
        "code": "CAJ",
        "name": "Diario de Caja",
        "type": JournalType.CASH,
        "sequence_prefix": "CAJ",
        "default_account_code": "111001",  # Caja General
        "is_active": True
    },
    {
        "code": "BAN",
        "name": "Diario de Bancos",
        "type": JournalType.BANK,
        "sequence_prefix": "BAN",
        "default_account_code": "111101",  # Banco Nacional - Cuenta Corriente
        "is_active": True
    },
    {
        "code": "GEN",
        "name": "Diario General",
        "type": JournalType.MISCELLANEOUS,
        "sequence_prefix": "GEN",
        "default_account_code": None,
        "is_active": True
    },
    {
        "code": "NOV",
        "name": "Diario de Nómina",
        "type": JournalType.MISCELLANEOUS,
        "sequence_prefix": "NOM",
        "default_account_code": "511001",  # Sueldos y Salarios
        "is_active": True
    },
    {
        "code": "DEP",
        "name": "Diario de Depreciaciones",
        "type": JournalType.MISCELLANEOUS,
        "sequence_prefix": "DEP",
        "default_account_code": "511006",  # Depreciaciones
        "is_active": True
    }
]


# =====================================================
# FUNCIONES DE CREACIÓN
# =====================================================

async def create_accounts_hierarchy(session: AsyncSession, accounts_data: list, created_by_id: Optional[uuid.UUID] = None):
    """Crear las cuentas en orden jerárquico"""
    logger.info("🏗️ Creando plan de cuentas completo...")
    
    created_accounts = {}
    accounts_created = 0
    
    # Ordenar cuentas por nivel y código para crear padres antes que hijos
    sorted_accounts = sorted(accounts_data, key=lambda x: (x.get('level', 1), x['code']))
    
    for account_data in sorted_accounts:
        code = account_data['code']
        
        # Verificar si la cuenta ya existe
        existing_account = await session.scalar(
            select(Account).where(Account.code == code)
        )
        
        if existing_account:
            created_accounts[code] = existing_account
            continue
        
        # Buscar cuenta padre si existe
        parent = None
        if 'parent_code' in account_data:
            parent_code = account_data['parent_code']
            if parent_code in created_accounts:
                parent = created_accounts[parent_code]
            else:
                logger.warning(f"⚠️ Cuenta padre {parent_code} no encontrada para {code}")
                continue
        
        # Crear la cuenta
        account = Account(
            code=code,
            name=account_data['name'],
            account_type=account_data['account_type'],
            category=account_data.get('category'),
            cash_flow_category=account_data.get('cash_flow_category'),
            parent_id=parent.id if parent else None,
            level=account_data.get('level', 1),
            allows_movements=account_data.get('allows_movements', True),
            requires_third_party=account_data.get('requires_third_party', False),
            requires_cost_center=account_data.get('requires_cost_center', False),
            allows_reconciliation=account_data.get('allows_reconciliation', False),
            is_active=True,
            created_by_id=created_by_id
        )
        
        session.add(account)
        await session.flush()  # Para obtener el ID
        
        created_accounts[code] = account
        accounts_created += 1
        
        if accounts_created % 10 == 0:
            logger.info(f"✅ {accounts_created} cuentas creadas...")
    
    await session.commit()
    logger.info(f"✅ Plan de cuentas completo creado: {accounts_created} cuentas")
    return created_accounts


async def create_company_journals(session: AsyncSession, journals_data: list, accounts: dict, created_by_id: Optional[uuid.UUID] = None):
    """Crear los diarios contables necesarios"""
    logger.info("📚 Creando diarios contables...")
    
    created_journals = []
    
    for journal_data in journals_data:
        # Verificar si el diario ya existe
        existing_journal = await session.scalar(
            select(Journal).where(Journal.code == journal_data['code'])
        )
        
        if existing_journal:
            created_journals.append(existing_journal)
            continue
        
        # Buscar cuenta por defecto si se especifica
        default_account = None
        if journal_data.get('default_account_code'):
            default_account = accounts.get(journal_data['default_account_code'])
        
        # Crear el diario
        journal = Journal(
            code=journal_data['code'],
            name=journal_data['name'],
            type=journal_data['type'],
            sequence_prefix=journal_data['sequence_prefix'],
            default_account_id=default_account.id if default_account else None,
            is_active=journal_data.get('is_active', True),
            created_by_id=created_by_id
        )
        
        session.add(journal)
        created_journals.append(journal)
    
    await session.commit()
    logger.info(f"✅ {len(created_journals)} diarios creados")
    return created_journals


async def create_admin_user_if_not_exists(session: AsyncSession):
    """Crear usuario administrador si no existe"""
    admin_email = "admin@contable.com"
    
    existing_admin = await session.scalar(
        select(User).where(User.email == admin_email)
    )
    
    if existing_admin:
        logger.info("👤 Usuario administrador ya existe")
        return existing_admin
    
    # Crear usuario administrador
    admin_user = User(
        username="admin",
        email=admin_email,
        full_name="Administrador del Sistema",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LTaPrtv3/1Zp4j1Zm",  # password123
        is_active=True,
        is_superuser=True
    )
    
    session.add(admin_user)
    await session.commit()
    
    logger.info("✅ Usuario administrador creado (admin@contable.com / password123)")
    return admin_user


async def setup_complete_company():
    """Configurar empresa completa"""
    logger.info("🏢 INICIANDO CONFIGURACIÓN COMPLETA DE EMPRESA")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Crear usuario administrador
            admin_user = await create_admin_user_if_not_exists(session)
            
            # 2. Crear plan de cuentas completo
            accounts = await create_accounts_hierarchy(
                session, 
                COMPLETE_CHART_OF_ACCOUNTS, 
                admin_user.id
            )
            
            # 3. Crear diarios contables
            journals = await create_company_journals(
                session, 
                COMPANY_JOURNALS, 
                accounts, 
                admin_user.id
            )
            
            logger.info("🎉 CONFIGURACIÓN COMPLETA EXITOSA")
            logger.info("=" * 60)
            logger.info("📊 RESUMEN:")
            logger.info(f"   • {len(accounts)} cuentas contables creadas")
            logger.info(f"   • {len(journals)} diarios contables creados")
            logger.info(f"   • Usuario administrador configurado")
            logger.info("")
            logger.info("🚀 LA EMPRESA ESTÁ LISTA PARA OPERACIÓN")
            logger.info("   • Crear terceros (clientes/proveedores)")
            logger.info("   • Registrar facturas de venta y compra")
            logger.info("   • Procesar pagos y cobros")
            logger.info("   • Generar reportes contables")
            
            return {
                "success": True,
                "accounts_created": len(accounts),
                "journals_created": len(journals),
                "admin_user": admin_user.email
            }
            
        except Exception as e:
            logger.error(f"❌ Error en configuración: {str(e)}")
            await session.rollback()
            raise


def main():
    """Función principal"""
    print("🏢 CONFIGURACIÓN COMPLETA DE EMPRESA CONTABLE")
    print("=" * 60)
    print("Este script configurará:")
    print("• Plan de cuentas completo (Activos, Pasivos, Patrimonio, Ingresos, Gastos)")
    print("• Diarios contables necesarios")
    print("• Usuario administrador")
    print("• Configuraciones por defecto")
    print("")
    print("⚠️  IMPORTANTE: Esto creará muchos registros en la base de datos")
    print("")
    
    response = input("¿Deseas continuar con la configuración completa? (y/N): ")
    
    if response.lower() not in ['y', 'yes', 'sí', 's']:
        print("❌ Configuración cancelada")
        return
    
    try:
        result = asyncio.run(setup_complete_company())
        
        if result["success"]:
            print("")
            print("🎉 ¡CONFIGURACIÓN EXITOSA!")
            print(f"✅ {result['accounts_created']} cuentas creadas")
            print(f"✅ {result['journals_created']} diarios creados") 
            print(f"✅ Usuario: {result['admin_user']}")
            print("")
            print("🚀 Puedes empezar a usar el sistema contable")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return


if __name__ == "__main__":
    main()
