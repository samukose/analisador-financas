import sqlite3
from datetime import datetime

def iniciar_banco():
    conn = sqlite3.connect('financas.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    #tabela categorias
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        tipo TEXT CHECK(tipo IN ('Receita', 'Despesa')) NOT NULL
    );
    """)

    #tabela transacoes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data DATE NOT NULL,
        categoria_id INTEGER,
        FOREIGN KEY (categoria_id) REFERENCES categorias (id)
    );
    """)

    #categorias padrão
    cursor.execute("SELECT COUNT(*) FROM categorias;")
    if cursor.fetchone()[0] == 0:
        categorias_padrao = [
            ("Salário", "Receita"),
            ("Freelance", "Receita"),
            ("Alimentação", "Despesa"),
            ("Transporte", "Despesa"),
            ("Lazer", "Despesa"),
            ("Saúde", "Despesa")
        ]
        cursor.executemany("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", categorias_padrao)

    conn.commit()
    return conn

def adicionar_categoria(conn):
    nome = input("Digite o nome da categoria: ")
    tipo = input("Digite o tipo da categoria (Receita/Despesa): ")

    if tipo not in ['Receita', 'Despesa']:
        print("Tipo inválido. A categoria não foi adicionada.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categorias (nome, tipo) VALUES (?, ?)", (nome, tipo))
        conn.commit()
        print(f"Categoria '{nome}' adicionada com sucesso!")
    except sqlite3.IntegrityError:
        print(f"A categoria '{nome}' já existe.")

def listar_categorias(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, tipo FROM categorias")
    rows = cursor.fetchall()
    print("\n--- Categorias Disponíveis ---")
    print(f"{'ID':<5} | {'Nome':<20} | {'Tipo':<10}")
    print("-" * 40)
    for row in rows:
        print(f"{row[0]:<5} | {row[1]:<20} | {row[2]:<10}")
    return [row[0] for row in rows] 

def registrar_transacao(conn):
    print("\n--- Nova Transação ---")
    ids_validos = listar_categorias(conn)
    
    try:
        cat_id = int(input("\nDigite o ID da categoria desejada: "))
        if cat_id not in ids_validos:
            print("Erro: ID de categoria não existe.")
            return
            
        descricao = input("Descrição da transação: ").strip() 
        valor = float(input("Valor (Ex: 150.50 para positivo, -50.00 para despesa): "))
        
        
        cursor = conn.cursor()
        cursor.execute("SELECT tipo FROM categorias WHERE id = ?", (cat_id,))
        tipo_cat = cursor.fetchone()[0]
        
        if tipo_cat == 'Despesa' and valor > 0:
            valor = -valor  
        elif tipo_cat == 'Receita' and valor < 0:
            valor = abs(valor) 

        data_atual = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO transacoes (descricao, valor, data, categoria_id)
            VALUES (?, ?, ?, ?)
        """, (descricao, valor, data_atual, cat_id))
        
        conn.commit()
        print(f"Sucesso: Transação '{descricao}' registrada com o valor de R$ {valor:.2f}!")
        
    except ValueError:
        print("Erro: Entrada inválida. Certifique-se de digitar números nos campos de ID e Valor.")

def mostrar_extrato(conn):
    cursor = conn.cursor()
    query="""
        SELECT t.id, t.descricao, t.valor, t.data, c.nome
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        ORDER BY t.data DESC
        """
    cursor.execute(query)
    rows = cursor.fetchall()

    print("\n--- Extrato Financeiro ---")
    print(f"{'ID':<5} | {'Descrição':<30} | {'data':<12} | {'Valor':<10} | {'Categoria':<20}")
    print("-" * 90)
    for row in rows:
        print(f"{row[0]:<5} | {row[1]:<30} | {row[3]:<12} | R$ {row[2]:<10.2f} | {row[4]:<20}")

def resumo_financeiro(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE valor > 0")
    total_receitas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE valor < 0")
    total_despesas = cursor.fetchone()[0] or 0

    saldo = total_receitas + total_despesas

    if month := input("Deseja filtrar por mês? (s/n): ").strip().lower() == 's':
        mes = input("Digite o mês (MM): ")
        ano = input("Digite o ano (YYYY): ")
        cursor.execute("""
            SELECT SUM(valor) FROM transacoes 
            WHERE valor > 0 AND strftime('%m', data) = ? AND strftime('%Y', data) = ?
        """, (mes, ano))
        total_receitas = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT SUM(valor) FROM transacoes 
            WHERE valor < 0 AND strftime('%m', data) = ? AND strftime('%Y', data) = ?
        """, (mes, ano))
        total_despesas = cursor.fetchone()[0] or 0

    print("\n--- Resumo Financeiro ---")
    print(f"Total de Receitas: R$ {total_receitas:.2f}")
    print(f"Total de Despesas: R$ {abs(total_despesas):.2f}")
    print(f"Saldo Atual: R$ {saldo:.2f}")

    print("\n--- Resumo por Categoria ---")
    query_gastos="""
        SELECT c.nome, SUM(t.valor) as total
        FROM transacoes t
        JOIN categorias c ON t.categoria_id = c.id
        GROUP BY c.nome
    """
    cursor.execute(query_gastos)
    rows = cursor.fetchall()
    if not rows:
        print("Nenhuma transação registrada.")
    for g in rows:
        print(f"Categoria: {g[0]:<20} | Total: R$ {g[1]:<10.2f}")

def apagar_transacao(conn):
    cursor = conn.cursor()
    mostrar_extrato(conn)
    option = input("\nDeseja apagar todas as transações? (s/n): ").strip().lower()
    if option == 's':
        cursor.execute("DELETE FROM transacoes")
        conn.commit()
        print("Sucesso: Todas as transações foram apagadas.")
        return
    
    try:
        transacao_id = int(input("\nDigite o ID da transação que deseja apagar: "))
        cursor.execute("SELECT * FROM transacoes WHERE id = ?", (transacao_id,))
        if cursor.fetchone() is None:
            print("Erro: ID de transação não encontrado.")
            return
        cursor.execute("DELETE FROM transacoes WHERE id = ?", (transacao_id,))
        conn.commit()
        print("Sucesso: Transação apagada.")
    except ValueError:
        print("Erro: Entrada inválida. Certifique-se de digitar um número válido para o ID.")

def menu ():
    conn = iniciar_banco()
    while True:
        print("\n--- Menu Principal ---")
        print("1. Adicionar Categoria")
        print("2. Registrar Transação")
        print("3. Mostrar Extrato")
        print("4. Resumo Financeiro")
        print("5. Apagar Transação")
        print("6. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            adicionar_categoria(conn)
        elif escolha == '2':
            registrar_transacao(conn)
        elif escolha == '3':
            mostrar_extrato(conn)
        elif escolha == '4':
            resumo_financeiro(conn)
        elif escolha == '5':
            apagar_transacao(conn)
        elif escolha == '6':
            print("Saindo do programa...")
            break
        else:
            print("Opção inválida. Tente novamente.")

    conn.close()

if __name__ == "__main__":
    menu()