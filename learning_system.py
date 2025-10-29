import sqlite3
import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import re

class IntelligentLearningSystem:
    def __init__(self, db_path=None):
        # Configuração de banco de dados para produção
        if db_path is None:
            if os.environ.get('RENDER'):
                # Ambiente de produção no Render - usa volume persistente
                db_path = "/app/data/learning_data.db"
            else:
                # Desenvolvimento local
                db_path = "learning_data.db"

        self.db_path = db_path

        # Garantir que o diretório existe
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados para armazenar dados de aprendizado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela para histórico de classificações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_classification TEXT NOT NULL,
                corrected_classification TEXT,
                confidence_score REAL,
                text_content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                feedback_provided BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Tabela para padrões aprendidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                category TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                usage_count INTEGER DEFAULT 1,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela para estatísticas de performance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                total_classifications INTEGER DEFAULT 0,
                correct_classifications INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabela para feedback dos usuários (like/dislike)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                category TEXT NOT NULL,
                is_positive BOOLEAN NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_classification(self, filename, classification, confidence_score=None, text_content=None):
        """Registra uma classificação no histórico"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO classification_history 
            (filename, original_classification, confidence_score, text_content)
            VALUES (?, ?, ?, ?)
        ''', (filename, classification, confidence_score, text_content))
        
        conn.commit()
        conn.close()
        
        # Atualiza estatísticas
        self.update_category_stats(classification)
    
    def record_feedback(self, filename, correct_classification):
        """Registra feedback de correção do usuário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Atualiza o registro mais recente para este arquivo
        cursor.execute('''
            UPDATE classification_history 
            SET corrected_classification = ?, feedback_provided = TRUE
            WHERE filename = ? AND id = (
                SELECT MAX(id) FROM classification_history WHERE filename = ?
            )
        ''', (correct_classification, filename, filename))
        
        # Busca informações do registro para aprender padrões
        cursor.execute('''
            SELECT original_classification, text_content FROM classification_history
            WHERE filename = ? AND corrected_classification = ?
            ORDER BY id DESC LIMIT 1
        ''', (filename, correct_classification))
        
        result = cursor.fetchone()
        if result:
            original_class, text_content = result
            self.learn_from_correction(filename, text_content, original_class, correct_classification)
        
        conn.commit()
        conn.close()
        
        # Atualiza estatísticas de performance
        self.update_performance_stats(correct_classification, was_correct=False)
    
    def learn_from_correction(self, filename, text_content, wrong_class, correct_class):
        """Aprende novos padrões baseado nas correções"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extrai padrões do nome do arquivo
        filename_patterns = self.extract_filename_patterns(filename)
        for pattern in filename_patterns:
            self.add_or_update_pattern('filename', pattern, correct_class, cursor)
        
        # Extrai padrões do conteúdo de texto
        if text_content:
            text_patterns = self.extract_text_patterns(text_content, correct_class)
            for pattern in text_patterns:
                self.add_or_update_pattern('text', pattern, correct_class, cursor)
        
        conn.commit()
        conn.close()
    
    def extract_filename_patterns(self, filename):
        """Extrai padrões úteis do nome do arquivo"""
        patterns = []
        filename_lower = filename.lower()
        
        # Palavras-chave importantes
        words = re.findall(r'\b\w+\b', filename_lower)
        for word in words:
            if len(word) > 2:  # Ignora palavras muito curtas
                patterns.append(word)
        
        # Padrões de números (CPF, RG, etc.)
        number_patterns = re.findall(r'\d+', filename)
        for pattern in number_patterns:
            if len(pattern) >= 3:  # Números significativos
                patterns.append(f"num_{len(pattern)}_digits")
        
        return patterns
    
    def extract_text_patterns(self, text_content, category):
        """Extrai padrões úteis do conteúdo de texto com melhor detecção"""
        patterns = []
        text_lower = text_content.lower()
        
        # Palavras-chave específicas por categoria expandidas
        category_keywords = {
            'rg': ['registro geral', 'carteira de identidade', 'rg nº', 'identidade', 'documento de identidade'],
            'cpf': ['cadastro de pessoa física', 'cpf', 'receita federal', 'contribuinte'],
            'cnh': ['carteira nacional', 'habilitação', 'detran', 'condutor', 'permissão para dirigir'],
            'certidao_nascimento': ['certidão de nascimento', 'nascimento', 'cartório', 'registro civil'],
            'certidao_casamento': ['certidão de casamento', 'casamento', 'matrimônio', 'união'],
            'certidao_obito': ['certidão de óbito', 'óbito', 'falecimento', 'morte'],
            'contracheque': ['contracheque', 'holerite', 'salário', 'remuneração', 'folha de pagamento'],
            'conta_luz': ['conta de luz', 'energia elétrica', 'kwh', 'cemig', 'cpfl', 'eletropaulo'],
            'conta_agua': ['conta de água', 'saneamento', 'sabesp', 'copasa', 'águas'],
            'conta_gas': ['conta de gás', 'gás natural', 'comgás'],
            'extrato_bancario': ['extrato', 'banco', 'saldo', 'movimentação', 'conta corrente'],
            'comprovante_residencia': ['comprovante de residência', 'endereço', 'residência'],
            'comprovante_renda': ['comprovante de renda', 'declaração de renda', 'rendimentos'],
            'diploma': ['diploma', 'graduação', 'conclusão de curso', 'formatura'],
            'historico_escolar': ['histórico escolar', 'boletim', 'notas', 'disciplinas'],
            'atestado_medico': ['atestado médico', 'atestado', 'médico', 'cid'],
            'laudo_medico': ['laudo médico', 'laudo', 'exame', 'diagnóstico'],
            'nota_fiscal': ['nota fiscal', 'nf-e', 'cupom fiscal', 'danfe'],
            'recibo': ['recibo', 'comprovante de pagamento', 'quitação'],
            'procuracao': ['procuração', 'mandato', 'representação legal'],
            'contrato_aluguel': ['contrato de aluguel', 'locação', 'inquilino', 'locador'],
            'carta': ['carta', 'correspondência', 'missiva', 'letter', 'comunicação']
        }
        
        # Busca por palavras-chave relevantes
        if category in category_keywords:
            for keyword in category_keywords[category]:
                if keyword in text_lower:
                    patterns.append(keyword)
        
        # Padrões de formato melhorados
        date_patterns = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text_content)
        if date_patterns:
            patterns.append('has_date_format')
        
        cpf_patterns = re.findall(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text_content)
        if cpf_patterns:
            patterns.append('has_cpf_format')
        
        rg_patterns = re.findall(r'\d{1,2}\.\d{3}\.\d{3}-\d{1,2}', text_content)
        if rg_patterns:
            patterns.append('has_rg_format')
        
        cnpj_patterns = re.findall(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', text_content)
        if cnpj_patterns:
            patterns.append('has_cnpj_format')
        
        # Padrões de valores monetários
        money_patterns = re.findall(r'R\$\s*\d+[,.]?\d*', text_content)
        if money_patterns:
            patterns.append('has_money_format')
        
        # Padrões de CEP
        cep_patterns = re.findall(r'\d{5}-?\d{3}', text_content)
        if cep_patterns:
            patterns.append('has_cep_format')
        
        return patterns
    
    def add_or_update_pattern(self, pattern_type, pattern_value, category, cursor):
        """Adiciona ou atualiza um padrão aprendido"""
        # Verifica se o padrão já existe
        cursor.execute('''
            SELECT id, usage_count, confidence FROM learned_patterns
            WHERE pattern_type = ? AND pattern_value = ? AND category = ?
        ''', (pattern_type, pattern_value, category))
        
        result = cursor.fetchone()
        if result:
            # Atualiza padrão existente
            pattern_id, usage_count, confidence = result
            new_usage_count = usage_count + 1
            new_confidence = min(1.0, confidence + 0.1)  # Aumenta confiança gradualmente
            
            cursor.execute('''
                UPDATE learned_patterns 
                SET usage_count = ?, confidence = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_usage_count, new_confidence, pattern_id))
        else:
            # Adiciona novo padrão
            cursor.execute('''
                INSERT INTO learned_patterns 
                (pattern_type, pattern_value, category, confidence, usage_count)
                VALUES (?, ?, ?, 0.5, 1)
            ''', (pattern_type, pattern_value, category))
    
    def get_intelligent_classification(self, filename, text_content=None):
        """Usa padrões aprendidos para sugerir classificação com pontuação de confiança melhorada"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        category_scores = defaultdict(float)
        pattern_matches = defaultdict(int)
        
        # Analisa padrões do nome do arquivo
        filename_patterns = self.extract_filename_patterns(filename)
        for pattern in filename_patterns:
            cursor.execute('''
                SELECT category, confidence, usage_count FROM learned_patterns
                WHERE pattern_type = 'filename' AND pattern_value = ?
                ORDER BY confidence DESC, usage_count DESC
            ''', (pattern,))
            
            results = cursor.fetchall()
            for category, confidence, usage_count in results:
                # Pontuação melhorada baseada na confiança, uso e recência
                base_score = confidence * (1 + min(usage_count * 0.1, 2.0))  # Limita o boost por uso
                category_scores[category] += base_score
                pattern_matches[category] += 1
        
        # Analisa padrões do conteúdo de texto se disponível
        if text_content:
            # Busca padrões em todas as categorias conhecidas
            cursor.execute('SELECT DISTINCT category FROM learned_patterns')
            all_categories = [row[0] for row in cursor.fetchall()]
            
            for category in all_categories:
                text_patterns = self.extract_text_patterns(text_content, category)
                for pattern in text_patterns:
                    cursor.execute('''
                        SELECT confidence, usage_count FROM learned_patterns
                        WHERE pattern_type = 'text' AND pattern_value = ? AND category = ?
                    ''', (pattern, category))
                    
                    result = cursor.fetchone()
                    if result:
                        confidence, usage_count = result
                        base_score = confidence * (1 + min(usage_count * 0.1, 2.0))
                        category_scores[category] += base_score * 1.5  # Texto tem peso maior
                        pattern_matches[category] += 1
        
        conn.close()
        
        # Calcula confiança final baseada em múltiplos fatores
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            category, raw_score = best_category
            
            # Normaliza a confiança baseada no número de padrões encontrados
            pattern_count = pattern_matches[category]
            confidence_multiplier = min(1.0, 0.3 + (pattern_count * 0.2))  # Mais padrões = mais confiança
            
            # Confiança final entre 0.0 e 1.0
            final_confidence = min(1.0, raw_score * confidence_multiplier)
            
            return category, final_confidence
        
        return None, 0.0
    
    def update_category_stats(self, category):
        """Atualiza estatísticas de uma categoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO performance_stats 
            (category, total_classifications, correct_classifications, accuracy_rate, last_updated)
            VALUES (
                ?, 
                COALESCE((SELECT total_classifications FROM performance_stats WHERE category = ?), 0) + 1,
                COALESCE((SELECT correct_classifications FROM performance_stats WHERE category = ?), 0),
                COALESCE((SELECT accuracy_rate FROM performance_stats WHERE category = ?), 0.0),
                CURRENT_TIMESTAMP
            )
        ''', (category, category, category, category))
        
        conn.commit()
        conn.close()
    
    def update_performance_stats(self, category, was_correct):
        """Atualiza estatísticas de performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if was_correct:
            cursor.execute('''
                UPDATE performance_stats 
                SET correct_classifications = correct_classifications + 1,
                    accuracy_rate = CAST(correct_classifications AS REAL) / total_classifications,
                    last_updated = CURRENT_TIMESTAMP
                WHERE category = ?
            ''', (category,))
        
        conn.commit()
        conn.close()
    
    def record_positive_feedback(self, filename, category):
        """Registra feedback positivo do usuário e reforça padrões aprendidos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_feedback (filename, category, is_positive)
            VALUES (?, ?, TRUE)
        ''', (filename, category))

        # Extrai padrões do filename que funcionaram bem
        filename_patterns = self.extract_filename_patterns(filename)
        for pattern in filename_patterns:
            # Verifica se o padrão já existe
            cursor.execute('''
                SELECT id, confidence, usage_count FROM learned_patterns
                WHERE pattern_type = 'filename' AND pattern_value = ? AND category = ?
            ''', (pattern, category))

            result = cursor.fetchone()
            if result:
                # Aumenta confiança significativamente para feedback positivo
                pattern_id, confidence, usage_count = result
                new_confidence = min(1.0, confidence + 0.15)  # Boost maior
                cursor.execute('''
                    UPDATE learned_patterns
                    SET confidence = ?, usage_count = ?, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_confidence, usage_count + 1, pattern_id))
            else:
                # Cria novo padrão com confiança inicial boa
                cursor.execute('''
                    INSERT INTO learned_patterns (pattern_type, pattern_value, category, confidence, usage_count)
                    VALUES (?, ?, ?, 0.75, 1)
                ''', ('filename', pattern, category))

        conn.commit()
        conn.close()
        print(f"✅ Feedback positivo registrado: {filename} -> {category} (padrões reforçados)")

    def record_negative_feedback(self, filename, category):
        """Registra feedback negativo e penaliza padrões incorretos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_feedback (filename, category, is_positive)
            VALUES (?, ?, FALSE)
        ''', (filename, category))

        # Extrai padrões do filename que falharam
        filename_patterns = self.extract_filename_patterns(filename)
        for pattern in filename_patterns:
            # Reduz confiança apenas dos padrões associados a essa categoria incorreta
            cursor.execute('''
                UPDATE learned_patterns
                SET confidence = MAX(0.05, confidence - 0.20)
                WHERE pattern_type = 'filename' AND pattern_value = ? AND category = ?
            ''', (pattern, category))

        conn.commit()
        conn.close()
        print(f"❌ Feedback negativo registrado: {filename} -> {category} (padrões penalizados)")

    def get_performance_report(self):
        """Gera relatório de performance do sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT category, total_classifications, correct_classifications, accuracy_rate
            FROM performance_stats
            ORDER BY total_classifications DESC
        ''')

        stats = cursor.fetchall()

        # Estatísticas gerais
        cursor.execute('SELECT COUNT(*) FROM classification_history')
        total_classifications = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM classification_history WHERE feedback_provided = TRUE')
        total_feedback = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT pattern_value) FROM learned_patterns')
        learned_patterns = cursor.fetchone()[0]

        # Estatísticas de feedback (like/dislike)
        cursor.execute('SELECT COUNT(*) FROM user_feedback WHERE is_positive = TRUE')
        positive_feedback = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM user_feedback WHERE is_positive = FALSE')
        negative_feedback = cursor.fetchone()[0]

        # Feedback por categoria
        cursor.execute('''
            SELECT category,
                   SUM(CASE WHEN is_positive = TRUE THEN 1 ELSE 0 END) as likes,
                   SUM(CASE WHEN is_positive = FALSE THEN 1 ELSE 0 END) as dislikes
            FROM user_feedback
            GROUP BY category
            ORDER BY (likes + dislikes) DESC
        ''')
        feedback_by_category = cursor.fetchall()

        conn.close()

        return {
            'total_classifications': total_classifications,
            'total_feedback': total_feedback,
            'learned_patterns': learned_patterns,
            'positive_feedback': positive_feedback,
            'negative_feedback': negative_feedback,
            'feedback_by_category': feedback_by_category,
            'category_stats': stats
        }