document.addEventListener('DOMContentLoaded', function() {
    const projects = [
        {
            id: 'healthcare',
            name: 'Healthcare Medical KG',
            color: '#e74c3c',
            status: 'verified',
            repo: 'itsPremkumar/aetheria-healthcare',
            commitSha: 'd9ea50e',
            testCount: 15,
            fileCount: 42,
            lastUpdated: '2026-09-03 14:23'
        },
        {
            id: 'legal',
            name: 'Legal Contract Analysis KG',
            color: '#3498db',
            status: 'verified',
            repo: 'itsPremkumar/aetheria-legal',
            commitSha: 'd9ea50e',
            testCount: 22,
            fileCount: 38,
            lastUpdated: '2026-09-03 14:45'
        },
        {
            id: 'education',
            name: 'Education Learning Assistant KG',
            color: '#2ecc71',
            status: 'pending',
            repo: 'itsPremkumar/aetheria-education',
            commitSha: 'pending',
            testCount: 0,
            fileCount: 0,
            lastUpdated: 'Pending creation'
        },
        {
            id: 'finance',
            name: 'Finance Reasoning KG',
            color: '#f39c12',
            status: 'pending',
            repo: 'itsPremkumar/aetheria-finance',
            commitSha: 'pending',
            testCount: 0,
            fileCount: 0,
            lastUpdated: 'Pending creation'
        },
        {
            id: 'agriculture',
            name: 'Agriculture Crop & Soil KG',
            color: '#27ae60',
            status: 'pending',
            repo: 'itsPremkumar/aetheria-agriculture',
            commitSha: 'pending',
            testCount: 0,
            fileCount: 0,
            lastUpdated: 'Pending creation'
        },
        {
            id: 'manufacturing',
            name: 'Manufacturing Supply Chain KG',
            color: '#9b59b6',
            status: 'building',
            repo: 'itsPremkumar/aetheria-manufacturing',
            commitSha: 'building',
            testCount: 0,
            fileCount: 0,
            lastUpdated: 'In progress'
        },
        {
            id: 'customer',
            name: 'Customer Service Knowledge Base KG',
            color: '#e67e22',
            status: 'building',
            repo: 'itsPremkumar/aetheria-customer-service',
            commitSha: 'building',
            testCount: 0,
            fileCount: 0,
            lastUpdated: 'In progress'
        }
    ];

    const grid = document.getElementById('projectsGrid');

    projects.forEach(project => {
        const card = document.createElement('div');
        card.className = 'project-card';

        const statusClass = `status-${project.status}`;
        const statusText = project.status.charAt(0).toUpperCase() + project.status.slice(1);

        card.innerHTML = `
            <div class="project-header">
                <div class="project-name" style="color: ${project.color}">${project.name}</div>
                <div class="project-status ${statusClass}">${statusText}</div>
            </div>
            <div class="project-details">
                <div class="detail-item">
                    <span class="detail-label">Repository</span>
                    <span class="detail-value">${project.repo}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Commit SHA</span>
                    <span class="detail-value">${project.commitSha}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Tests</span>
                    <span class="detail-value">${project.testCount}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Files</span>
                    <span class="detail-value">${project.fileCount}</span>
                </div>
            </div>
            <div class="project-links">
                <a href="https://github.com/${project.repo}" target="_blank" class="project-link link-github">GitHub</a>
                <a href="https://github.com/${project.repo}/actions" target="_blank" class="project-link link-ci">CI/CD</a>
                <a href="https://github.com/${project.repo}/wiki" target="_blank" class="project-link link-docs">Docs</a>
            </div>
        `;

        grid.appendChild(card);
    });

    document.getElementById('lastUpdated').textContent = `Last updated: ${new Date().toLocaleString()}`;
});
