import plotly.graph_objects as go
def price_chart(df, ticker):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], name=ticker))
    for c in ["EMA20","EMA50","EMA200"]:
        if c in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[c], mode="lines", name=c))
    fig.update_layout(height=390, margin=dict(l=10,r=10,t=35,b=10), xaxis_rangeslider_visible=False, legend=dict(orientation="h"))
    return fig
