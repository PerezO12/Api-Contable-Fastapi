# 🎯 Casos de Uso y Ejemplos

## Descripción General

Esta sección proporciona ejemplos prácticos y casos de uso reales del sistema de reportes financieros. Incluye escenarios completos, flujos de trabajo típicos, y ejemplos de código para diferentes tipos de usuarios y necesidades empresariales.

## Casos de Uso por Rol

### 👔 **Contador General**

#### Preparación de Estados Financieros Mensuales

**Escenario:** Preparar estados financieros completos al cierre mensual.

**Flujo de trabajo:**
1. Verificar integridad contable
2. Generar Balance de Comprobación
3. Preparar Balance General
4. Generar Estado de Resultados
5. Exportar reportes para revisión

**Implementación:**

```python
import asyncio
import aiohttp
from datetime import date, datetime

class MonthlyFinancialReports:
    def __init__(self, api_base_url: str, auth_token: str):
        self.base_url = api_base_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    async def generate_monthly_package(self, year: int, month: int):
        """Generar paquete completo de reportes mensuales"""
        
        # Calcular fechas del período
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        async with aiohttp.ClientSession() as session:
            # 1. Verificar integridad contable
            integrity_check = await self.check_integrity(session, end_date)
            if not integrity_check["overall_integrity"]:
                raise ValueError("Integridad contable comprometida")
            
            # 2. Generar reportes principales
            reports = await asyncio.gather(
                self.generate_trial_balance(session, end_date),
                self.generate_balance_sheet(session, end_date),
                self.generate_income_statement(session, start_date, end_date)
            )
            
            # 3. Exportar a PDF para archivo
            exports = await asyncio.gather(
                self.export_report(session, "trial_balance", "pdf", {
                    "as_of_date": end_date.isoformat()
                }),
                self.export_report(session, "balance_sheet", "pdf", {
                    "as_of_date": end_date.isoformat()
                }),
                self.export_report(session, "income_statement", "pdf", {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                })
            )
            
            return {
                "period": f"{year}-{month:02d}",
                "integrity_check": integrity_check,
                "reports": {
                    "trial_balance": reports[0],
                    "balance_sheet": reports[1],
                    "income_statement": reports[2]
                },
                "exports": exports
            }
    
    async def check_integrity(self, session, as_of_date):
        """Verificar integridad contable"""
        url = f"{self.base_url}/reports/accounting-integrity"
        params = {"as_of_date": as_of_date.isoformat()}
        
        async with session.get(url, headers=self.headers, params=params) as response:
            return await response.json()
    
    async def generate_trial_balance(self, session, as_of_date):
        """Generar Balance de Comprobación"""
        url = f"{self.base_url}/reports/trial-balance"
        params = {
            "as_of_date": as_of_date.isoformat(),
            "include_zero_balances": False
        }
        
        async with session.get(url, headers=self.headers, params=params) as response:
            return await response.json()
    
    async def generate_balance_sheet(self, session, as_of_date):
        """Generar Balance General"""
        url = f"{self.base_url}/reports/balance-sheet"
        params = {
            "as_of_date": as_of_date.isoformat(),
            "include_zero_balances": False
        }
        
        async with session.get(url, headers=self.headers, params=params) as response:
            return await response.json()
    
    async def generate_income_statement(self, session, start_date, end_date):
        """Generar Estado de Resultados"""
        url = f"{self.base_url}/reports/income-statement"
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "include_zero_balances": False
        }
        
        async with session.get(url, headers=self.headers, params=params) as response:
            return await response.json()
    
    async def export_report(self, session, report_type, format, parameters):
        """Exportar reporte a formato específico"""
        url = f"{self.base_url}/reports/export"
        payload = {
            "report_type": report_type,
            "format": format,
            "parameters": parameters,
            "template": "standard"
        }
        
        async with session.post(url, headers=self.headers, json=payload) as response:
            return await response.json()

# Uso del caso
async def main():
    reports = MonthlyFinancialReports(
        "https://api.contable.com/api/v1",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
    
    monthly_package = await reports.generate_monthly_package(2025, 6)
    print(f"Reportes generados para: {monthly_package['period']}")
    print(f"Integridad: {monthly_package['integrity_check']['overall_integrity']}")
```

---

### 👨‍💼 **Gerente Financiero**

#### Dashboard Ejecutivo en Tiempo Real

**Escenario:** Monitoreo continuo de KPIs financieros clave.

**Implementación:**

