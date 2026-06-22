// Chart Rendering Orchestrator - InterviewAI

document.addEventListener('DOMContentLoaded', () => {
    // 1. Performance Trend Line Chart (Analytics page)
    const trendCtx = document.getElementById('chart-performance-trend');
    if (trendCtx) {
        const rawData = JSON.parse(trendCtx.dataset.chartData || '[]');
        const labels = rawData.map(item => item.label);
        const scores = rawData.map(item => item.score);
        
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Interview Score (%)',
                    data: scores,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#8b5cf6',
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#00d4ff',
                    pointHoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        ticks: { color: '#cbd5e1' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        ticks: { color: '#cbd5e1' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // 2. Category Distribution Doughnut Chart (Analytics page)
    const catCtx = document.getElementById('chart-category-dist');
    if (catCtx) {
        const rawData = JSON.parse(catCtx.dataset.chartData || '{}');
        const labels = Object.keys(rawData);
        const data = Object.values(rawData);
        
        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#8b5cf6', // Violet
                        '#3b82f6', // Blue
                        '#00d4ff', // Cyan
                        '#ec4899', // Pink
                        '#10b981', // Emerald
                        '#f59e0b'  // Amber
                    ],
                    borderWidth: 2,
                    borderColor: '#030712'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#cbd5e1', font: { family: 'Inter', size: 11 } }
                    }
                }
            }
        });
    }

    // 3. Skill Heatmap Radar Chart (Report details page)
    const radarCtx = document.getElementById('chart-skill-radar');
    if (radarCtx) {
        const rawData = JSON.parse(radarCtx.dataset.chartData || '{}');
        const labels = Object.keys(rawData);
        const data = Object.values(rawData);
        
        new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Skill Proficiency',
                    data: data,
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: '#8b5cf6',
                    borderWidth: 2,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#8b5cf6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        pointLabels: { color: '#cbd5e1', font: { size: 11, family: 'Inter', weight: 'bold' } },
                        ticks: {
                            color: '#9ca3af',
                            backdropColor: 'transparent',
                            showLabelBackdrop: false
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
});
