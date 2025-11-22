"""
Advanced Visualization Module
Provides enhanced interactive visualizations using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import networkx as nx
from typing import List, Dict, Any, Tuple
import numpy as np


def create_interaction_network(conflicts: List[Dict[str, Any]]) -> go.Figure:
    """
    Create an interactive network graph showing drug-drug and drug-condition interactions.
    
    Args:
        conflicts: List of conflict dictionaries
        
    Returns:
        Plotly Figure object
    """
    if not conflicts:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No conflicts to visualize",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title="Drug Interaction Network",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=600
        )
        return fig
    
    # Build network graph
    G = nx.Graph()
    
    # Color mapping for severity
    severity_colors = {
        'Major': '#f44336',
        'Moderate': '#ff9800',
        'Minor': '#fbc02d'
    }
    
    edge_data = []
    node_set = set()
    
    for conflict in conflicts:
        item_a = conflict['item_a']
        item_b = conflict['item_b']
        severity = conflict['severity']
        
        node_set.add(item_a)
        node_set.add(item_b)
        
        G.add_edge(item_a, item_b, 
                   severity=severity, 
                   weight=conflict.get('score', 1),
                   recommendation=conflict.get('recommendation', ''))
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Create edge traces (one per severity level for legend)
    edge_traces = {}
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        severity = edge[2]['severity']
        
        if severity not in edge_traces:
            edge_traces[severity] = {
                'x': [], 'y': [],
                'color': severity_colors[severity],
                'name': severity
            }
        
        edge_traces[severity]['x'].extend([x0, x1, None])
        edge_traces[severity]['y'].extend([y0, y1, None])
    
    # Create node trace
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Count connections
        connections = len(list(G.neighbors(node)))
        node_size.append(20 + connections * 5)
        
        # Hover text
        node_text.append(f"{node}<br>Connections: {connections}")
    
    # Build figure
    fig = go.Figure()
    
    # Add edge traces
    for severity, data in edge_traces.items():
        fig.add_trace(go.Scatter(
            x=data['x'], y=data['y'],
            mode='lines',
            line=dict(width=2, color=data['color']),
            hoverinfo='none',
            name=f"{severity} Conflict",
            showlegend=True
        ))
    
    # Add node trace
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        marker=dict(
            size=node_size,
            color='#4CAF50',
            line=dict(width=2, color='white')
        ),
        text=[node for node in G.nodes()],
        textposition="top center",
        textfont=dict(size=10),
        hovertext=node_text,
        hoverinfo='text',
        name='Drugs/Conditions',
        showlegend=True
    ))
    
    fig.update_layout(
        title="Drug Interaction Network",
        titlefont_size=16,
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig


def create_3d_conflict_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Create 3D scatter plot of conflicts by severity, type, and score.
    
    Args:
        df: DataFrame with conflict data
        
    Returns:
        Plotly Figure object
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for 3D visualization",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig
    
    # Map severity to numeric values for z-axis
    severity_map = {'Minor': 1, 'Moderate': 2, 'Major': 3}
    df['severity_num'] = df['severity'].map(severity_map)
    
    # Color map
    color_map = {
        'Major': '#f44336',
        'Moderate': '#ff9800',
        'Minor': '#fbc02d'
    }
    
    fig = go.Figure()
    
    for severity in ['Minor', 'Moderate', 'Major']:
        subset = df[df['severity'] == severity]
        if not subset.empty:
            fig.add_trace(go.Scatter3d(
                x=subset.index,
                y=subset['score'],
                z=subset['severity_num'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=color_map[severity],
                    line=dict(color='white', width=1)
                ),
                text=subset.apply(
                    lambda row: f"{row['item_a']} - {row['item_b']}<br>"
                                f"Type: {row['type']}<br>"
                                f"Score: {row['score']}", 
                    axis=1
                ),
                hoverinfo='text',
                name=severity
            ))
    
    fig.update_layout(
        title="3D Conflict Analysis",
        scene=dict(
            xaxis_title="Conflict Index",
            yaxis_title="Severity Score",
            zaxis_title="Severity Level",
            xaxis=dict(backgroundcolor="rgba(230, 230, 230, 0.5)"),
            yaxis=dict(backgroundcolor="rgba(230, 230, 230, 0.5)"),
            zaxis=dict(backgroundcolor="rgba(230, 230, 230, 0.5)")
        ),
        height=600,
        showlegend=True
    )
    
    return fig


def create_sankey_diagram(conflicts: List[Dict[str, Any]], 
                         prescriptions: Dict[str, List[str]]) -> go.Figure:
    """
    Create Sankey diagram showing flow from conditions to drugs to conflicts.
    
    Args:
        conflicts: List of conflict dictionaries
        prescriptions: Dict mapping patient conditions to prescribed drugs
        
    Returns:
        Plotly Figure object
    """
    if not conflicts:
        fig = go.Figure()
        fig.add_annotation(
            text="No conflicts to visualize",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig
    
    # Build node and link data
    nodes = []
    node_map = {}
    links = {'source': [], 'target': [], 'value': []}
    
    def add_node(label, group):
        if label not in node_map:
            node_map[label] = len(nodes)
            nodes.append({'label': label, 'group': group})
        return node_map[label]
    
    # Add flows: condition -> drug -> conflict
    drug_counts = {}
    conflict_counts = {}
    
    for conflict in conflicts:
        # Drugs involved
        drugs = [conflict['item_a'], conflict['item_b']]
        for drug in drugs:
            if drug not in drug_counts:
                drug_counts[drug] = 0
            drug_counts[drug] += 1
        
        # Conflict type
        conflict_key = f"{conflict['severity']} Conflict"
        if conflict_key not in conflict_counts:
            conflict_counts[conflict_key] = 0
        conflict_counts[conflict_key] += 1
    
    # Create simplified flow
    condition_node = add_node("Prescriptions", "source")
    
    for drug, count in drug_counts.items():
        drug_node = add_node(drug, "drug")
        links['source'].append(condition_node)
        links['target'].append(drug_node)
        links['value'].append(count)
    
    for conflict_type, count in conflict_counts.items():
        conflict_node = add_node(conflict_type, "conflict")
        # Link from drugs to conflicts (simplified)
        for drug in list(drug_counts.keys())[:3]:  # Limit to top 3 drugs
            drug_node = node_map[drug]
            links['source'].append(drug_node)
            links['target'].append(conflict_node)
            links['value'].append(count // len(drug_counts))
    
    # Create figure
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[n['label'] for n in nodes],
            color=['#4CAF50' if n['group'] == 'source' else
                   '#2196F3' if n['group'] == 'drug' else
                   '#f44336' for n in nodes]
        ),
        link=dict(
            source=links['source'],
            target=links['target'],
            value=links['value']
        )
    )])
    
    fig.update_layout(
        title="Prescription Flow: Drugs → Conflicts",
        font_size=12,
        height=500
    )
    
    return fig


def create_heatmap_matrix(df: pd.DataFrame) -> go.Figure:
    """
    Create heatmap showing drug-drug conflict matrix.
    
    Args:
        df: DataFrame with conflict data
        
    Returns:
        Plotly Figure object
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No conflicts to visualize",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig
    
    # Get unique items
    all_items = sorted(set(df['item_a'].tolist() + df['item_b'].tolist()))
    n = len(all_items)
    
    # Create matrix
    matrix = np.zeros((n, n))
    severity_text = [['' for _ in range(n)] for _ in range(n)]
    
    severity_score = {'Minor': 1, 'Moderate': 2, 'Major': 3}
    
    for _, row in df.iterrows():
        i = all_items.index(row['item_a'])
        j = all_items.index(row['item_b'])
        
        score = severity_score[row['severity']]
        matrix[i][j] = score
        matrix[j][i] = score
        
        text = f"{row['severity']}"
        severity_text[i][j] = text
        severity_text[j][i] = text
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=all_items,
        y=all_items,
        text=severity_text,
        texttemplate="%{text}",
        textfont={"size": 8},
        colorscale=[
            [0, '#ffffff'],
            [0.33, '#fbc02d'],
            [0.66, '#ff9800'],
            [1, '#f44336']
        ],
        hovertemplate='%{y} ↔ %{x}<br>Severity: %{text}<extra></extra>',
        showscale=True,
        colorbar=dict(
            title="Severity",
            tickvals=[0, 1, 2, 3],
            ticktext=["None", "Minor", "Moderate", "Major"]
        )
    ))
    
    fig.update_layout(
        title="Drug-Drug Interaction Heatmap",
        xaxis_title="Drug/Condition",
        yaxis_title="Drug/Condition",
        height=600,
        xaxis={'side': 'bottom'},
        yaxis={'autorange': 'reversed'}
    )
    
    return fig


def enhance_chart_interactivity(fig: go.Figure) -> go.Figure:
    """
    Add enhanced interactivity to existing charts.
    
    Args:
        fig: Existing Plotly figure
        
    Returns:
        Enhanced figure
    """
    fig.update_layout(
        hovermode='closest',
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    # Add range slider for time-based data
    fig.update_xaxes(rangeslider_visible=False)
    
    # Enable click events
    fig.update_traces(
        marker=dict(line=dict(width=1, color='white')),
        selector=dict(mode='markers')
    )
    
    return fig
