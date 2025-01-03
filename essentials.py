import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import re
from plotly.subplots import make_subplots


class RobotScriptParser:
    @staticmethod
    def extract_coordinates(script_content):
        pattern = r'CalcRobT\(\[\[(.*?)\]'
        moves = []
        matches = re.finditer(pattern, script_content)
        for match in matches:
            coords_str = match.group(1)
            coords = [float(x) for x in coords_str.split(',')[:3]]
            moves.append(coords)
        return moves

class RobotPathVisualizer:
    def __init__(self, test_case):
        parser = RobotScriptParser()
        self.master_moves = parser.extract_coordinates(test_case['master_script'])
        self.test_moves = parser.extract_coordinates(test_case['test_script'])
        self.test_name = test_case.get('testname', 'Unknown Test')
        self.test_date = test_case.get('startdate', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.test_status = test_case.get('test_status', '')

    def plot_3d_paths(self):
        master_array = np.array(self.master_moves)
        test_array = np.array(self.test_moves)
        
        fig = go.Figure()
        
        # Add master path trace
        fig.add_trace(go.Scatter3d(
            x=master_array[:, 0],
            y=master_array[:, 1],
            z=master_array[:, 2],
            mode='lines+markers',
            name='Master Path',
            line=dict(color='blue', width=4),
            marker=dict(size=6)
        ))
        
        # Add test path trace
        fig.add_trace(go.Scatter3d(
            x=test_array[:, 0],
            y=test_array[:, 1],
            z=test_array[:, 2],
            mode='lines+markers',
            name='Test Path',
            line=dict(color='red', width=4, dash='dash'),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            scene=dict(
                xaxis_title='X Axis (mm)',
                yaxis_title='Y Axis (mm)',
                zaxis_title='Z Axis (mm)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            title='3D Comparison of Robot Paths',
            showlegend=True,
            template='plotly_white',
            height=800,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig

    def plot_deviation_analysis(self):
        min_len = min(len(self.master_moves), len(self.test_moves))
        master_array = np.array(self.master_moves[:min_len])
        test_array = np.array(self.test_moves[:min_len])
        deviations = master_array - test_array
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                'Absolute Deviations per Axis',
                'Deviation Heatmap'
            )
        )
        
        # Plot absolute deviations per axis
        for idx, axis in enumerate(['X', 'Y', 'Z']):
            fig.add_trace(
                go.Scatter(
                    y=np.abs(deviations[:, idx]),
                    mode='lines+markers',
                    name=f'{axis}-axis',
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # Heatmap
        fig.add_trace(
            go.Heatmap(
                z=deviations,
                x=['X', 'Y', 'Z'],
                y=[f'Move {i+1}' for i in range(len(deviations))],
                colorscale='RdBu',
                zmid=0,
                colorbar=dict(
                    tickvals=[-np.max(np.abs(deviations)), 0, np.max(np.abs(deviations))],  # Show min, mid, and max ticks
                    ticktext=['Low', '0', 'High'],  # Customize the colorbar ticks
                    len=0.6 # Length of the colorbar
                ),
                hovertemplate='x = %{x}<br>y = %{y}<br>Diff = %{z}<extra></extra>'  # Customize hover information


            ),
            row=1, col=2
        )
        
        # # Cumulative path length
        # master_diffs = np.diff(master_array, axis=0)
        # test_diffs = np.diff(test_array, axis=0)
        # master_lengths = np.cumsum(np.sqrt(np.sum(master_diffs**2, axis=1)))
        # test_lengths = np.cumsum(np.sqrt(np.sum(test_diffs**2, axis=1)))
        
        # fig.add_trace(
        #     go.Scatter(y=master_lengths, name='Master Path', mode='lines+markers'),
        #     row=2, col=1
        # )
        # fig.add_trace(
        #     go.Scatter(y=test_lengths, name='Test Path', mode='lines+markers'),
        #     row=2, col=1
        # )
        
        # # Deviation distribution
        # fig.add_trace(
        #     go.Histogram(x=deviations.flatten(), nbinsx=30, name='Deviations'),
        #     row=2, col=2
        # )
    
        # Update layout for better appearance
        fig.update_layout(
            height=500,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig

    def generate_insights_report(self):
        min_len = min(len(self.master_moves), len(self.test_moves))
        master_array = np.array(self.master_moves[:min_len])
        test_array = np.array(self.test_moves[:min_len])
        deviations = master_array - test_array
        
        return {
            'test_name': self.test_name,
            'test_date': self.test_date,
            'test_status': self.test_status,
            'max_deviation': {
                'x': np.max(np.abs(deviations[:, 0])),
                'y': np.max(np.abs(deviations[:, 1])),
                'z': np.max(np.abs(deviations[:, 2]))
            },
            'mean_deviation': {
                'x': np.mean(np.abs(deviations[:, 0])),
                'y': np.mean(np.abs(deviations[:, 1])),
                'z': np.mean(np.abs(deviations[:, 2]))
            }
        }
