import os
import imapclient
import pyzmail36
import re
import psycopg2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from time import sleep
import shutil

# Carrega variáveis do .env
load_dotenv()

EMAIL = os.getenv("EMAIL")
SENHA = os.getenv("EMAIL_SENHA")
IMAP_SERVER = os.getenv("IMAP_SERVER")

DB_URL = os.getenv("DATABASE_URL")  # URL completa do PostgreSQL

ASSUNTO = "relatorio_manhaes_diario"
XPATH_BOTAO_BAIXAR = "/html/body/div[1]/div/div/div/div[1]/button"

# Função para conectar ao banco
def conectar_db():
    return psycopg2.connect(DB_URL)

# Função para baixar o CSV com Selenium
def baixar_csv(link):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.binary_location = "/usr/bin/microsoft-edge"

    prefs = {
        "download.default_directory": "/app/downloads",
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Edge(options=options)
    try:
        print("🌐 Acessando página do relatório...")
        driver.get(link)
        sleep(5)

        print("⬇️ Clicando no botão de download...")
        botao = driver.find_element(By.XPATH, "//*[contains(text(), 'Baixar')]")
        botao.click()
        sleep(10)

        arquivos = os.listdir("/app/downloads")
        csvs = [f for f in arquivos if f.endswith(".csv")]
        if not csvs:
            print("❌ Nenhum arquivo CSV encontrado.")
            return None

        mais_recente = max([os.path.join("/app/downloads", f) for f in csvs], key=os.path.getctime)
        final_path = f"/app/relatorio_yeastar_{datetime.today().date()}.csv"
        shutil.move(mais_recente, final_path)
        return final_path
    except Exception as e:
        print("❌ Erro no Selenium:", e)
        return None
    finally:
        driver.quit()

# Função para importar CSV no banco
def importar_para_db(path_csv):
    df = pd.read_csv(path_csv)
    df.fillna("00:00:00", inplace=True)
    data_relatorio = datetime.today().date()

    conn = conectar_db()
    cur = conn.cursor()

    for _, row in df.iterrows():
        extensao = row['Extensão']
        atendidas = int(row['Atendidas'])
        nao_atendidas = int(row['Não Atendidas'])
        ocupado = int(row['Ocupado'])
        falhada = int(row['Falhada'])
        mensagem_voz = int(row['Mensagem de Voz'])
        tempo_tocando = row['Total de Tempo Tocando']
        tempo_conversa = row['Duração Total Conversação']

        cur.execute("""
            INSERT INTO cobranca_chamadayeastar
            (data_relatorio, extensao, atendidas, nao_atendidas, ocupado, falhada, mensagem_voz, tempo_tocando, tempo_conversa)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (data_relatorio, extensao)
            DO UPDATE SET
                atendidas = EXCLUDED.atendidas,
                nao_atendidas = EXCLUDED.nao_atendidas,
                ocupado = EXCLUDED.ocupado,
                falhada = EXCLUDED.falhada,
                mensagem_voz = EXCLUDED.mensagem_voz,
                tempo_tocando = EXCLUDED.tempo_tocando,
                tempo_conversa = EXCLUDED.tempo_conversa;
        """, (
            data_relatorio, extensao, atendidas, nao_atendidas, ocupado, falhada,
            mensagem_voz, tempo_tocando, tempo_conversa
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Dados importados com sucesso.")

# Função principal
def executar_processo():
    print("📧 Conectando ao e-mail...")
    with imapclient.IMAPClient(IMAP_SERVER, ssl=True) as client:
        client.login(EMAIL, SENHA)
        client.select_folder("INBOX")
        mensagens = client.search(['SUBJECT', ASSUNTO])

        if not mensagens:
            print("❌ Nenhum e-mail encontrado.")
            return

        uid = mensagens[-1]
        mensagem = client.fetch([uid], ['BODY[]', 'FLAGS'])
        email_msg = pyzmail36.PyzMessage.factory(mensagem[uid][b'BODY[]'])

        if not email_msg.text_part:
            print("❌ E-mail sem corpo de texto.")
            return

        corpo = email_msg.text_part.get_payload().decode(email_msg.text_part.charset)
        match = re.search(r"https://[^\s]+", corpo)
        if not match:
            print("❌ Link não encontrado no corpo do e-mail.")
            return

        link = match.group(0)
        print("🔗 Link encontrado:", link)

        caminho_csv = baixar_csv(link)
        if caminho_csv:
            importar_para_db(caminho_csv)

if __name__ == "__main__":
    executar_processo()
