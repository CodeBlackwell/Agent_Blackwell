document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('mynetwork');
    const dropdown = document.getElementById('workflow-dropdown');
    let allWorkflowsData = {};

    // Options for the Vis.js network
    const options = {
        layout: {
            hierarchical: {
                direction: 'UD', // Up-Down direction
                sortMethod: 'directed',
                levelSeparation: 150,
            },
        },
        edges: {
            arrows: 'to',
            color: '#848484',
            font: {
                size: 12
            },
            smooth: {
                type: 'cubicBezier'
            }
        },
        nodes: {
            shape: 'box',
            size: 30,
            font: {
                size: 14,
                color: '#ffffff'
            },
            borderWidth: 2,
            color: {
                background: '#6E6EFD',
                border: '#5A5AFF',
                highlight: {
                    background: '#8A8AFF',
                    border: '#5A5AFF'
                }
            }
        },
        physics: {
            enabled: false, // Turn off physics for a static layout
        },
        interaction: {
            hover: true
        }
    };

    // Function to draw the graph
    function drawGraph(workflowName) {
        const workflowData = allWorkflowsData[workflowName];
        if (!workflowData) return;

        const data = {
            nodes: new vis.DataSet(workflowData.nodes),
            edges: new vis.DataSet(workflowData.edges)
        };

        const network = new vis.Network(container, data, options);
    }

    // Fetch the workflow data and populate the dropdown
    fetch('interactive_workflow_data.json')
        .then(response => response.json())
        .then(data => {
            allWorkflowsData = data;
            const workflowNames = Object.keys(data);

            workflowNames.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                dropdown.appendChild(option);
            });

            // Draw the first workflow by default
            if (workflowNames.length > 0) {
                drawGraph(workflowNames[0]);
            }

            // Add event listener for dropdown changes
            dropdown.addEventListener('change', (event) => {
                drawGraph(event.target.value);
            });
        })
        .catch(error => console.error('Error loading workflow data:', error));
});
