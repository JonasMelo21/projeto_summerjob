import requests
from bs4 import BeautifulSoup
import logging

def scrape_website(url):
    """
    Faz o download do conteúdo da página e retorna o texto visível.
    Tenta contornar alguns bloqueios simples com User-Agent.
    """
    if not isinstance(url, str) or not url.strip():
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts e estilos
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        # Obtém o texto
        text = soup.get_text(separator=' ')
        
        # Limpa espaços em branco extras
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Truncar se for muito grande (apenas segurança básica, o LLM tem limite)
        return text[:10000] 

    except Exception as e:
        logging.error(f"Erro ao acessar {url}: {e}")
        return None
