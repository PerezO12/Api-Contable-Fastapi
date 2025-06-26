#!/usr/bin/env python3
"""
Script de prueba para el endpoint de importación em lote de NFe
Usa arquivos reais do ZIP para testar o sistema completo
"""

import httpx
import zipfile
import json
from pathlib import Path
import asyncio
from typing import List, Dict, Any

# Configuração do teste
BASE_URL = "http://localhost:8000"
NFE_ZIP_PATH = Path("../NFesEmitidas-2025-05-13-10_46_06")

# Credenciais de teste (adaptar conforme o usuário existente)
TEST_CREDENTIALS = {
    "email": "admin@contable.com",    # Adaptar conforme usuário existente
    "password": "Admin123!"           # Adaptar conforme senha
}

# Configuração para importação de NFe
NFE_IMPORT_CONFIG = {
    "batch_size": 10,
    "skip_duplicates": True,
    "auto_create_third_parties": True,
    "auto_create_products": True,
    "create_invoices": True,
    "create_journal_entries": False,  # Desabilitado por enquanto
    "default_revenue_account": "410001",  # Conta de receita - adaptar conforme plano de contas
    "default_customer_account": "130001", # Conta de clientes - adaptar conforme plano de contas
    "default_supplier_account": "210001", # Conta de fornecedores - adaptar conforme plano de contas
    "default_sales_journal": "VEN",       # Diário de vendas - adaptar conforme existente
    "default_purchase_journal": "COM",    # Diário de compras - adaptar conforme existente
    "currency_code": "BRL",
    "time_zone": "America/Sao_Paulo"
}


