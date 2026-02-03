"""
Script para inicializar o banco de dados e criar migrations.
Executa: flask db init && flask db migrate && flask db upgrade
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app_simple import app, db
from flask_migrate import init, migrate, upgrade
import flask_migrate

def initialize_database():
    """Inicializa o banco de dados com Flask-Migrate"""
    
    with app.app_context():
        print("🔧 Inicializando Flask-Migrate...")
        
        # Verifica se já existe o diretório de migrations
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        
        if not os.path.exists(migrations_dir):
            print("📁 Criando estrutura de migrations...")
            flask_migrate.init()
            print("✅ Migrations inicializadas")
        else:
            print("ℹ️  Diretório migrations já existe")
        
        print("\n🔄 Criando migration inicial...")
        flask_migrate.migrate(message="Initial schema with User and AccessLog tables")
        print("✅ Migration criada")
        
        print("\n⬆️  Aplicando migrations ao banco...")
        flask_migrate.upgrade()
        print("✅ Migrations aplicadas com sucesso")
        
        print("\n✅ Banco de dados inicializado com sucesso!")
        print("📊 Tabelas criadas: users, access_logs")

if __name__ == '__main__':
    try:
        initialize_database()
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
