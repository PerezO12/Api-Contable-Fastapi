#!/usr/bin/env python3
"""
Script de prueba para el ZIP real de NFe
Testa o processamento do arquivo ZIP real com múltiplos XMLs
"""

import httpx
import json
from pathlib import Path

# Configuração do teste
BASE_URL = "http://localhost:8000"
REAL_ZIP_PATH = Path("../NFesEmitidas-2025-05-13-10_46_06.zip")

# Credenciais de teste
TEST_CREDENTIALS = {
    "email": "admin@contable.com",
    "password": "Admin123!"
}

# Configuração para teste do ZIP real (permite duplicados)
NFE_IMPORT_CONFIG = {
    "batch_size": 20,  # Lotes menores para teste
    "skip_duplicates": False,  # Permitir duplicados para teste
    "auto_create_third_parties": True,
    "auto_create_products": True,
    "create_invoices": True,
    "create_journal_entries": False,
    "default_revenue_account": "410001",
    "default_customer_account": "130001",
    "default_supplier_account": "210001",
    "default_sales_journal": "VEN",
    "default_purchase_journal": "COM",
    "currency_code": "BRL",
    "time_zone": "America/Sao_Paulo"
}


def test_real_zip():
    """Testar o ZIP real de NFe"""
    print("🚀 Testando ZIP real de NFe\n")
    
    # Verificar se o ZIP existe
    if not REAL_ZIP_PATH.exists():
        print(f"❌ ZIP não encontrado: {REAL_ZIP_PATH}")
        return
    
    print(f"📦 ZIP encontrado: {REAL_ZIP_PATH.name}")
    print(f"📏 Tamanho: {REAL_ZIP_PATH.stat().st_size / (1024*1024):.1f} MB")
    
    # Fazer login
    client = httpx.Client(base_url=BASE_URL, timeout=600.0)  # 10 minutos timeout
    
    try:
        response = client.post("/api/v1/auth/login", json=TEST_CREDENTIALS)
        if response.status_code != 200:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return
        
        token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        print("✅ Login realizado com sucesso")
        
        # Fazer importação do ZIP
        print(f"\n🧪 Testando importação do ZIP real...")
        
        with open(REAL_ZIP_PATH, 'rb') as f:
            files = [('files', (REAL_ZIP_PATH.name, f.read(), 'application/zip'))]
        
        data = {"config": json.dumps(NFE_IMPORT_CONFIG)}
        
        print("⏳ Enviando ZIP para processamento (isso pode demorar alguns minutos)...")
        response = client.post("/api/v1/nfe/bulk-import", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Importação de ZIP concluída com sucesso!")
            
            summary = result.get('summary', {})
            entities = result.get('created_entities', {})
            errors = result.get('errors', [])
            warnings = result.get('warnings', [])
            
            print(f"\n📊 RESUMO DA IMPORTAÇÃO:")
            print(f"   Total de arquivos: {summary.get('total_files', 0)}")
            print(f"   Processados com sucesso: {summary.get('processed_successfully', 0)}")
            print(f"   Processados com erros: {summary.get('processed_with_errors', 0)}")
            print(f"   Ignorados: {summary.get('ignored', 0)}")
            print(f"   Taxa de sucesso: {summary.get('success_rate', 0)}%")
            print(f"   Tempo de processamento: {summary.get('processing_time', 0)}s")
            
            print(f"\n🏗️  ENTIDADES CRIADAS:")
            print(f"   Faturas: {entities.get('invoices', 0)}")
            print(f"   Terceiros: {entities.get('third_parties', 0)}")
            print(f"   Produtos: {entities.get('products', 0)}")
            
            if errors:
                print(f"\n❌ ERROS ({len(errors)}):")
                for error in errors[:5]:  # Mostrar apenas os primeiros 5
                    print(f"   - {error.get('file', 'N/A')}: {error.get('message', 'N/A')[:100]}...")
                if len(errors) > 5:
                    print(f"   ... e mais {len(errors) - 5} erros")
                    
            if warnings:
                print(f"\n⚠️  AVISOS ({len(warnings)}):")
                for warning in warnings[:3]:  # Mostrar apenas os primeiros 3
                    print(f"   - {warning.get('file', 'N/A')}: {warning.get('message', 'N/A')[:100]}...")
                if len(warnings) > 3:
                    print(f"   ... e mais {len(warnings) - 3} avisos")
            
        else:
            print(f"❌ Erro na importação: {response.status_code}")
            print(f"Resposta: {response.text}")
        
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
    
    finally:
        client.close()
        
    print("\n✅ Teste concluído!")


if __name__ == "__main__":
    test_real_zip()