class NFeTester:
    def __init__(self):
        self.client = httpx.Client(base_url=BASE_URL, timeout=300.0)  # 5 minutos timeout
        self.token = None
    
    def login(self) -> bool:
        """Fazer login e obter token"""
        try:
            response = self.client.post("/api/v1/auth/login", json=TEST_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.client.headers.update({"Authorization": f"Bearer {self.token}"})
                print("✅ Login realizado com sucesso")
                return True
            else:
                print(f"❌ Erro no login: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na conexão: {str(e)}")
            return False
    
    def get_sample_xml_files(self, max_files: int = 5) -> List[Path]:
        """Obter arquivos XML de amostra"""
        xml_files = []
        
        if NFE_ZIP_PATH.exists():
            xml_files = list(NFE_ZIP_PATH.glob("*.xml"))[:max_files]
            print(f"📁 Encontrados {len(xml_files)} arquivos XML para teste")
        else:
            print(f"❌ Pasta não encontrada: {NFE_ZIP_PATH}")
        
        return xml_files
    
    def create_test_zip(self, xml_files: List[Path], zip_name: str = "test_nfes.zip") -> Path:
        """Criar ZIP de teste com alguns XMLs"""
        zip_path = Path(zip_name)
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for xml_file in xml_files:
                zip_file.write(xml_file, xml_file.name)
        
        print(f"📦 Criado ZIP de teste: {zip_path} com {len(xml_files)} arquivos")
        return zip_path
    
    def test_bulk_import_xml_files(self, xml_files: List[Path]) -> Dict[str, Any]:
        """Testar importação com arquivos XML individuais"""
        print(f"\n🧪 Testando importação de {len(xml_files)} arquivos XML individuais...")
        
        files = []
        for xml_file in xml_files:
            with open(xml_file, 'rb') as f:
                files.append(('files', (xml_file.name, f.read(), 'text/xml')))
        
        # Preparar dados da requisição
        data = {"config": json.dumps(NFE_IMPORT_CONFIG)}
        
        try:
            response = self.client.post("/api/v1/nfe/bulk-import", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Importação concluída com sucesso!")
                self.print_import_result(result)
                return result
            else:
                print(f"❌ Erro na importação: {response.status_code}")
                print(f"Resposta: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Erro na requisição: {str(e)}")
            return {"error": str(e)}
    
    def test_bulk_import_zip(self, zip_path: Path) -> Dict[str, Any]:
        """Testar importação com arquivo ZIP"""
        print(f"\n🧪 Testando importação de arquivo ZIP: {zip_path.name}...")
        
        with open(zip_path, 'rb') as f:
            files = [('files', (zip_path.name, f.read(), 'application/zip'))]
        
        # Preparar dados da requisição
        data = {"config": json.dumps(NFE_IMPORT_CONFIG)}
        
        try:
            response = self.client.post("/api/v1/nfe/bulk-import", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Importação de ZIP concluída com sucesso!")
                self.print_import_result(result)
                return result
            else:
                print(f"❌ Erro na importação: {response.status_code}")
                print(f"Resposta: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Erro na requisição: {str(e)}")
            return {"error": str(e)}
    
    def print_import_result(self, result: Dict[str, Any]):
        """Imprimir resultado da importação"""
        summary = result.get("summary", {})
        created = result.get("created_entities", {})
        errors = result.get("errors", [])
        warnings = result.get("warnings", [])
        
        print(f"""
📊 RESUMO DA IMPORTAÇÃO:
   Total de arquivos: {summary.get('total_files', 0)}
   Processados com sucesso: {summary.get('processed_successfully', 0)}
   Processados com erros: {summary.get('processed_with_errors', 0)}
   Ignorados: {summary.get('skipped', 0)}
   Taxa de sucesso: {summary.get('success_rate', 0):.1f}%
   Tempo de processamento: {summary.get('processing_time_seconds', 0):.2f}s

🏗️  ENTIDADES CRIADAS:
   Faturas: {created.get('invoices', 0)}
   Terceiros: {created.get('third_parties', 0)}
   Produtos: {created.get('products', 0)}
        """)
        
        if errors:
            print(f"\n❌ ERROS ({len(errors)}):")
            for error in errors[:5]:  # Mostrar apenas os primeiros 5
                print(f"   - {error.get('file_name', 'N/A')}: {error.get('error_message', 'N/A')}")
            if len(errors) > 5:
                print(f"   ... e mais {len(errors) - 5} erros")
        
        if warnings:
            print(f"\n⚠️  AVISOS ({len(warnings)}):")
            for warning in warnings[:5]:  # Mostrar apenas os primeiros 5
                print(f"   - {warning.get('file_name', 'N/A')}: {warning.get('warning_message', 'N/A')}")
            if len(warnings) > 5:
                print(f"   ... e mais {len(warnings) - 5} avisos")
    
    def test_list_nfes(self) -> Dict[str, Any]:
        """Testar listagem de NFe"""
        print("\n🧪 Testando listagem de NFe...")
        
        try:
            response = self.client.get("/api/v1/nfe/", params={"page": 1, "page_size": 10})
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Listagem realizada! Total: {result.get('total', 0)} NFe encontradas")
                
                for nfe in result.get('items', [])[:3]:  # Mostrar apenas as primeiras 3
                    print(f"   - NFe {nfe.get('numero_nfe')}: {nfe.get('nome_emitente')} -> {nfe.get('nome_destinatario')} | Status: {nfe.get('status')} | Valor: R$ {nfe.get('valor_total_nfe', 0)}")
                
                return result
            else:
                print(f"❌ Erro na listagem: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Erro na requisição: {str(e)}")
            return {"error": str(e)}
    
    def run_tests(self):
        """Executar todos os testes"""
        print("🚀 Iniciando testes do sistema de importação NFe\n")
        
        # 1. Login
        if not self.login():
            return
        
        # 2. Obter arquivos de amostra
        xml_files = self.get_sample_xml_files(max_files=3)
        if not xml_files:
            print("❌ Nenhum arquivo XML encontrado para teste")
            return
        
        # 3. Teste com arquivos XML individuais
        xml_result = self.test_bulk_import_xml_files(xml_files)
        
        # 4. Teste com ZIP
        zip_path = self.create_test_zip(xml_files[:2])  # Apenas 2 arquivos no ZIP
        zip_result = self.test_bulk_import_zip(zip_path)
        
        # 5. Listar NFe criadas
        list_result = self.test_list_nfes()
        
        # 6. Limpeza
        if zip_path.exists():
            zip_path.unlink()
            print(f"🧹 Arquivo temporário removido: {zip_path}")
        
        print("\n✅ Testes concluídos!")
        
        # Resumo final
        total_processed = 0
        if 'summary' in xml_result:
            total_processed += xml_result['summary'].get('processed_successfully', 0)
        if 'summary' in zip_result:
            total_processed += zip_result['summary'].get('processed_successfully', 0)
        
        print(f"📈 Total de NFe processadas com sucesso: {total_processed}")


def main():
    """Função principal"""
    tester = NFeTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
