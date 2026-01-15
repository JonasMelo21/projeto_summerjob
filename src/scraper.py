import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse

def get_text_from_url(url):
    """Auxiliar: Baixa e limpa o texto de uma URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts e estilos
        for script in soup(["script", "style", "nav", "footer", "iframe"]):
            script.decompose()
            
        text = soup.get_text(separator=' ')
        
        # Limpa espaços
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return soup, clean_text
    except Exception as e:
        logging.warning(f"Erro ao acessar {url}: {e}")
        return None, ""

def scrape_website(url):
    """
    Scraper Inteligente V2:
    1. Baixa a página principal.
    2. Se tiver pouco texto, procura links de 'Research', 'Projects', 'Publications', 'Lab'.
    3. Baixa essas sub-páginas e junta o conteúdo.
    """
    if not isinstance(url, str) or not url.strip():
        return None

    logging.info(f"🔍 Scraping: {url}")
    
    # 1. Página Principal
    soup_main, text_main = get_text_from_url(url)
    
    if not soup_main:
        return None

    final_text = f"--- CONTEÚDO DA HOME PAGE ({url}) ---\n{text_main}\n"
    
    # Se já tem bastante texto, retorna logo (economizando tempo)
    if len(text_main) > 5000:
        return final_text[:15000]

    # 2. Busca Links Complementares (Heurística)
    # Palavras-chave que indicam conteúdo relevante
    keywords = ['research', 'publication', 'project', 'lab', 'group', 'pesquisa', 'projeto']
    
    # Filtros de exclusão (Redes Sociais, Arquivos, etc)
    ignore_domains = ['linkedin.com', 'twitter.com', 'x.com', 'facebook.com', 'instagram.com', 'youtube.com', 'google.com', 'researchgate.net']
    ignore_exts = ['.pdf', '.doc', '.docx', '.zip', '.png', '.jpg']
    ignore_terms_text = ['home', 'contact', 'email', 'login', 'sign in', 'back']
    
    visited_links = set()
    extra_content = []
    
    # Detecção de "Página Cartão de Visita" (Muito curta, exige navegação agressiva)
    is_short_page = len(text_main) < 1000
    
    # Encontra todos os links
    links = soup_main.find_all('a', href=True)
    
    found_relevant_links = 0
    max_links = 3 if is_short_page else 2
    
    for link in links:
        if found_relevant_links >= max_links: 
            break
            
        href = link['href']
        text_link = link.get_text().strip().lower()
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        
        # --- FILTROS DE SEGURANÇA ---
        if full_url == url or href.startswith('#') or not text_link: continue
        if any(parsed.netloc.endswith(d) for d in ignore_domains): continue
        if any(parsed.path.lower().endswith(ext) for ext in ignore_exts): continue
        
        should_follow = False
        
        # Regra 1: Tem palavra-chave no texto ou link?
        if any(w in text_link for w in keywords) or any(w in href.lower() for w in keywords):
            should_follow = True
            
        # Regra 2: Se a página é curta, segue links que não sejam "Home/Contact" (Link do Lab muitas vezes é o nome do lab)
        elif is_short_page:
            if len(text_link) > 2 and not any(t in text_link for t in ignore_terms_text):
                 # Evita sair do domínio se não tiver certeza ABSOLUTA, exceto se for página de perfil acadêmico que linka lab externo
                 should_follow = True

        if should_follow:
            # Restrição de Domínio: Relaxada para permitir Labs em domínios próprios
            # Mas evitamos navegar na web inteira. Aceitamos se for subdomínio ou se for 'clicado' por keyword.
            
            if full_url in visited_links: continue
                
            logging.info(f"   ↳ Aprofundando em: {full_url}")
            _, sub_text = get_text_from_url(full_url)
            
            # Só adiciona se trouxer conteúdo novo relevante
            if sub_text and len(sub_text) > 200:
                extra_content.append(f"\n--- CONTEÚDO EXTRA ({text_link.upper()}) ---\nLink: {full_url}\n{sub_text}")
                visited_links.add(full_url)
                found_relevant_links += 1

    # Junta tudo
    if extra_content:
        final_text += "\n".join(extra_content)
    
    return final_text[:25000] # Limite aumentado para gemma/gemini
