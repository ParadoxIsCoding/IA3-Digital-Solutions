from graphviz import Digraph

dot = Digraph(comment='IA3 Mind Map Vertical Layout')
dot.attr(rankdir='TB', size='10')  # Top to Bottom layout

# Central node
dot.node('A', 'IA3 Digital Solutions Project')

# Major branches
branches = [
    'Proto-personas',
    'Problem and Opportunity',
    'Key Areas of Study (IA3)',
    'Data Exchange Components',
    'Solution Specifications',
    'User Stories',
    'Mind Map Flow',
    'Wireframes',
    'Authentication & Security'
]

# Add major branches
for i, b in enumerate(branches):
    dot.node(f'B{i}', b)
    dot.edge('A', f'B{i}')

# Sub-branches
sub_branches = {
    'B0': ['Lyndsey (Farmer)', 'Carol (Planner)', 'Shane (Developer)'],
    'B1': ['View local weather', 'Need real-time data', 'Users require filtering'],
    'B2': ['Part 1: Research', 'Part 2: Development', 'Part 3: Impacts'],
    'B3': ['JSON API access', 'Secure data handling', 'User-specific filtering'],
    'B4': ['Login system', 'Dashboard output', 'Settings/preferences'],
    'B5': ['Farmer: Rainfall + Temp', 'Planner: UV + Wind', 'Developer: Solar + Wind Dir'],
    'B6': ['API → Transform → Display', 'User filters apply logic'],
    'B7': ['Login Wireframe', 'Dashboard Wireframe'],
    'B8': ['SHA256 Password Hashing', 'No PII Stored', 'HTTPS Protocol', 'Validation and Filtering']
}

# Add sub-branches
for parent, children in sub_branches.items():
    for j, label in enumerate(children):
        node_id = f'{parent}_{j}'
        dot.node(node_id, label)
        dot.edge(parent, node_id)

# Render the diagram as SVG (you can change format to 'png' if you prefer)
dot.render('IA3_MindMap_Vertical', format='svg', cleanup=True)
