import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio 
import pandas as pd

class DashboardComponents:
    def __init__(self, colors):
        self.colors = colors

    def render_metric_card(self, title, value, trend, trend_value):
        """Render a metric card for the dashboard"""
        trend_class = 'trend-up' if trend_value > 0 else 'trend-down' if trend_value < 0 else 'trend-neutral'
        return {
            'title': title,
            'value': value,
            'trend': trend,
            'trend_value': f"{abs(trend_value)}%" if trend_value != 0 else '',
            'trend_class': trend_class,
            'background': self.colors['card'],
            'text': self.colors['text'],
            'subtext': self.colors['subtext']
        }

    def create_gauge_chart(self, value, title, chart_id):
        """Create a gauge chart for ATS score or similar metrics"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'color': self.colors['text']}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': self.colors['subtext']},
                'bar': {'color': self.colors['primary']},
                'bgcolor': self.colors['background'],
                'bordercolor': self.colors['card'],
                'steps': [
                    {'range': [0, 50], 'color': self.colors['danger']},
                    {'range': [50, 75], 'color': self.colors['warning']},
                    {'range': [75, 100], 'color': self.colors['success']}
                ],
            }
        ))
        fig.update_layout(
            paper_bgcolor=self.colors['background'],
            font={'color': self.colors['text']},
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return pio.to_json(fig) 

    def create_bar_chart(self, categories, counts, title, chart_id):
        """Create a bar chart for skill distribution or job categories"""
        df = pd.DataFrame({
            'Category': categories,
            'Count': counts
        })
        fig = px.bar(
            df,
            x='Count',
            y='Category',
            orientation='h',
            title=title,
            labels={'Count': 'Count', 'Category': 'Category'}
        )
        fig.update_traces(marker_color=self.colors['primary'])
        fig.update_layout(
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text']},
            title_font_color=self.colors['text'],
            xaxis={'tickfont': {'color': self.colors['subtext']}},
            yaxis={'tickfont': {'color': self.colors['subtext']}},
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return pio.to_json(fig)  

    def create_trend_chart(self, dates, values, title, chart_id):
        df = pd.DataFrame({
            'Date': dates,
            'Submissions': values
        })
        
        fig = px.line(
            df,
            x='Date',
            y='Submissions',
            title=title,
            labels={'Date': 'Date', 'Submissions': 'Submissions'}
        )
        fig.update_traces(line_color=self.colors['primary'])
        fig.update_layout(
            paper_bgcolor=self.colors['background'],
            plot_bgcolor=self.colors['background'],
            font={'color': self.colors['text']},
            title_font_color=self.colors['text'],
            xaxis={'tickfont': {'color': self.colors['subtext']}},
            yaxis={'tickfont': {'color': self.colors['subtext']}},
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return pio.to_json(fig)  