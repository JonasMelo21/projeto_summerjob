import os
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    logging.warning("GEMINI_API_KEY não encontrada no arquivo .env")

def analyze_profile(website_content):
    if not API_KEY:
        return "Erro: API Key não configurada", "N/A"
    
    if not website_content or len(website_content) < 50:
        return "Conteúdo insuficiente para análise.", "N/A"

    prompt_avaliacao = f"""
Atue como um Recrutador Técnico Sênior e Especialista em Carreira de Dados (Data Science, ML e Engenharia de Dados).

Sua tarefa é avaliar o "Job Fit" (Compatibilidade) entre o perfil do candidato descrito abaixo e as informações coletadas do site de um professor (Research Interests/Projects).

### PERFIL DO CANDIDATO (CONTEXTO)
1. **Experiência Profissional:**
   - Atual: Estagiário em Machine Learning Engineering.
   - Anterior: Estagiário em Engenharia de Dados (foco em pipelines, ETL).
2. **Formação e Base Teórica:**
   - Forte base matemática: Cálculo, Álgebra Linear, Matemática Aplicada e Cálculo Numérico.
   - Conhecimentos avançados em Pesquisa Operacional (Método Simplex, Teoria das Filas, Otimização).
3. **Estudos Atuais em ML:**
   - Foco nos fundamentos teóricos e matemáticos dos algoritmos.
   - Cursos: Machine Learning Specialization (Andrew Ng).
   - Literatura: "Introduction to Statistical Learning" (ISLP) com aplicação em Python.

### CONTEÚDO DO SITE DO PROFESSOR
{website_content[:8000]} 

### INSTRUÇÕES DE SAÍDA
Analise o conteúdo do site e retorne:

1. **Score de Compatibilidade (0-100%):**
2. **Pontos Fortes (Match):**
3. **Gaps (Lacunas):**
4. **Veredito:**
5. **Classificação Final:** (OBRIGATÓRIO: Escolha APENAS UMA das opções: "Fit Muito Alto", "Fit Alto", "Fit Baixo", "Fit Muito Baixo")

Responda de forma direta.
"""

    # Tenta usar um modelo mais recente (Flash é mais rápido e economico, 1.5 Pro é mais robusto)
    # Atualizado com modelos disponíveis no log do usuário (2.0/2.5 e Latest)
    model_candidates = [
        # Modelos Lite/Flash (Geralmente mais rápidos e com cotas melhores)
        'gemini-2.5-flash-lite',
        'gemini-2.0-flash-lite-preview-02-05',
        'gemini-flash-lite-latest',
        'gemini-3-flash-preview',
        'gemini-2.5-flash',
        
        # Modelos Standard/Pro
        'gemini-2.0-flash', 
        'gemini-flash-latest',
        'gemini-1.5-flash',
        
        # Modelos Alternativos (Gemma/Outros Previews)
        'gemma-3-27b-it',
        'gemini-3-pro-preview',
    ]
    
    response = None
    last_error = None

    for model_name in model_candidates:
        try:
            model = genai.GenerativeModel(model_name)
            
            # Executa diretamente sem retries (pedida do usuário para falhar rápido em caso de cota)
            response = model.generate_content(prompt_avaliacao)
            break # Sucesso, sai do loop de modelos
            
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            
            # Se for erro de cota (429), propaga o erro imediatamente para parar o script
            if "429" in err_str or "quota" in err_str or "resource exhausted" in err_str:
                logging.error(f"❌ Cota excedida no modelo {model_name}. Interrompendo script imediatamente.")
                raise e
            
            # Outros erros (ex: modelo não encontrado, erro interno), tenta o próximo modelo
            logging.warning(f"Falha ao usar modelo {model_name}: {str(e)}")
            continue

    if not response:
        # Se falhar com todos, tenta listar os disponíveis para debug
        try:
            logging.error("Todos os modelos falharam. Listando modelos disponíveis...")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    logging.info(f"Modelo disponível: {m.name}")
        except Exception as e_list:
            logging.error(f"Não foi possível listar modelos: {e_list}")
            
        return f"Erro na análise (Todos modelos falharam): {last_error}", "Erro"

    try:
        text_response = response.text
        
        # Extrair a classificação final de forma simples
        fit_category = "Fit Baixo" # Valor default conservador se a IA falhar na formatação
        lower_resp = text_response.lower()
        
        # Ordem importa: verificar "muito" antes do simples
        if "fit muito alto" in lower_resp:
            fit_category = "Fit Muito Alto"
        elif "fit alto" in lower_resp:
            fit_category = "Fit Alto"
        elif "fit muito baixo" in lower_resp:
            fit_category = "Fit Muito Baixo"
        elif "fit baixo" in lower_resp:
            fit_category = "Fit Baixo"
            
        return text_response, fit_category

    except Exception as e:
        logging.error(f"Erro na API do Gemini: {e}")
        return f"Erro na análise: {e}", "Erro"