```javascript
class FinancialDashboard {
    constructor(apiBaseUrl, authToken) {
        this.baseUrl = apiBaseUrl;
        this.headers = {
            'Authorization': `Bearer ${authToken}`,
            'Content-Type': 'application/json'
        };
    }
    
    async getDashboardData() {
        const today = new Date().toISOString().split('T')[0];
        const firstDayOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
            .toISOString().split('T')[0];
        
        try {
            // Generar reportes unificados para dashboard
            const [balanceData, incomeData, cashFlowData] = await Promise.all([
                this.getUnifiedReport('balance-general', firstDayOfMonth, today),
                this.getUnifiedReport('perdidas-ganancias', firstDayOfMonth, today),
                this.getUnifiedReport('flujo-efectivo', firstDayOfMonth, today)
            ]);
            
            return this.processKPIs(balanceData, incomeData, cashFlowData);
        } catch (error) {
            console.error('Error generating dashboard:', error);
            throw error;
        }
    }
    
    async getUnifiedReport(reportType, fromDate, toDate) {
        const url = `${this.baseUrl}/reports/${reportType}`;
        const params = new URLSearchParams({
            project_context: 'Dashboard Ejecutivo',
            from_date: fromDate,
            to_date: toDate,
            detail_level: 'bajo'
        });
        
        const response = await fetch(`${url}?${params}`, {
            headers: this.headers
        });
        
        if (!response.ok) {
            throw new Error(`Error fetching ${reportType}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    processKPIs(balanceData, incomeData, cashFlowData) {
        return {
            timestamp: new Date().toISOString(),
            financial_position: {
                total_assets: parseFloat(balanceData.table.totals.total_activos),
                total_liabilities: parseFloat(balanceData.table.totals.total_pasivos),
                equity: parseFloat(balanceData.table.totals.total_patrimonio),
                debt_to_equity_ratio: this.calculateDebtToEquity(balanceData)
            },
            profitability: {
                total_revenue: parseFloat(incomeData.table.totals.total_ingresos),
                total_expenses: parseFloat(incomeData.table.totals.total_gastos),
                net_profit: parseFloat(incomeData.table.totals.utilidad_neta),
                net_margin: this.calculateNetMargin(incomeData)
            },
            liquidity: {
                operating_cash_flow: parseFloat(cashFlowData.table.totals.flujo_operativo),
                cash_position: parseFloat(cashFlowData.table.totals.flujo_neto),
                liquidity_trend: this.assessLiquidityTrend(cashFlowData)
            },
            insights: [
                ...balanceData.narrative.key_insights,
                ...incomeData.narrative.key_insights,
                ...cashFlowData.narrative.key_insights
            ],
            recommendations: [
                ...balanceData.narrative.recommendations,
                ...incomeData.narrative.recommendations,
                ...cashFlowData.narrative.recommendations
            ]
        };
    }
    
    calculateDebtToEquity(balanceData) {
        const liabilities = parseFloat(balanceData.table.totals.total_pasivos);
        const equity = parseFloat(balanceData.table.totals.total_patrimonio);
        return equity > 0 ? (liabilities / equity).toFixed(2) : 'N/A';
    }
    
    calculateNetMargin(incomeData) {
        const revenue = parseFloat(incomeData.table.totals.total_ingresos);
        const netProfit = parseFloat(incomeData.table.totals.utilidad_neta);
        return revenue > 0 ? ((netProfit / revenue) * 100).toFixed(2) + '%' : 'N/A';
    }
    
    assessLiquidityTrend(cashFlowData) {
        const netFlow = parseFloat(cashFlowData.table.totals.flujo_neto);
        if (netFlow > 100000) return 'Excelente';
        if (netFlow > 50000) return 'Bueno';
        if (netFlow > 0) return 'Aceptable';
        return 'Preocupante';
    }
}

// Uso en aplicación React/Vue/Angular
async function updateDashboard() {
    const dashboard = new FinancialDashboard(
        'https://api.contable.com/api/v1',
        localStorage.getItem('authToken')
    );
    
    try {
        const kpis = await dashboard.getDashboardData();
        
        // Actualizar UI
        document.getElementById('total-assets').textContent = 
            new Intl.NumberFormat('es-ES', { 
                style: 'currency', 
                currency: 'EUR' 
            }).format(kpis.financial_position.total_assets);
        
        document.getElementById('net-margin').textContent = kpis.profitability.net_margin;
        document.getElementById('liquidity-trend').textContent = kpis.liquidity.liquidity_trend;
        
        // Actualizar insights y recomendaciones
        updateInsightsPanel(kpis.insights);
        updateRecommendationsPanel(kpis.recommendations);
        
    } catch (error) {
        console.error('Dashboard update failed:', error);
        showErrorMessage('Error actualizando dashboard financiero');
    }
}

// Actualizar cada 5 minutos
setInterval(updateDashboard, 5 * 60 * 1000);
```

---

### 🕵️ **Auditor Interno**

#### Análisis de Integridad y Cumplimiento

**Escenario:** Verificación mensual de integridad contable y detección de anomalías.

**Implementación:**

```python
import pandas as pd
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class AuditFinding:
    severity: str  # 'low', 'medium', 'high', 'critical'
    category: str
    description: str
    recommendation: str
    accounts_affected: List[str]

