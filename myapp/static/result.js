document.addEventListener("DOMContentLoaded", function() {
    // Define cluster colors
    const clusterColors = [
        '#FF5733', '#33FF57', '#3357FF', '#F033FF',
        '#FF33A8', '#33FFF0', '#FFD133', '#8C33FF'
    ];

    // Add CSS for cluster badges
    const style = document.createElement('style');
    style.textContent = clusterColors.map((color, index) =>
        `.bg-cluster-${index} { background-color: ${color}; color: white; }`
    ).join('\n');
    document.head.appendChild(style);

    // Check if we have data
    const pieLabels = {{ pie_labels|safe }};
    const pieValues = {{ pie_values|safe }};
    const barLabels = {{ bar_labels|safe }};
    const barValues = {{ bar_values|safe }};
    const lineLabels = {{ line_labels|safe }};
    const lineValues = {{ line_values|safe }};

    console.log("Pie Chart Data:", pieLabels, pieValues);
    console.log("Bar Chart Data:", barLabels, barValues);
    console.log("Line Chart Data:", lineLabels, lineValues);

    if (pieLabels.length > 0) {
        // Create Pie Chart
        new Chart(document.getElementById('pieChart'), {
            type: 'doughnut',
            data: {
                labels: pieLabels,
                datasets: [{
                    data: pieValues,
                    backgroundColor: ['#DC3545', '#007BFF', '#FFC107', '#28A745', '#6F42C1', '#FD7E14', '#20C997', '#6C757D'],
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    }
                }
            }
        });

        // Create Bar Chart
        new Chart(document.getElementById('barChart'), {
            type: 'bar',
            data: {
                labels: barLabels,
                datasets: [{
                    label: 'Number of Crimes',
                    data: barValues,
                    backgroundColor: '#343A40',
                    borderColor: '#343A40',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Crimes'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Location'
                        }
                    }
                }
            }
        });

        // Create Line Chart
        new Chart(document.getElementById('lineChart'), {
            type: 'line',
            data: {
                labels: lineLabels,
                datasets: [{
                    label: 'Number of Crimes',
                    data: lineValues,
                    borderColor: '#007BFF',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Crimes'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Month/Year'
                        }
                    }
                }
            }
        });

        // Initialize the map
        const map = L.map('map').setView([8.9485, 125.6217], 12);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Add markers for each crime location
        const crimeData = [
            {% for crime in crimes %}
                {% if crime.latitude and crime.longitude %}
                {
                    lat: {{ crime.latitude }},
                    lng: {{ crime.longitude }},
                    type: "{{ crime.crime_type }}",
                    location: "{{ crime.location }}",
                    date: "{{ crime.date|date:'F Y' }}",
                    cluster: {% if crime.cluster is not None %}{{ crime.cluster }}{% else %}null{% endif %}
                },
                {% endif %}
            {% endfor %}
        ];

        // Group markers by cluster
        const clusterGroups = {};

        crimeData.forEach(crime => {
            const clusterKey = crime.cluster !== null ? crime.cluster : 'none';

            if (!clusterGroups[clusterKey]) {
                clusterGroups[clusterKey] = [];
            }

            clusterGroups[clusterKey].push(crime);
        });

        // Add markers for each cluster with different colors
        Object.entries(clusterGroups).forEach(([cluster, crimes]) => {
            const color = cluster !== 'none' ? clusterColors[cluster % clusterColors.length] : '#999999';

            crimes.forEach(crime => {
                const marker = L.circleMarker([crime.lat, crime.lng], {
                    radius: 8,
                    fillColor: color,
                    color: '#000',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map);

                marker.bindPopup(`
                    <strong>Crime Type:</strong> ${crime.type}<br>
                    <strong>Location:</strong> ${crime.location}<br>
                    <strong>Date:</strong> ${crime.date}<br>
                    <strong>Cluster:</strong> ${crime.cluster !== null ? `Cluster ${crime.cluster}` : 'No Cluster'}
                `);
            });
        });

        // Fit map to bounds of all markers
        if (crimeData.length > 0) {
            const bounds = crimeData.map(crime => [crime.lat, crime.lng]);
            map.fitBounds(bounds);
        }
    }
});