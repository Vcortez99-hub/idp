// Dashboard de Aprendizado Inteligente
class LearningDashboard {
    constructor() {
        this.performanceData = null;
        this.init();
    }

    init() {
        this.loadPerformanceData();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Botão de atualizar dados
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadPerformanceData());
        }

        // Botão de feedback
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('feedback-btn')) {
                const filename = e.target.dataset.filename;
                const currentCategory = e.target.dataset.category;
                this.showFeedbackModal(filename, currentCategory);
            }
        });
    }

    async loadPerformanceData() {
        try {
            const response = await fetch('/api/performance');
            if (response.ok) {
                this.performanceData = await response.json();
                this.renderDashboard();
            } else {
                console.error('Erro ao carregar dados de performance');
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
        }
    }

    renderDashboard() {
        if (!this.performanceData) return;

        this.renderOverviewStats();
        this.renderFeedbackByCategory();
        this.renderCategoryStats();
        this.renderLearningProgress();
    }

    renderFeedbackByCategory() {
        const container = document.getElementById('feedback-category-content');
        if (!container || !this.performanceData.feedback_by_category) return;

        const feedbackData = this.performanceData.feedback_by_category;

        if (feedbackData.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: #9ca3af;">Nenhum feedback registrado ainda. Comece avaliando as classificações!</p>';
            return;
        }

        let html = `
            <div class="feedback-table">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #374151; text-align: left;">
                            <th style="padding: 12px;">Categoria</th>
                            <th style="padding: 12px;">👍 Likes</th>
                            <th style="padding: 12px;">👎 Dislikes</th>
                            <th style="padding: 12px;">Total</th>
                            <th style="padding: 12px;">Taxa de Aprovação</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        feedbackData.forEach(([category, likes, dislikes]) => {
            const total = likes + dislikes;
            const approvalRate = total > 0 ? ((likes / total) * 100).toFixed(1) : 0;
            const approvalColor = approvalRate >= 80 ? '#10b981' : approvalRate >= 60 ? '#f59e0b' : '#ef4444';

            html += `
                <tr style="border-bottom: 1px solid #4b5563;">
                    <td style="padding: 12px; font-weight: 600;">${category}</td>
                    <td style="padding: 12px; color: #10b981;">${likes}</td>
                    <td style="padding: 12px; color: #ef4444;">${dislikes}</td>
                    <td style="padding: 12px;">${total}</td>
                    <td style="padding: 12px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="flex: 1; background: #374151; height: 8px; border-radius: 4px; overflow: hidden;">
                                <div style="width: ${approvalRate}%; background: ${approvalColor}; height: 100%;"></div>
                            </div>
                            <span style="color: ${approvalColor}; font-weight: 600; min-width: 50px;">${approvalRate}%</span>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;
    }

    renderOverviewStats() {
        const { total_classifications, total_feedback, learned_patterns, positive_feedback, negative_feedback } = this.performanceData;

        const totalUserFeedback = positive_feedback + negative_feedback;
        const approvalRate = totalUserFeedback > 0 ?
            ((positive_feedback / totalUserFeedback) * 100).toFixed(1) :
            'N/A';

        // Atualiza os números nos cards existentes
        document.getElementById('total-classifications').textContent = total_classifications || 0;
        document.getElementById('total-feedback').textContent = total_feedback || 0;
        document.getElementById('learned-patterns').textContent = learned_patterns || 0;
        document.getElementById('positive-feedback').textContent = positive_feedback || 0;
        document.getElementById('negative-feedback').textContent = negative_feedback || 0;
        document.getElementById('approval-rate').textContent = approvalRate !== 'N/A' ? `${approvalRate}%` : 'N/A';
    }

    renderCategoryStats() {
        const container = document.getElementById('category-stats');
        if (!container || !this.performanceData.category_stats) return;

        const stats = this.performanceData.category_stats;
        
        let html = `
            <h3>Performance por Categoria</h3>
            <div class="category-table">
                <table>
                    <thead>
                        <tr>
                            <th>Categoria</th>
                            <th>Total</th>
                            <th>Corretas</th>
                            <th>Taxa de Acerto</th>
                            <th>Barra de Progresso</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        stats.forEach(([category, total, correct, accuracy]) => {
            const accuracyPercent = (accuracy * 100).toFixed(1);
            html += `
                <tr>
                    <td>${category}</td>
                    <td>${total}</td>
                    <td>${correct}</td>
                    <td>${accuracyPercent}%</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${accuracyPercent}%"></div>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;
    }

    renderLearningProgress() {
        const container = document.getElementById('learning-progress');
        if (!container) return;

        const { total_classifications, learned_patterns } = this.performanceData;
        
        // Calcula métricas de progresso
        const learningRate = total_classifications > 0 ? 
            (learned_patterns / total_classifications * 100).toFixed(1) : 0;

        container.innerHTML = `
            <h3>Progresso do Aprendizado</h3>
            <div class="learning-metrics">
                <div class="metric">
                    <label>Taxa de Aprendizado:</label>
                    <span>${learningRate}% (${learned_patterns} padrões de ${total_classifications} classificações)</span>
                </div>
                <div class="metric">
                    <label>Status do Sistema:</label>
                    <span class="status ${learned_patterns > 10 ? 'active' : 'learning'}">
                        ${learned_patterns > 10 ? 'Ativo e Aprendendo' : 'Coletando Dados'}
                    </span>
                </div>
            </div>
        `;
    }

    showFeedbackModal(filename, currentCategory) {
        // Cria modal de feedback
        const modal = document.createElement('div');
        modal.className = 'feedback-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Corrigir Classificação</h3>
                <p>Arquivo: <strong>${filename}</strong></p>
                <p>Classificação atual: <strong>${currentCategory}</strong></p>
                <label for="correct-category">Categoria correta:</label>
                <select id="correct-category">
                    <option value="">Selecione a categoria correta</option>
                    <!-- Categorias serão carregadas dinamicamente -->
                </select>
                <div class="modal-buttons">
                    <button onclick="this.closest('.feedback-modal').remove()">Cancelar</button>
                    <button onclick="learningDashboard.submitFeedback('${filename}')">Enviar Feedback</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.loadCategoriesForFeedback();
    }

    async loadCategoriesForFeedback() {
        try {
            const response = await fetch('/static/categories.json');
            const categories = await response.json();
            
            const select = document.getElementById('correct-category');
            if (select) {
                Object.entries(categories).forEach(([key, name]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Erro ao carregar categorias:', error);
        }
    }

    async submitFeedback(filename) {
        const correctCategory = document.getElementById('correct-category').value;
        
        if (!correctCategory) {
            alert('Por favor, selecione a categoria correta.');
            return;
        }

        try {
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: filename,
                    correct_category: correctCategory
                })
            });

            if (response.ok) {
                const result = await response.json();
                alert(result.message);
                document.querySelector('.feedback-modal').remove();
                this.loadPerformanceData(); // Atualiza os dados
            } else {
                alert('Erro ao enviar feedback');
            }
        } catch (error) {
            console.error('Erro ao enviar feedback:', error);
            alert('Erro ao enviar feedback');
        }
    }
}

// Inicializa o dashboard quando a página carrega
let learningDashboard;
document.addEventListener('DOMContentLoaded', () => {
    learningDashboard = new LearningDashboard();
});