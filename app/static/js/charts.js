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
                    borderColor: '#66fcf1',
                    backgroundColor: 'rgba(102, 252, 241, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.3,
                    pointBackgroundColor: '#66fcf1',
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#c5c6c7' }
                    },
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#c5c6c7' }
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
                        '#66fcf1',
                        '#8a2be2',
                        '#45a29e',
                        '#2ecc71',
                        '#f1c40f',
                        '#ff4c4c'
                    ],
                    borderWidth: 1,
                    borderColor: '#0b0c10'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#c5c6c7', font: { family: 'Inter' } }
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
                    backgroundColor: 'rgba(138, 43, 226, 0.2)',
                    borderColor: '#8a2be2',
                    borderWidth: 2,
                    pointBackgroundColor: '#8a2be2'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
                        grid: { color: 'rgba(255, 255, 255, 0.08)' },
                        pointLabels: { color: '#c5c6c7', font: { size: 11, family: 'Inter', weight: 'bold' } },
                        ticks: {
                            color: '#7a8288',
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