class AuditReportsAnalyzer:
    def __init__(self, api_client):
        self.api = api_client
        self.findings: List[AuditFinding] = []
    
    async def comprehensive_audit(self, audit_date: date) -> Dict[str, Any]:
        """Realizar auditoría integral de reportes financieros"""
        
        # 1. Verificar integridad básica
        integrity_check = await self.verify_accounting_integrity(audit_date)
        
        # 2. Análizar Balance de Comprobación
        trial_balance_analysis = await self.analyze_trial_balance(audit_date)
        
        # 3. Verificar consistencia en Balance General
        balance_sheet_analysis = await self.analyze_balance_sheet(audit_date)
        
        # 4. Analizar movimientos inusuales
        unusual_movements = await self.detect_unusual_movements(audit_date)
        
        # 5. Verificar completitud de registros
        completeness_check = await self.verify_completeness(audit_date)
        
        return {
            "audit_date": audit_date.isoformat(),
            "overall_score": self.calculate_audit_score(),
            "integrity_status": integrity_check,
            "findings": [
                trial_balance_analysis,
                balance_sheet_analysis,
                unusual_movements,
                completeness_check
            ],
            "recommendations": self.generate_audit_recommendations(),
            "critical_issues": [f for f in self.findings if f.severity == 'critical']
        }
    
    async def verify_accounting_integrity(self, audit_date: date) -> Dict[str, Any]:
        """Verificar integridad fundamental de la contabilidad"""
        response = await self.api.get(
            "/reports/accounting-integrity",
            params={"as_of_date": audit_date.isoformat()}
        )
        
        if not response["overall_integrity"]:
            self.findings.append(AuditFinding(
                severity='critical',
                category='integrity',
                description='Ecuación contable fundamental no balanceada',
                recommendation='Revisar y corregir asientos contables inmediatamente',
                accounts_affected=['ALL']
            ))
        
        return response
    
    async def analyze_trial_balance(self, audit_date: date) -> Dict[str, Any]:
        """Analizar Balance de Comprobación para detectar anomalías"""
        trial_balance = await self.api.get(
            "/reports/trial-balance",
            params={
                "as_of_date": audit_date.isoformat(),
                "include_zero_balances": True
            }
        )
        
        analysis = {
            "total_accounts": len(trial_balance["accounts"]),
            "balanced": trial_balance["is_balanced"],
            "zero_balance_accounts": 0,
            "unusual_balances": []
        }
        
        for account in trial_balance["accounts"]:
            # Detectar cuentas con saldo cero
            if float(account["closing_balance"]) == 0:
                analysis["zero_balance_accounts"] += 1
            
            # Detectar balances inusuales (saldo contrario a la naturaleza)
            balance = float(account["closing_balance"])
            normal_side = account["normal_balance_side"]
            
            if (normal_side == "debit" and balance < 0) or (normal_side == "credit" and balance > 0):
                analysis["unusual_balances"].append({
                    "account_code": account["account_code"],
                    "account_name": account["account_name"],
                    "balance": balance,
                    "expected_side": normal_side
                })
                
                self.findings.append(AuditFinding(
                    severity='medium',
                    category='unusual_balance',
                    description=f'Cuenta {account["account_code"]} tiene saldo contrario a su naturaleza',
                    recommendation='Revisar movimientos de la cuenta y corregir si es necesario',
                    accounts_affected=[account["account_code"]]
                ))
        
        return analysis
    
    async def analyze_balance_sheet(self, audit_date: date) -> Dict[str, Any]:
        """Analizar Balance General para verificar consistencia"""
        balance_sheet = await self.api.get(
            "/reports/balance-sheet",
            params={"as_of_date": audit_date.isoformat()}
        )
        
        analysis = {
            "equation_balanced": balance_sheet["is_balanced"],
            "total_assets": float(balance_sheet["total_assets"]),
            "total_liabilities_equity": float(balance_sheet["total_liabilities_equity"]),
            "difference": abs(float(balance_sheet["total_assets"]) - 
                            float(balance_sheet["total_liabilities_equity"]))
        }
        
        # Verificar ratios de alerta
        assets = analysis["total_assets"]
        liabilities = float(balance_sheet["liabilities"]["total"])
        equity = float(balance_sheet["equity"]["total"])
        
        if assets > 0:
            debt_ratio = liabilities / assets
            if debt_ratio > 0.8:  # Más del 80% de deuda
                self.findings.append(AuditFinding(
                    severity='high',
                    category='financial_risk',
                    description=f'Ratio de deuda elevado: {debt_ratio:.2%}',
                    recommendation='Evaluar estructura financiera y considerar reducción de deuda',
                    accounts_affected=['PASIVOS']
                ))
        
        return analysis
    
    async def detect_unusual_movements(self, audit_date: date) -> Dict[str, Any]:
        """Detectar movimientos inusuales en el período"""
        start_date = date(audit_date.year, audit_date.month, 1)
        
        general_ledger = await self.api.get(
            "/reports/general-ledger",
            params={
                "start_date": start_date.isoformat(),
                "end_date": audit_date.isoformat()
            }
        )
        
        unusual_movements = []
        
        for account in general_ledger["accounts"]:
            movements = account["movements"]
            
            if not movements:
                continue
            
            # Detectar movimientos de fin de mes inusuales
            last_day_movements = [
                m for m in movements 
                if m["date"] == audit_date.isoformat()
            ]
            
            if len(last_day_movements) > 5:  # Más de 5 movimientos el último día
                unusual_movements.append({
                    "account_code": account["account_code"],
                    "account_name": account["account_name"],
                    "last_day_movements": len(last_day_movements),
                    "concern": "Alto volumen de movimientos en último día del mes"
                })
            
            # Detectar movimientos muy grandes
            for movement in movements:
                amount = max(float(movement["debit_amount"]), float(movement["credit_amount"]))
                if amount > 100000:  # Movimientos > 100,000
                    unusual_movements.append({
                        "account_code": account["account_code"],
                        "date": movement["date"],
                        "amount": amount,
                        "description": movement["description"],
                        "concern": "Movimiento de alto valor"
                    })
        
        if unusual_movements:
            self.findings.append(AuditFinding(
                severity='medium',
                category='unusual_activity',
                description=f'Detectados {len(unusual_movements)} movimientos inusuales',
                recommendation='Revisar documentación soporte de movimientos identificados',
                accounts_affected=list(set([m["account_code"] for m in unusual_movements if "account_code" in m]))
            ))
        
        return {"unusual_movements": unusual_movements}
    
    async def verify_completeness(self, audit_date: date) -> Dict[str, Any]:
        """Verificar completitud de registros contables"""
        # Verificar que hay actividad contable en días laborables
        start_date = date(audit_date.year, audit_date.month, 1)
        
        general_ledger = await self.api.get(
            "/reports/general-ledger",
            params={
                "start_date": start_date.isoformat(),
                "end_date": audit_date.isoformat()
            }
        )
        
        # Crear DataFrame para análisis
        all_movements = []
        for account in general_ledger["accounts"]:
            for movement in account["movements"]:
                all_movements.append({
                    "date": movement["date"],
                    "account_code": account["account_code"],
                    "amount": max(float(movement["debit_amount"]), float(movement["credit_amount"]))
                })
        
        df = pd.DataFrame(all_movements)
        
        if df.empty:
            self.findings.append(AuditFinding(
                severity='critical',
                category='completeness',
                description='No se encontraron movimientos contables en el período',
                recommendation='Verificar que se están registrando todas las transacciones',
                accounts_affected=['ALL']
            ))
            return {"movement_days": 0, "total_movements": 0}
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Analizar patrones de actividad
        daily_activity = df.groupby(df['date'].dt.date).size()
        business_days = pd.bdate_range(start_date, audit_date)
        days_with_activity = len(daily_activity)
        expected_business_days = len(business_days)
        
        completeness_ratio = days_with_activity / expected_business_days if expected_business_days > 0 else 0
        
        if completeness_ratio < 0.7:  # Menos del 70% de días laborables con actividad
            self.findings.append(AuditFinding(
                severity='medium',
                category='completeness',
                description=f'Baja actividad contable: solo {days_with_activity} de {expected_business_days} días laborables',
                recommendation='Verificar procesos de registro diario de transacciones',
                accounts_affected=['PROCESO']
            ))
        
        return {
            "movement_days": days_with_activity,
            "expected_business_days": expected_business_days,
            "completeness_ratio": completeness_ratio,
            "total_movements": len(df)
        }
    
    def calculate_audit_score(self) -> int:
        """Calcular puntuación general de auditoría (0-100)"""
        base_score = 100
        
        for finding in self.findings:
            if finding.severity == 'critical':
                base_score -= 25
            elif finding.severity == 'high':
                base_score -= 15
            elif finding.severity == 'medium':
                base_score -= 10
            elif finding.severity == 'low':
                base_score -= 5
        
        return max(0, base_score)
    
    def generate_audit_recommendations(self) -> List[str]:
        """Generar recomendaciones consolidadas"""
        recommendations = []
        
        critical_findings = [f for f in self.findings if f.severity == 'critical']
        if critical_findings:
            recommendations.append("URGENTE: Corregir problemas críticos de integridad contable")
        
        high_findings = [f for f in self.findings if f.severity == 'high']
        if high_findings:
            recommendations.append("Priorizar resolución de problemas de alto riesgo")
        
        categories = set([f.category for f in self.findings])
        if 'unusual_balance' in categories:
            recommendations.append("Implementar controles adicionales para balances inusuales")
        
        if 'completeness' in categories:
            recommendations.append("Reforzar procesos de registro diario")
        
        return recommendations

