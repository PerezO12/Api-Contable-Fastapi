"""
Test de flujo completo end-to-end
Simula un flujo de trabajo contable real desde el inicio hasta los reportes
"""
import pytest
import uuid
from httpx import AsyncClient
from typing import Dict, Any, List
from datetime import date, timedelta

from tests.test_helpers import TestHelpers, TestDataFactory


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """Test de flujo completo de trabajo contable"""

    async def test_complete_accounting_workflow(
        self, 
        client: AsyncClient, 
        auth_headers_admin: Dict[str, str],
        auth_headers_contador: Dict[str, str]
    ):
        """
        Test completo que simula un flujo contable real:
        1. Setup inicial del plan de cuentas
        2. Creación de usuarios
        3. Registro de transacciones contables
        4. Generación de reportes
        5. Verificación de integridad
        """
        
        # =============================================
        # FASE 1: SETUP INICIAL DEL SISTEMA
        # =============================================
        
        # 1.1 Crear plan de cuentas básico
        print("📊 Creando plan de cuentas...")
        accounts_data = TestDataFactory.sample_accounts_data()
        created_accounts = {}
        
        for account_data in accounts_data:
            response = await client.post(
                "/api/v1/accounts/",
                json=account_data,
                headers=auth_headers_admin
            )
            assert response.status_code == 201
            account = response.json()
            created_accounts[account_data["code"]] = account
            print(f"   ✅ Cuenta creada: {account['code']} - {account['name']}")
        
        # 1.2 Verificar estadísticas iniciales
        stats_response = await client.get(
            "/api/v1/accounts/stats",
            headers=auth_headers_admin
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_accounts"] >= len(accounts_data)
        print(f"   📈 Total de cuentas creadas: {stats['total_accounts']}")
        
        # 1.3 Crear usuarios adicionales
        print("\n👥 Creando usuarios...")
        users_data = TestDataFactory.sample_users_data()
        created_users = []
        
        for user_data in users_data[:2]:  # Solo crear algunos usuarios
            try:
                response = await client.post(
                    "/api/v1/users/admin/create-user",
                    json=user_data,
                    headers=auth_headers_admin
                )
                if response.status_code == 200:
                    user = response.json()
                    created_users.append(user)
                    print(f"   ✅ Usuario creado: {user['email']} ({user['role']})")
            except Exception as e:
                print(f"   ⚠️  Usuario ya existe o error: {user_data['email']}")
        
        # =============================================
        # FASE 2: REGISTRO DE TRANSACCIONES
        # =============================================
        
        print("\n💰 Registrando transacciones contables...")
        journal_entries_scenarios = TestDataFactory.sample_journal_entries_scenarios()
        created_entries = []
        
        for scenario in journal_entries_scenarios:
            # Obtener IDs de las cuentas necesarias
            account_ids = []
            for code in scenario["accounts"]:
                if code in created_accounts:
                    account_ids.append(created_accounts[code]["id"])
            
            if len(account_ids) >= 2:
                try:
                    entry = await TestHelpers.create_test_journal_entry(
                        client=client,
                        auth_headers=auth_headers_contador,  # Usar contador para crear asientos
                        account_ids=account_ids,
                        amounts=scenario["amounts"],
                        reference=scenario["reference"],
                        description=scenario["description"]
                    )
                    created_entries.append(entry)
                    print(f"   ✅ Asiento creado: {entry['reference']} - {entry['description']}")
                    
                    # Aprobar y contabilizar cada asiento
                    posted_entry = await TestHelpers.approve_and_post_journal_entry(
                        client=client,
                        auth_headers=auth_headers_admin,
                        entry_id=entry["id"]
                    )
                    print(f"   📝 Asiento contabilizado: {posted_entry['entry_number']}")
                    
                except Exception as e:
                    print(f"   ❌ Error creando asiento {scenario['reference']}: {str(e)}")
        
        # 2.1 Verificar estadísticas de asientos
        je_stats_response = await client.get(
            "/api/v1/journal-entries/statistics/summary",
            headers=auth_headers_admin
        )
        assert je_stats_response.status_code == 200
        je_stats = je_stats_response.json()
        print(f"   📊 Total asientos registrados: {je_stats['total_entries']}")
        
        # =============================================
        # FASE 3: CONSULTAS Y VALIDACIONES
        # =============================================
        
        print("\n🔍 Realizando consultas y validaciones...")
        
        # 3.1 Consultar movimientos de una cuenta específica
        cash_account = created_accounts["1001"]  # Caja
        movements_response = await client.get(
            f"/api/v1/accounts/{cash_account['id']}/movements",
            headers=auth_headers_admin
        )
        assert movements_response.status_code == 200
        movements = movements_response.json()
        print(f"   💸 Movimientos en Caja: {len(movements['movements'])}")
        
        # 3.2 Obtener saldo actual de caja
        balance_response = await client.get(
            f"/api/v1/accounts/{cash_account['id']}/balance",
            headers=auth_headers_admin
        )
        assert balance_response.status_code == 200
        balance = balance_response.json()
        print(f"   💰 Saldo actual en Caja: ${balance['balance']}")
        
        # 3.3 Buscar asientos por referencia
        search_response = await client.get(
            "/api/v1/journal-entries/search?reference=CAP-001",
            headers=auth_headers_admin
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        print(f"   🔎 Asientos encontrados para CAP-001: {len(search_results)}")
        
        # =============================================
        # FASE 4: GENERACIÓN DE REPORTES
        # =============================================
        
        print("\n📈 Generando reportes financieros...")
        
        # 4.1 Balance General
        balance_sheet_response = await client.get(
            "/api/v1/reports/balance-sheet",
            headers=auth_headers_admin
        )
        assert balance_sheet_response.status_code == 200
        balance_sheet = balance_sheet_response.json()
        print(f"   📊 Balance General generado - Balanceado: {balance_sheet['is_balanced']}")
        print(f"      💰 Total Activos: ${balance_sheet['total_assets']}")
        print(f"      💳 Total Pasivos: ${balance_sheet['total_liabilities']}")
        print(f"      🏛️  Total Patrimonio: ${balance_sheet['total_equity']}")
        
        # 4.2 Estado de Resultados
        start_date, end_date = TestHelpers.generate_date_range(60)
        income_statement_response = await client.get(
            f"/api/v1/reports/income-statement?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_admin
        )
        assert income_statement_response.status_code == 200
        income_statement = income_statement_response.json()
        print(f"   📈 Estado de Resultados generado")
        print(f"      💹 Total Ingresos: ${income_statement['total_revenues']}")
        print(f"      💸 Total Gastos: ${income_statement['total_expenses']}")
        print(f"      💎 Resultado Neto: ${income_statement['net_income']}")
        
        # 4.3 Balance de Comprobación
        trial_balance_response = await client.get(
            "/api/v1/reports/trial-balance",
            headers=auth_headers_admin
        )
        assert trial_balance_response.status_code == 200
        trial_balance = trial_balance_response.json()
        print(f"   ⚖️  Balance de Comprobación - Balanceado: {trial_balance['is_balanced']}")
        print(f"      📊 Total Débitos: ${trial_balance['total_debits']}")
        print(f"      📊 Total Créditos: ${trial_balance['total_credits']}")
        
        # 4.4 Libro Mayor General
        ledger_response = await client.get(
            f"/api/v1/reports/general-ledger?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_admin
        )
        assert ledger_response.status_code == 200
        ledger = ledger_response.json()
        print(f"   📚 Libro Mayor generado - Cuentas: {len(ledger['accounts'])}")
        
        # 4.5 Análisis Financiero
        analysis_response = await client.get(
            "/api/v1/reports/financial-analysis",
            headers=auth_headers_admin
        )
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()
        print(f"   🎯 Análisis Financiero completado")
        
        # =============================================
        # FASE 5: VERIFICACIÓN DE INTEGRIDAD
        # =============================================
        
        print("\n🔍 Verificando integridad contable...")
        
        # 5.1 Verificación completa de integridad
        integrity_response = await client.get(
            "/api/v1/reports/accounting-integrity",
            headers=auth_headers_admin
        )
        assert integrity_response.status_code == 200
        integrity = integrity_response.json()
        
        print(f"   ✅ Verificación de integridad completada")
        print(f"      ⚖️  Balance General balanceado: {integrity['balance_sheet_balanced']}")
        print(f"      📊 Balance de Comprobación balanceado: {integrity['trial_balance_balanced']}")
        print(f"      🎯 Puntuación de integridad: {integrity['integrity_score']}")
        print(f"      ⚠️  Problemas encontrados: {len(integrity['issues_found'])}")
        
        # 5.2 Verificar que el sistema esté balanceado
        assert integrity["balance_sheet_balanced"] is True, "El Balance General debe estar balanceado"
        assert integrity["trial_balance_balanced"] is True, "El Balance de Comprobación debe estar balanceado"
        assert integrity["integrity_score"] >= 80, f"La puntuación de integridad debe ser >= 80, actual: {integrity['integrity_score']}"
        
        # =============================================
        # FASE 6: OPERACIONES AVANZADAS
        # =============================================
        
        print("\n🚀 Probando operaciones avanzadas...")
        
        # 6.1 Exportar reporte
        export_data = {
            "report_type": "balance_sheet",
            "format": "PDF",
            "as_of_date": date.today().isoformat(),
            "options": {
                "company_name": "Empresa de Prueba",
                "include_notes": True
            }
        }
        
        export_response = await client.post(
            "/api/v1/reports/export",
            json=export_data,
            headers=auth_headers_admin
        )
        assert export_response.status_code == 200
        export_result = export_response.json()
        print(f"   📄 Exportación iniciada: {export_result['export_id']}")
        
        # 6.2 Crear asiento de reversión
        if created_entries:
            first_entry = created_entries[0]
            reversal_response = await client.post(
                f"/api/v1/journal-entries/{first_entry['id']}/reverse?reason=Prueba de reversión",
                headers=auth_headers_admin
            )
            assert reversal_response.status_code == 200
            reversal = reversal_response.json()
            print(f"   🔄 Asiento de reversión creado: {reversal['reference']}")
        
        # 6.3 Resumen por tipo de cuenta
        asset_summary_response = await client.get(
            "/api/v1/reports/accounts-summary/ACTIVO",
            headers=auth_headers_admin
        )
        assert asset_summary_response.status_code == 200
        asset_summary = asset_summary_response.json()
        print(f"   🏢 Resumen de Activos: {len(asset_summary)} cuentas")
        
        # =============================================
        # FASE 7: VERIFICACIÓN FINAL
        # =============================================
        
        print("\n🎉 Verificación final del sistema...")
        
        # 7.1 Verificar estadísticas finales
        final_stats_response = await client.get(
            "/api/v1/users/admin/stats",
            headers=auth_headers_admin
        )
        assert final_stats_response.status_code == 200
        final_stats = final_stats_response.json()
        print(f"   👥 Usuarios totales: {final_stats['total_users']}")
        
        # 7.2 Verificar integridad una vez más
        final_integrity_response = await client.get(
            "/api/v1/reports/accounting-integrity",
            headers=auth_headers_admin
        )
        assert final_integrity_response.status_code == 200
        final_integrity = final_integrity_response.json()
        
        # 7.3 Assertions finales críticas
        assert final_integrity["balance_sheet_balanced"] is True
        assert final_integrity["trial_balance_balanced"] is True
        assert len(created_accounts) >= 10
        assert len(created_entries) >= 3
        assert balance_sheet["is_balanced"] is True
        assert trial_balance["is_balanced"] is True
        
        print("\n🎊 ¡Flujo de trabajo completo ejecutado exitosamente!")
        print("="*60)
        print("RESUMEN DEL TEST:")
        print(f"📊 Cuentas creadas: {len(created_accounts)}")
        print(f"💰 Asientos registrados: {len(created_entries)}")
        print(f"👥 Usuarios adicionales: {len(created_users)}")
        print(f"📈 Reportes generados: 5")
        print(f"✅ Sistema balanceado: {final_integrity['balance_sheet_balanced']}")
        print(f"🎯 Integridad: {final_integrity['integrity_score']}%")
        print("="*60)

    async def test_user_permissions_workflow(
        self,
        client: AsyncClient,
        auth_headers_admin: Dict[str, str],
        auth_headers_contador: Dict[str, str],
        auth_headers_readonly: Dict[str, str]
    ):
        """Test de flujo de permisos por rol de usuario"""
        
        print("\n🔐 Probando permisos por rol de usuario...")
        
        # Crear una cuenta para las pruebas
        test_account = await TestHelpers.create_test_account(
            client=client,
            auth_headers=auth_headers_admin,
            code="PERM-001",
            name="Cuenta de Prueba Permisos"
        )
        
        # =============================================
        # PERMISOS DE ADMINISTRADOR
        # =============================================
        
        print("👑 Verificando permisos de ADMINISTRADOR...")
        
        # Admin puede crear usuarios
        user_response = await client.post(
            "/api/v1/users/admin/create-user",
            json={
                "email": f"test-perm-{date.today().isoformat()}@test.com",
                "full_name": "Usuario Prueba Permisos",
                "role": "CONTADOR"
            },
            headers=auth_headers_admin
        )
        assert user_response.status_code == 200
        print("   ✅ Admin puede crear usuarios")
        
        # Admin puede ver estadísticas
        stats_response = await client.get(
            "/api/v1/users/admin/stats",
            headers=auth_headers_admin
        )
        assert stats_response.status_code == 200
        print("   ✅ Admin puede ver estadísticas")
        
        # Admin puede hacer operaciones masivas
        bulk_response = await client.post(
            "/api/v1/accounts/bulk-operation",
            json={
                "operation": "activate",
                "account_ids": [test_account["id"]]
            },
            headers=auth_headers_admin
        )
        assert bulk_response.status_code == 200
        print("   ✅ Admin puede realizar operaciones masivas")
        
        # =============================================
        # PERMISOS DE CONTADOR
        # =============================================
        
        print("📊 Verificando permisos de CONTADOR...")
        
        # Contador puede crear cuentas
        contador_account_response = await client.post(
            "/api/v1/accounts/",
            json={
                "code": "CONT-001",
                "name": "Cuenta Creada por Contador",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE"
            },
            headers=auth_headers_contador
        )
        assert contador_account_response.status_code == 201
        print("   ✅ Contador puede crear cuentas")
        
        # Contador puede crear asientos
        entry_response = await client.post(
            "/api/v1/journal-entries/",
            json={
                "reference": "CONT-JE-001",
                "description": "Asiento creado por contador",
                "entry_date": date.today().isoformat(),
                "line_items": [
                    {
                        "account_id": test_account["id"],
                        "description": "Débito",
                        "debit_amount": "1000.00",
                        "credit_amount": "0.00"
                    },
                    {
                        "account_id": contador_account_response.json()["id"],
                        "description": "Crédito",
                        "debit_amount": "0.00",
                        "credit_amount": "1000.00"
                    }
                ]
            },
            headers=auth_headers_contador
        )
        assert entry_response.status_code == 201
        print("   ✅ Contador puede crear asientos")
        
        # Contador NO puede crear usuarios
        user_forbidden_response = await client.post(
            "/api/v1/users/admin/create-user",
            json={
                "email": "forbidden@test.com",
                "full_name": "Usuario Prohibido",
                "role": "CONTADOR"
            },
            headers=auth_headers_contador
        )
        assert user_forbidden_response.status_code == 403
        print("   ✅ Contador NO puede crear usuarios")
        
        # Contador NO puede hacer operaciones masivas
        bulk_forbidden_response = await client.post(
            "/api/v1/accounts/bulk-operation",
            json={
                "operation": "deactivate",
                "account_ids": [test_account["id"]]
            },
            headers=auth_headers_contador
        )
        assert bulk_forbidden_response.status_code == 403
        print("   ✅ Contador NO puede realizar operaciones masivas")
        
        # =============================================
        # PERMISOS DE SOLO LECTURA
        # =============================================
        
        print("👀 Verificando permisos de SOLO LECTURA...")
        
        # Solo lectura puede ver cuentas
        readonly_accounts_response = await client.get(
            "/api/v1/accounts/",
            headers=auth_headers_readonly
        )
        assert readonly_accounts_response.status_code == 200
        print("   ✅ Solo lectura puede ver cuentas")
        
        # Solo lectura puede ver reportes
        readonly_reports_response = await client.get(
            "/api/v1/reports/balance-sheet",
            headers=auth_headers_readonly
        )
        assert readonly_reports_response.status_code == 200
        print("   ✅ Solo lectura puede ver reportes")
        
        # Solo lectura NO puede crear cuentas
        readonly_create_forbidden = await client.post(
            "/api/v1/accounts/",
            json={
                "code": "FORBIDDEN",
                "name": "Cuenta Prohibida",
                "account_type": "ACTIVO",
                "category": "ACTIVO_CORRIENTE"
            },
            headers=auth_headers_readonly
        )
        assert readonly_create_forbidden.status_code == 403
        print("   ✅ Solo lectura NO puede crear cuentas")
        
        # Solo lectura NO puede crear asientos
        readonly_entry_forbidden = await client.post(
            "/api/v1/journal-entries/",
            json={
                "reference": "FORBIDDEN",
                "description": "Asiento prohibido",
                "entry_date": date.today().isoformat(),
                "line_items": []
            },
            headers=auth_headers_readonly
        )
        assert readonly_entry_forbidden.status_code == 403
        print("   ✅ Solo lectura NO puede crear asientos")
        
        print("\n🎉 Verificación de permisos completada exitosamente!")

    async def test_error_handling_workflow(
        self,
        client: AsyncClient,
        auth_headers_admin: Dict[str, str]
    ):
        """Test de manejo de errores y casos límite"""
        
        print("\n🚨 Probando manejo de errores...")
        
        # =============================================
        # ERRORES DE VALIDACIÓN
        # =============================================
        
        # Crear cuenta con código duplicado
        account_data = {
            "code": "ERROR-001",
            "name": "Cuenta Original",
            "account_type": "ACTIVO",
            "category": "ACTIVO_CORRIENTE"
        }
        
        # Primera cuenta (debe funcionar)
        first_response = await client.post(
            "/api/v1/accounts/",
            json=account_data,
            headers=auth_headers_admin
        )
        assert first_response.status_code == 201
        
        # Segunda cuenta con mismo código (debe fallar)
        duplicate_response = await client.post(
            "/api/v1/accounts/",
            json=account_data,
            headers=auth_headers_admin
        )
        assert duplicate_response.status_code == 400
        print("   ✅ Error de código duplicado manejado correctamente")
        
        # =============================================
        # ERRORES DE ASIENTOS DESBALANCEADOS
        # =============================================
        
        unbalanced_entry = {
            "reference": "UNBALANCED-001",
            "description": "Asiento desbalanceado",
            "entry_date": date.today().isoformat(),
            "line_items": [
                {
                    "account_id": first_response.json()["id"],
                    "description": "Débito mayor",
                    "debit_amount": "1000.00",
                    "credit_amount": "0.00"
                },
                {
                    "account_id": first_response.json()["id"],
                    "description": "Crédito menor",
                    "debit_amount": "0.00",
                    "credit_amount": "500.00"  # No balancea
                }
            ]
        }
        
        unbalanced_response = await client.post(
            "/api/v1/journal-entries/",
            json=unbalanced_entry,
            headers=auth_headers_admin
        )
        assert unbalanced_response.status_code == 400
        print("   ✅ Error de asiento desbalanceado manejado correctamente")
        
        # =============================================
        # ERRORES DE RECURSOS NO ENCONTRADOS
        # =============================================
        
        # Buscar cuenta inexistente
        nonexistent_account_response = await client.get(
            f"/api/v1/accounts/{uuid.uuid4()}",
            headers=auth_headers_admin
        )
        assert nonexistent_account_response.status_code == 404
        print("   ✅ Error de cuenta inexistente manejado correctamente")
        
        # Buscar asiento inexistente
        nonexistent_entry_response = await client.get(
            f"/api/v1/journal-entries/{uuid.uuid4()}",
            headers=auth_headers_admin
        )
        assert nonexistent_entry_response.status_code == 404
        print("   ✅ Error de asiento inexistente manejado correctamente")
        
        # =============================================
        # ERRORES DE FECHAS INVÁLIDAS
        # =============================================
        
        # Reporte con fechas inválidas
        invalid_date_response = await client.get(
            "/api/v1/reports/income-statement?start_date=2025-12-31&end_date=2025-01-01",
            headers=auth_headers_admin
        )
        assert invalid_date_response.status_code == 400
        print("   ✅ Error de fechas inválidas manejado correctamente")
        print("\n🎉 Manejo de errores verificado exitosamente!")
