from graphviz import Digraph

dot = Digraph(format='png')

# Graph flows top to bottom (vertical tree), left-aligned
dot.attr(rankdir='LR', dpi='300', fontname='Helvetica', nodesep='0.5', ranksep='1.2')

# Root node on the left
dot.node('root', 'IA3 Digital Solutions Project', shape='ellipse')

# First-level categories branching to the right
branches = {
    'Proto-personas': ['Lyndsey (Farmer)', 'Carol (Planner)', 'Shane (Developer)'],
    'Problem and Opportunity': ['View local weather', 'Need real-time data', 'Users require filtering'],
    'Key Areas of Study (IA3)': ['Part 1: Research', 'Part 2: Development', 'Part 3: Impacts'],
    'Data Exchange Components': ['JSON API access', 'Secure data handling', 'User-specific filtering'],
    'Solution Specifications': ['Login system', 'Dashboard output', 'Settings/preferences'],
    'User Stories': ['Farmer: Rainfall + Temp', 'Planner: UV + Wind', 'Developer: Solar + Wind Dir'],
    'Mind Map Flow': ['API → Transform → Display', 'User filters apply logic'],
    'Wireframes': ['Login Wireframe', 'Dashboard Wireframe'],
    'Authentication and Security': ['SHA256 Password Hashing', 'No PII Stored', 'HTTPS Protocol', 'Validation and Filtering']
}

# Add all first and second level nodes
for i, (section, items) in enumerate(branches.items()):
    parent_id = f"branch{i}"
    dot.node(parent_id, section, shape='ellipse')
    dot.edge('root', parent_id)

    for j, item in enumerate(items):
        child_id = f"{parent_id}_{j}"
        dot.node(child_id, item, shape='ellipse')
        dot.edge(parent_id, child_id)

# Render to PNG (change format to 'svg' if needed)
dot.render('IA3_MindMap_VerticalBranchRight', view=True)