# Uso del analizador de auditoría
async def run_monthly_audit():
    api_client = ReportsAPIClient("https://api.contable.com/api/v1", "token")
    auditor = AuditReportsAnalyzer(api_client)
    
    audit_results = await auditor.comprehensive_audit(date.today())
    
    print(f"Puntuación de Auditoría: {audit_results['overall_score']}/100")
    print(f"Problemas Críticos: {len(audit_results['critical_issues'])}")
    
    for recommendation in audit_results['recommendations']:
        print(f"• {recommendation}")
```

---

### 💼 **CFO / Director Financiero**

#### Análisis Estratégico Trimestral

**Escenario:** Preparación de presentación para junta directiva con análisis financiero integral.

**Implementación:**

```python
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date, timedelta
import json

class StrategicFinancialAnalysis:
    def __init__(self, api_client):
        self.api = api_client
        
    async def quarterly_board_report(self, quarter: int, year: int) -> Dict[str, Any]:
        """Generar reporte integral para junta directiva"""
        
        # Calcular fechas del trimestre
        quarter_dates = self.get_quarter_dates(quarter, year)
        previous_quarter_dates = self.get_quarter_dates(
            quarter - 1 if quarter > 1 else 4, 
            year if quarter > 1 else year - 1
        )
        
        # Generar análisis completo
        current_analysis = await self.comprehensive_analysis(
            quarter_dates['start'], quarter_dates['end']
        )
        
        previous_analysis = await self.comprehensive_analysis(
            previous_quarter_dates['start'], previous_quarter_dates['end']
        )
        
        # Calcular tendencias y variaciones
        trends = self.calculate_trends(current_analysis, previous_analysis)
        
        # Generar insights estratégicos
        strategic_insights = self.generate_strategic_insights(current_analysis, trends)
        
        return {
            "period": f"Q{quarter} {year}",
            "executive_summary": self.create_executive_summary(current_analysis, trends),
            "financial_highlights": current_analysis,
            "performance_trends": trends,
            "strategic_insights": strategic_insights,
            "risk_assessment": self.assess_financial_risks(current_analysis),
            "recommendations": self.strategic_recommendations(current_analysis, trends),
            "kpi_dashboard": self.create_kpi_dashboard(current_analysis),
            "charts_data": self.prepare_chart_data(current_analysis, previous_analysis)
        }
    
    async def comprehensive_analysis(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Análisis financiero integral usando API unificada"""
        
        # Generar reportes unificados con análisis automático
        balance_report = await self.api.get(
            "/reports/balance-general",
            params={
                "project_context": "Análisis Estratégico",
                "from_date": start_date.isoformat(),
                "to_date": end_date.isoformat(),
                "detail_level": "medio"
            }
        )
        
        income_report = await self.api.get(
            "/reports/perdidas-ganancias",
            params={
                "project_context": "Análisis Estratégico",
                "from_date": start_date.isoformat(),
                "to_date": end_date.isoformat(),
                "detail_level": "medio"
            }
        )
        
        cash_flow_report = await self.api.get(
            "/reports/flujo-efectivo",
            params={
                "project_context": "Análisis Estratégico",
                "from_date": start_date.isoformat(),
                "to_date": end_date.isoformat(),
                "detail_level": "medio"
            }
        )
        
        return {
            "period": {"start": start_date, "end": end_date},
            "balance_sheet": {
                "data": balance_report,
                "metrics": self.extract_balance_metrics(balance_report)
            },
            "income_statement": {
                "data": income_report,
                "metrics": self.extract_income_metrics(income_report)
            },
            "cash_flow": {
                "data": cash_flow_report,
                "metrics": self.extract_cash_metrics(cash_flow_report)
            }
        }
    
    def extract_balance_metrics(self, balance_report: Dict) -> Dict[str, float]:
        """Extraer métricas clave del balance"""
        totals = balance_report["table"]["totals"]
        
        total_assets = float(totals["total_activos"])
        total_liabilities = float(totals["total_pasivos"])
        total_equity = float(totals["total_patrimonio"])
        
        return {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
            "debt_to_equity": total_liabilities / total_equity if total_equity > 0 else 0,
            "equity_ratio": total_equity / total_assets if total_assets > 0 else 0,
            "debt_ratio": total_liabilities / total_assets if total_assets > 0 else 0
        }
    
    def extract_income_metrics(self, income_report: Dict) -> Dict[str, float]:
        """Extraer métricas clave del estado de resultados"""
        totals = income_report["table"]["totals"]
        
        revenue = float(totals["total_ingresos"])
        expenses = float(totals["total_gastos"])
        net_profit = float(totals["utilidad_neta"])
        
        return {
            "total_revenue": revenue,
            "total_expenses": expenses,
            "net_profit": net_profit,
            "gross_margin": (revenue - expenses) / revenue * 100 if revenue > 0 else 0,
            "net_margin": net_profit / revenue * 100 if revenue > 0 else 0,
            "expense_ratio": expenses / revenue * 100 if revenue > 0 else 0
        }
    
    def extract_cash_metrics(self, cash_report: Dict) -> Dict[str, float]:
        """Extraer métricas de flujo de efectivo"""
        totals = cash_report["table"]["totals"]
        
        return {
            "operating_cash_flow": float(totals["flujo_operativo"]),
            "investing_cash_flow": float(totals.get("flujo_inversion", 0)),
            "financing_cash_flow": float(totals.get("flujo_financiamiento", 0)),
            "net_cash_flow": float(totals["flujo_neto"])
        }
    
    def calculate_trends(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Calcular tendencias entre períodos"""
        trends = {}
        
        # Tendencias de balance
        current_balance = current["balance_sheet"]["metrics"]
        previous_balance = previous["balance_sheet"]["metrics"]
        
        trends["balance"] = {
            "asset_growth": self.calculate_growth(
                current_balance["total_assets"], 
                previous_balance["total_assets"]
            ),
            "equity_growth": self.calculate_growth(
                current_balance["total_equity"], 
                previous_balance["total_equity"]
            ),
            "debt_trend": current_balance["debt_ratio"] - previous_balance["debt_ratio"]
        }
        
        # Tendencias de ingresos
        current_income = current["income_statement"]["metrics"]
        previous_income = previous["income_statement"]["metrics"]
        
        trends["income"] = {
            "revenue_growth": self.calculate_growth(
                current_income["total_revenue"], 
                previous_income["total_revenue"]
            ),
            "profit_growth": self.calculate_growth(
                current_income["net_profit"], 
                previous_income["net_profit"]
            ),
            "margin_trend": current_income["net_margin"] - previous_income["net_margin"]
        }
        
        # Tendencias de efectivo
        current_cash = current["cash_flow"]["metrics"]
        previous_cash = previous["cash_flow"]["metrics"]
        
        trends["cash_flow"] = {
            "operating_flow_growth": self.calculate_growth(
                current_cash["operating_cash_flow"], 
                previous_cash["operating_cash_flow"]
            ),
            "net_flow_change": current_cash["net_cash_flow"] - previous_cash["net_cash_flow"]
        }
        
        return trends
    
    def calculate_growth(self, current: float, previous: float) -> float:
        """Calcular tasa de crecimiento porcentual"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / abs(previous)) * 100
    
    def generate_strategic_insights(self, analysis: Dict, trends: Dict) -> List[Dict[str, str]]:
        """Generar insights estratégicos basados en análisis"""
        insights = []
        
        # Insight de crecimiento
        revenue_growth = trends["income"]["revenue_growth"]
        if revenue_growth > 10:
            insights.append({
                "category": "Growth",
                "insight": f"Crecimiento excepcional de ingresos del {revenue_growth:.1f}%",
                "implication": "Oportunidad para acelerar inversiones estratégicas",
                "action": "Evaluar expansión de capacidades y mercados"
            })
        elif revenue_growth < -5:
            insights.append({
                "category": "Risk",
                "insight": f"Declive en ingresos del {abs(revenue_growth):.1f}%",
                "implication": "Requiere acción correctiva inmediata",
                "action": "Revisar estrategia comercial y reducir costos"
            })
        
        # Insight de rentabilidad
        net_margin = analysis["income_statement"]["metrics"]["net_margin"]
        if net_margin > 20:
            insights.append({
                "category": "Profitability",
                "insight": f"Margen neto excepcional del {net_margin:.1f}%",
                "implication": "Posición competitiva muy fuerte",
                "action": "Mantener eficiencia operativa y considerar inversión en crecimiento"
            })
        elif net_margin < 5:
            insights.append({
                "category": "Efficiency",
                "insight": f"Margen neto bajo del {net_margin:.1f}%",
                "implication": "Presión en rentabilidad",
                "action": "Optimizar estructura de costos y mejorar pricing"
            })
        
        # Insight de apalancamiento
        debt_ratio = analysis["balance_sheet"]["metrics"]["debt_ratio"]
        if debt_ratio > 0.6:
            insights.append({
                "category": "Risk",
                "insight": f"Alto nivel de apalancamiento ({debt_ratio:.1%})",
                "implication": "Riesgo financiero elevado",
                "action": "Considerar reducción de deuda y mejorar estructura de capital"
            })
        elif debt_ratio < 0.3:
            insights.append({
                "category": "Opportunity",
                "insight": f"Bajo apalancamiento ({debt_ratio:.1%})",
                "implication": "Capacidad de deuda infrautilizada",
                "action": "Evaluar oportunidades de inversión financiadas con deuda"
            })
        
        return insights
    
    def assess_financial_risks(self, analysis: Dict) -> Dict[str, Any]:
        """Evaluar riesgos financieros principales"""
        balance_metrics = analysis["balance_sheet"]["metrics"]
        income_metrics = analysis["income_statement"]["metrics"]
        cash_metrics = analysis["cash_flow"]["metrics"]
        
        risks = {
            "liquidity": {
                "level": "low",
                "description": "Posición de liquidez adecuada"
            },
            "leverage": {
                "level": "low",
                "description": "Nivel de deuda manejable"
            },
            "profitability": {
                "level": "low",
                "description": "Rentabilidad estable"
            },
            "operational": {
                "level": "low",
                "description": "Operaciones eficientes"
            }
        }
        
        # Evaluar riesgo de liquidez
        if cash_metrics["operating_cash_flow"] < 0:
            risks["liquidity"] = {
                "level": "high",
                "description": "Flujo operativo negativo indica problemas de liquidez"
            }
        elif cash_metrics["net_cash_flow"] < 0:
            risks["liquidity"] = {
                "level": "medium",
                "description": "Flujo neto negativo requiere monitoreo"
            }
        
        # Evaluar riesgo de apalancamiento
        if balance_metrics["debt_ratio"] > 0.7:
            risks["leverage"] = {
                "level": "high",
                "description": "Alto apalancamiento aumenta riesgo financiero"
            }
        elif balance_metrics["debt_ratio"] > 0.5:
            risks["leverage"] = {
                "level": "medium",
                "description": "Apalancamiento moderado requiere atención"
            }
        
        # Evaluar riesgo de rentabilidad
        if income_metrics["net_margin"] < 0:
            risks["profitability"] = {
                "level": "high",
                "description": "Pérdidas operativas amenazan sostenibilidad"
            }
        elif income_metrics["net_margin"] < 5:
            risks["profitability"] = {
                "level": "medium",
                "description": "Márgenes bajos limitan capacidad de inversión"
            }
        
        return risks
    
    def strategic_recommendations(self, analysis: Dict, trends: Dict) -> List[str]:
        """Generar recomendaciones estratégicas"""
        recommendations = []
        
        # Basado en narrativa automática de reportes
        balance_narrative = analysis["balance_sheet"]["data"]["narrative"]
        income_narrative = analysis["income_statement"]["data"]["narrative"]
        cash_narrative = analysis["cash_flow"]["data"]["narrative"]
        
        # Combinar recomendaciones de todos los reportes
        all_recommendations = (
            balance_narrative["recommendations"] +
            income_narrative["recommendations"] +
            cash_narrative["recommendations"]
        )
        
        # Agregar recomendaciones estratégicas específicas
        revenue_growth = trends["income"]["revenue_growth"]
        if revenue_growth > 15:
            recommendations.append(
                "Aprovechar momento de crecimiento para inversiones estratégicas de largo plazo"
            )
        
        debt_ratio = analysis["balance_sheet"]["metrics"]["debt_ratio"]
        if debt_ratio < 0.3 and revenue_growth > 10:
            recommendations.append(
                "Considerar financiamiento para acelerar crecimiento dada la sólida posición financiera"
            )
        
        # Eliminar duplicados y combinar
        unique_recommendations = list(set(all_recommendations + recommendations))
        
        return unique_recommendations[:5]  # Top 5 recomendaciones
    
    def create_kpi_dashboard(self, analysis: Dict) -> Dict[str, Any]:
        """Crear dashboard de KPIs ejecutivos"""
        balance_metrics = analysis["balance_sheet"]["metrics"]
        income_metrics = analysis["income_statement"]["metrics"]
        cash_metrics = analysis["cash_flow"]["metrics"]
        
        return {
            "financial_strength": {
                "equity_ratio": balance_metrics["equity_ratio"],
                "debt_to_equity": balance_metrics["debt_to_equity"],
                "status": self.assess_financial_strength(balance_metrics)
            },
            "profitability": {
                "net_margin": income_metrics["net_margin"],
                "revenue": income_metrics["total_revenue"],
                "status": self.assess_profitability(income_metrics)
            },
            "liquidity": {
                "operating_cash_flow": cash_metrics["operating_cash_flow"],
                "net_cash_flow": cash_metrics["net_cash_flow"],
                "status": self.assess_liquidity(cash_metrics)
            },
            "efficiency": {
                "expense_ratio": income_metrics["expense_ratio"],
                "asset_utilization": income_metrics["total_revenue"] / balance_metrics["total_assets"] if balance_metrics["total_assets"] > 0 else 0,
                "status": self.assess_efficiency(income_metrics, balance_metrics)
            }
        }
    
    def assess_financial_strength(self, metrics: Dict) -> str:
        """Evaluar fortaleza financiera"""
        if metrics["equity_ratio"] > 0.6 and metrics["debt_to_equity"] < 0.5:
            return "Excelente"
        elif metrics["equity_ratio"] > 0.4 and metrics["debt_to_equity"] < 1.0:
            return "Buena"
        elif metrics["equity_ratio"] > 0.2 and metrics["debt_to_equity"] < 2.0:
            return "Aceptable"
        else:
            return "Preocupante"
    
    def assess_profitability(self, metrics: Dict) -> str:
        """Evaluar rentabilidad"""
        if metrics["net_margin"] > 15:
            return "Excelente"
        elif metrics["net_margin"] > 10:
            return "Buena"
        elif metrics["net_margin"] > 5:
            return "Aceptable"
        else:
            return "Preocupante"
    
    def assess_liquidity(self, metrics: Dict) -> str:
        """Evaluar liquidez"""
        if metrics["operating_cash_flow"] > 50000 and metrics["net_cash_flow"] > 0:
            return "Excelente"
        elif metrics["operating_cash_flow"] > 0 and metrics["net_cash_flow"] > -10000:
            return "Buena"
        elif metrics["operating_cash_flow"] > -10000:
            return "Aceptable"
        else:
            return "Preocupante"
    
    def assess_efficiency(self, income_metrics: Dict, balance_metrics: Dict) -> str:
        """Evaluar eficiencia operativa"""
        expense_ratio = income_metrics["expense_ratio"]
        if expense_ratio < 70:
            return "Excelente"
        elif expense_ratio < 80:
            return "Buena"
        elif expense_ratio < 90:
            return "Aceptable"
        else:
            return "Preocupante"
    
    def create_executive_summary(self, analysis: Dict, trends: Dict) -> str:
        """Crear resumen ejecutivo automático"""
        balance_narrative = analysis["balance_sheet"]["data"]["narrative"]["executive_summary"]
        income_narrative = analysis["income_statement"]["data"]["narrative"]["executive_summary"]
        
        revenue_growth = trends["income"]["revenue_growth"]
        profit_growth = trends["income"]["profit_growth"]
        
        growth_text = ""
        if revenue_growth > 10:
            growth_text = f"con un crecimiento excepcional de ingresos del {revenue_growth:.1f}%"
        elif revenue_growth > 0:
            growth_text = f"con crecimiento positivo de ingresos del {revenue_growth:.1f}%"
        else:
            growth_text = f"enfrentando un declive en ingresos del {abs(revenue_growth):.1f}%"
        
        return f"""
        El trimestre muestra una empresa {growth_text}. {balance_narrative} 
        {income_narrative} Las tendencias de rentabilidad muestran un 
        {'crecimiento' if profit_growth > 0 else 'declive'} del {abs(profit_growth):.1f}% 
        en utilidades comparado con el trimestre anterior.
        """.strip()
    
    def get_quarter_dates(self, quarter: int, year: int) -> Dict[str, date]:
        """Obtener fechas de inicio y fin de trimestre"""
        start_month = (quarter - 1) * 3 + 1
        if quarter == 4:
            end_month = 12
            end_day = 31
        else:
            end_month = quarter * 3
            end_day = 30 if end_month in [4, 6, 9] else 31
        
        return {
            "start": date(year, start_month, 1),
            "end": date(year, end_month, end_day)
        }
    
    def prepare_chart_data(self, current: Dict, previous: Dict) -> Dict[str, Any]:
        """Preparar datos para gráficos de la presentación"""
        return {
            "revenue_comparison": {
                "current": current["income_statement"]["metrics"]["total_revenue"],
                "previous": previous["income_statement"]["metrics"]["total_revenue"]
            },
            "profit_margins": {
                "current": current["income_statement"]["metrics"]["net_margin"],
                "previous": previous["income_statement"]["metrics"]["net_margin"]
            },
            "balance_composition": {
                "assets": current["balance_sheet"]["metrics"]["total_assets"],
                "liabilities": current["balance_sheet"]["metrics"]["total_liabilities"],
                "equity": current["balance_sheet"]["metrics"]["total_equity"]
            }
        }

# Uso para junta directiva
async def generate_board_presentation():
    api_client = ReportsAPIClient("https://api.contable.com/api/v1", "token")
    strategic_analysis = StrategicFinancialAnalysis(api_client)
    
    # Generar reporte Q2 2025
    board_report = await strategic_analysis.quarterly_board_report(2, 2025)
    
    # Guardar como JSON para integración con herramientas de presentación
    with open("board_report_q2_2025.json", "w") as f:
        json.dump(board_report, f, indent=2, default=str)
    
    print("Reporte de junta directiva generado:")
    print(f"Período: {board_report['period']}")
    print(f"Resumen: {board_report['executive_summary']}")
    print(f"Insights estratégicos: {len(board_report['strategic_insights'])}")
    print(f"Recomendaciones: {len(board_report['recommendations'])}")
```

## Integración con Herramientas Externas

### Excel/Google Sheets

```python
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

async def export_to_excel(report_data: Dict, filename: str):
    """Exportar datos de reporte a Excel con formato profesional"""
    
    wb = openpyxl.Workbook()
    
    # Hoja de Balance General
    ws_balance = wb.active
    ws_balance.title = "Balance General"
    
    # Headers con formato
    headers = ["Código", "Cuenta", "Saldo Inicial", "Movimientos", "Saldo Final"]
    for col, header in enumerate(headers, 1):
        cell = ws_balance.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    
    # Datos del balance
    row = 2
    for section in report_data["table"]["sections"]:
        # Título de sección
        ws_balance.cell(row=row, column=1, value=section["section_name"]).font = Font(bold=True)
        row += 1
        
        # Items de la sección
        for item in section["items"]:
            ws_balance.cell(row=row, column=1, value=item["account_code"])
            ws_balance.cell(row=row, column=2, value=item["account_name"])
            ws_balance.cell(row=row, column=3, value=float(item["opening_balance"]))
            ws_balance.cell(row=row, column=4, value=float(item["movements"]))
            ws_balance.cell(row=row, column=5, value=float(item["closing_balance"]))
            row += 1
        
        # Total de sección
        ws_balance.cell(row=row, column=2, value=f"Total {section['section_name']}")
        ws_balance.cell(row=row, column=5, value=float(section["total"]))
        ws_balance[f"B{row}"].font = Font(bold=True)
        ws_balance[f"E{row}"].font = Font(bold=True)
        row += 2
    
    wb.save(filename)
```

### Power BI/Tableau

```python
import requests
import json

class BIConnector:
    def __init__(self, api_client):
        self.api = api_client
    
    async def create_powerbi_dataset(self):
        """Crear dataset para Power BI con estructura optimizada"""
        
        # Obtener datos de múltiples períodos
        periods = []
        for month in range(1, 7):  # Primeros 6 meses del año
            start_date = date(2025, month, 1)
            end_date = date(2025, month, 28)  # Simplificado
            
            income_data = await self.api.get("/reports/perdidas-ganancias", params={
                "from_date": start_date.isoformat(),
                "to_date": end_date.isoformat(),
                "detail_level": "medio"
            })
            
            periods.append({
                "period": f"2025-{month:02d}",
                "revenue": float(income_data["table"]["totals"]["total_ingresos"]),
                "expenses": float(income_data["table"]["totals"]["total_gastos"]),
                "profit": float(income_data["table"]["totals"]["utilidad_neta"])
            })
        
        # Estructura para Power BI
        powerbi_data = {
            "name": "FinancialReports",
            "tables": [
                {
                    "name": "MonthlyPerformance",
                    "columns": [
                        {"name": "Period", "dataType": "string"},
                        {"name": "Revenue", "dataType": "double"},
                        {"name": "Expenses", "dataType": "double"},
                        {"name": "Profit", "dataType": "double"},
                        {"name": "ProfitMargin", "dataType": "double"}
                    ],
                    "rows": [
                        {
                            "Period": p["period"],
                            "Revenue": p["revenue"],
                            "Expenses": p["expenses"],
                            "Profit": p["profit"],
                            "ProfitMargin": (p["profit"] / p["revenue"] * 100) if p["revenue"] > 0 else 0
                        }
                        for p in periods
                    ]
                }
            ]
        }
        
        return powerbi_data
```

Estos casos de uso demuestran cómo el sistema de reportes financieros puede adaptarse a diferentes necesidades empresariales, desde el trabajo diario del contador hasta el análisis estratégico de alto nivel para la toma de decisiones ejecutivas.
