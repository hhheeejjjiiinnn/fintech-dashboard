import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="핀테크 마케팅 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .block-container { padding-top: 1.5rem; }
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem; color: #718096; }
    .insight-box {
        background: #1a1f35; border: 1px solid #2d3748; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 12px;
    }
    .insight-title { font-weight: 700; font-size: 15px; margin-bottom: 6px; }
    .stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

EXCEL_PATH = "fintech_data.xlsx"
COLORS = {
    "구글": "#4285f4", "네이버검색": "#03c75a", "페이스북": "#1877f2",
    "영상": "#667eea", "이미지": "#fc8181", "브랜드키워드": "#f6e05e", "일반키워드": "#68d391",
    "논타겟": "#9f7aea", "리타겟": "#4fd1c5",
    "회원가입": "#667eea", "계좌개설": "#ed8936"
}

@st.cache_data(show_spinner="데이터 로딩 중...")
def load_data():
    df = pd.read_excel(EXCEL_PATH)
    if df["date"].dtype == object or str(df["date"].dtype).startswith("int") or str(df["date"].dtype).startswith("float"):
        df["date"] = pd.to_datetime(df["date"].apply(
            lambda x: pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(x)) if pd.notna(x) else pd.NaT
        ))
    else:
        df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["CTR"] = df["광고클릭"] / df["광고노출"].replace(0, pd.NA) * 100
    df["CPA"] = df["광고비"] / (df["회원가입"] + df["계좌개설"]).replace(0, pd.NA)
    return df

df = load_data()

st.markdown("""
<div style="margin-bottom:4px">
    <div style="font-size:20px;font-weight:800;color:#e2e8f0;margin-bottom:6px">핀테크 마케팅 데이터 대시보드</div>
    <div style="font-size:13px;color:#718096">
        데이터 기반 의사결정을 위한 마케팅 데이터 시각화 &nbsp;|&nbsp; 기말고사 과제 &nbsp;|&nbsp; 총 {:,}건 데이터 &nbsp;|&nbsp; <span style="color:#a0aec0;font-weight:600">박희진 U2025071</span>
    </div>
</div>
""".format(len(df)), unsafe_allow_html=True)
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 개요", "📡 채널 분석", "🔽 퍼널 & 전환", "🎨 크리에이티브", "💡 10대 인사이트"])

with tab1:
    total_imp = df["광고노출"].sum()
    total_clk = df["광고클릭"].sum()
    total_spd = df["광고비"].sum()
    total_sgn = df["회원가입"].sum()
    total_acc = df["계좌개설"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 광고 노출", f"{total_imp/1e8:.1f}억", "3채널 합산")
    c2.metric("총 광고 클릭", f"{total_clk/1e4:.0f}만", f"CTR {total_clk/total_imp*100:.2f}%")
    c3.metric("총 광고비", f"{total_spd/1e8:.1f}억원", "2025년 연간")
    c4.metric("가입+계좌개설", f"{(total_sgn+total_acc)/1e4:.0f}만건", f"구글 CPA 최저")

    st.markdown("#### 월별 광고비 & 전환 트렌드")
    monthly = df.groupby("year_month").agg(
        광고비=("광고비", "sum"),
        회원가입=("회원가입", "sum"),
        계좌개설=("계좌개설", "sum")
    ).reset_index()
    monthly["전환합계"] = monthly["회원가입"] + monthly["계좌개설"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=monthly["year_month"], y=monthly["광고비"]/1e8,
        name="광고비(억)", marker_color="#667eea", opacity=0.8), secondary_y=False)
    fig.add_trace(go.Scatter(x=monthly["year_month"], y=monthly["전환합계"]/1e4,
        name="전환합계(만)", line=dict(color="#68d391", width=2.5),
        mode="lines+markers", marker=dict(size=7)), secondary_y=True)
    fig.update_layout(
        height=380, plot_bgcolor="#1a1f35", paper_bgcolor="#0f1117",
        font=dict(color="#a0aec0"), legend=dict(orientation="h", y=1.1),
        xaxis=dict(gridcolor="#2d3748"),
        yaxis=dict(gridcolor="#2d3748", title="광고비 (억원)"),
    )
    fig.update_yaxes(title_text="전환합계 (만건)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 채널별 광고비 비중")
        ch_spend = df.groupby("channel")["광고비"].sum().reset_index()
        fig2 = px.pie(ch_spend, values="광고비", names="channel",
            color="channel", color_discrete_map=COLORS, hole=0.45)
        fig2.update_layout(height=300, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
            font=dict(color="#a0aec0"), showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)
    with col_b:
        st.markdown("#### 채널별 CPA 비교")
        ch_cpa = df.groupby("channel").apply(
            lambda x: x["광고비"].sum() / (x["회원가입"].sum() + x["계좌개설"].sum())
        ).reset_index(name="CPA").sort_values("CPA")
        fig3 = px.bar(ch_cpa, x="CPA", y="channel", orientation="h",
            color="channel", color_discrete_map=COLORS, text="CPA")
        fig3.update_traces(texttemplate="%{text:,.0f}원", textposition="outside")
        fig3.update_layout(height=300, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
            font=dict(color="#a0aec0"), showlegend=False,
            xaxis=dict(gridcolor="#2d3748"), yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.markdown("#### 채널별 상세 성과 비교")

    ch = df.groupby("channel").agg(
        노출=("광고노출","sum"), 클릭=("광고클릭","sum"),
        광고비=("광고비","sum"), 회원가입=("회원가입","sum"), 계좌개설=("계좌개설","sum")
    ).reset_index()
    ch["CTR(%)"] = (ch["클릭"]/ch["노출"]*100).round(2)
    ch["CPA(원)"] = (ch["광고비"]/(ch["회원가입"]+ch["계좌개설"])).round(0).astype(int)
    ch["노출(억)"] = (ch["노출"]/1e8).round(1)
    ch["광고비(억)"] = (ch["광고비"]/1e8).round(1)
    ch["가입(만)"] = (ch["회원가입"]/1e4).round(0).astype(int)
    ch["계좌(만)"] = (ch["계좌개설"]/1e4).round(0).astype(int)

    st.dataframe(
        ch[["channel","노출(억)","CTR(%)","광고비(억)","가입(만)","계좌(만)","CPA(원)"]].rename(columns={"channel":"채널"}),
        use_container_width=True, hide_index=True
    )

    c1, c2, c3 = st.columns(3)
    _chart_layout = dict(
        height=300, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
        font=dict(color="#a0aec0"), showlegend=False,
        xaxis=dict(gridcolor="rgba(0,0,0,0)", title=""),
        yaxis=dict(gridcolor="#2d3748"),
        margin=dict(t=30, b=10, l=10, r=10)
    )
    with c1:
        st.markdown("#### 채널별 CTR (%)")
        fig4 = px.bar(ch.sort_values("CTR(%)"), x="channel", y="CTR(%)",
            color="channel", color_discrete_map=COLORS, text="CTR(%)")
        fig4.update_traces(texttemplate="%{text:.2f}%", textposition="outside",
            textfont=dict(color="#e2e8f0"))
        fig4.update_layout(**_chart_layout)
        st.plotly_chart(fig4, use_container_width=True)
    with c2:
        st.markdown("#### 채널별 노출 (억)")
        fig5a = px.bar(ch, x="channel", y=ch["노출"]/1e8,
            color="channel", color_discrete_map=COLORS,
            text=ch["노출"].apply(lambda v: f"{v/1e8:.1f}억"))
        fig5a.update_traces(textposition="outside", textfont=dict(color="#e2e8f0"))
        fig5a.update_layout(**_chart_layout)
        st.plotly_chart(fig5a, use_container_width=True)
    with c3:
        st.markdown("#### 채널별 클릭 (만)")
        fig5b = px.bar(ch, x="channel", y=ch["클릭"]/1e4,
            color="channel", color_discrete_map=COLORS,
            text=ch["클릭"].apply(lambda v: f"{v/1e4:.0f}만"))
        fig5b.update_traces(textposition="outside", textfont=dict(color="#e2e8f0"))
        fig5b.update_layout(**_chart_layout)
        st.plotly_chart(fig5b, use_container_width=True)

    st.markdown("#### 채널별 월간 광고비 추이")
    monthly_ch = df.groupby(["year_month","channel"])["광고비"].sum().reset_index()
    fig6 = px.line(monthly_ch, x="year_month", y="광고비", color="channel",
        color_discrete_map=COLORS, markers=True)
    fig6.update_layout(height=350, plot_bgcolor="#1a1f35", paper_bgcolor="#0f1117",
        font=dict(color="#a0aec0"), xaxis=dict(gridcolor="#2d3748"),
        yaxis=dict(gridcolor="#2d3748", title="광고비 (원)"),
        legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig6, use_container_width=True)

with tab3:
    st.markdown("#### 마케팅 퍼널 전환율 분석")

    total_imp  = df["광고노출"].sum()
    total_clk  = df["광고클릭"].sum()
    total_ins  = df["앱설치"].sum()
    total_lnc  = df["앱실행"].sum()
    total_sgn  = df["회원가입"].sum()
    total_acc  = df["계좌개설"].sum()
    total_ftx  = df["첫거래"].sum()
    total_rep  = df["반복사용"].sum()
    total_apt  = df["자동이체설정"].sum()
    total_ref  = df["추천완료"].sum()

    funnel_df = pd.DataFrame({
        "단계": ["광고노출","광고클릭","앱설치","앱실행","회원가입","계좌개설","첫거래","반복사용","자동이체설정","추천완료"],
        "수치": [total_imp, total_clk, total_ins, total_lnc, total_sgn, total_acc, total_ftx, total_rep, total_apt, total_ref]
    })
    funnel_df["전환율"] = (funnel_df["수치"] / funnel_df["수치"].shift(1) * 100).round(1)
    funnel_df.loc[0, "전환율"] = 100.0

    bar_colors = ["#667eea","#7c6fe0","#9f7aea","#b794f4",
                  "#68d391","#4fd1c5","#f6e05e","#ed8936","#fc8181","#f687b3"]
    funnel_df["전환율표시"] = funnel_df["전환율"].apply(lambda x: "100%" if x==100 else f"▼{x:.1f}%")
    funnel_df["inside_label"] = funnel_df.apply(
        lambda r: f"{r['수치']/1e4:.0f}만건  {r['전환율표시']}", axis=1)

    fig7 = go.Figure(go.Bar(
        x=funnel_df["수치"],
        y=funnel_df["단계"],
        orientation="h",
        text=funnel_df["inside_label"],
        textposition="inside",
        insidetextanchor="start",
        textfont=dict(size=12, color="#ffffff"),
        marker=dict(color=bar_colors),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f}건<extra></extra>",
    ))
    fig7.update_layout(
        height=480, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
        font=dict(color="#e2e8f0", size=12),
        xaxis=dict(type="log", title="건수 (로그 스케일)", gridcolor="#2d3748"),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)",
                   tickfont=dict(size=12), automargin=True),
        margin=dict(l=10, r=20, t=20, b=40)
    )
    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("#### 단계별 전환율 테이블")
    display_df = funnel_df.copy()
    display_df["수치(만)"] = (display_df["수치"]/1e4).round(1)
    display_df["전환율(%)"] = display_df["전환율"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    st.dataframe(display_df[["단계","수치(만)","전환율(%)"]].rename(columns={"수치(만)":"수치(만건)"}),
        use_container_width=True, hide_index=True)

    st.markdown("#### 리타겟 vs 논타겟")
    ag = df.groupby("ad_group").agg(광고비=("광고비","sum"), 클릭=("광고클릭","sum"), 노출=("광고노출","sum")).reset_index()
    ag["CTR(%)"] = (ag["클릭"]/ag["노출"]*100).round(2)
    fig8 = px.bar(ag, x="ad_group", y="CTR(%)", color="ad_group",
        color_discrete_map={"논타겟":COLORS["논타겟"],"리타겟":COLORS["리타겟"]}, text="CTR(%)")
    fig8.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig8.update_layout(height=300, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
        font=dict(color="#a0aec0"), showlegend=False, xaxis_title="", yaxis_title="CTR (%)")
    st.plotly_chart(fig8, use_container_width=True)

with tab4:
    st.markdown("#### 크리에이티브 포맷별 성과")

    fmt = df.groupby("creative_format").agg(
        노출=("광고노출","sum"), 클릭=("광고클릭","sum"), 광고비=("광고비","sum")
    ).reset_index()
    fmt["CTR(%)"] = (fmt["클릭"]/fmt["노출"]*100).round(2)
    fmt["CPC(원)"] = (fmt["광고비"]/fmt["클릭"]).round(0).astype(int)

    c1, c2, c3, c4 = st.columns(4)
    for col, row in zip([c1,c2,c3,c4], fmt.sort_values("CTR(%)", ascending=False).itertuples()):
        col.metric(row.creative_format, f"{row._5:.2f}%", f"CTR | 광고비 {row.광고비/1e8:.1f}억")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 포맷별 CTR 비교")
        fig9 = px.bar(fmt.sort_values("CTR(%)"), x="creative_format", y="CTR(%)",
            color="creative_format", color_discrete_map=COLORS, text="CTR(%)")
        fig9.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig9.update_layout(height=320, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
            font=dict(color="#a0aec0"), showlegend=False, xaxis_title="", yaxis=dict(gridcolor="#2d3748"))
        st.plotly_chart(fig9, use_container_width=True)
    with col_b:
        st.markdown("#### 포맷별 광고비 vs 노출 버블")
        # 텍스트 위치를 포맷별로 개별 지정
        text_positions = {"브랜드키워드": "top right", "일반키워드": "bottom right",
                          "영상": "top left", "이미지": "bottom left"}
        fig10 = go.Figure()
        for _, row in fmt.iterrows():
            fmt_name = row["creative_format"]
            fig10.add_trace(go.Scatter(
                x=[row["노출"]], y=[row["CTR(%)"]],
                mode="markers+text",
                name=fmt_name,
                text=[fmt_name],
                textposition=text_positions.get(fmt_name, "top center"),
                textfont=dict(size=13, color="#ffffff"),
                marker=dict(
                    size=max(row["광고비"] / 3e9 * 80, 20),
                    color=COLORS.get(fmt_name, "#888"),
                    opacity=0.85,
                    line=dict(width=1, color="rgba(255,255,255,0.25)")
                ),
                hovertemplate=f"<b>{fmt_name}</b><br>노출: %{{x:,.0f}}<br>CTR: %{{y:.2f}}%<extra></extra>"
            ))
        fig10.update_layout(height=380, plot_bgcolor="#1a1f35", paper_bgcolor="#1a1f35",
            font=dict(color="#e2e8f0"), showlegend=False,
            xaxis=dict(gridcolor="#2d3748", title="노출수"),
            yaxis=dict(gridcolor="#2d3748", title="CTR (%)", range=[-1, 17]),
            margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig10, use_container_width=True)

    st.markdown("#### 캠페인 목표별 비교")
    obj = df.groupby("campaign_objective").agg(
        광고비=("광고비","sum"), 클릭=("광고클릭","sum"), 노출=("광고노출","sum"),
        회원가입=("회원가입","sum"), 계좌개설=("계좌개설","sum")
    ).reset_index()
    obj["CTR(%)"] = (obj["클릭"]/obj["노출"]*100).round(2)
    obj["전환합계"] = obj["회원가입"] + obj["계좌개설"]
    obj["CPA(원)"] = (obj["광고비"]/obj["전환합계"]).round(0).astype(int)

    fig11 = make_subplots(rows=1, cols=2, subplot_titles=("광고비 (억원)","CPA (원/건)"))
    for i, row in enumerate(obj.itertuples()):
        color = COLORS.get(row.campaign_objective, "#888")
        fig11.add_trace(go.Bar(name=row.campaign_objective, x=[row.campaign_objective],
            y=[row.광고비/1e8], marker_color=color, showlegend=False), row=1, col=1)
        fig11.add_trace(go.Bar(name=row.campaign_objective, x=[row.campaign_objective],
            y=[row._9], marker_color=color, showlegend=True), row=1, col=2)
    fig11.update_layout(height=300, plot_bgcolor="#1a1f35", paper_bgcolor="#0f1117",
        font=dict(color="#a0aec0"),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"))
    fig11.update_xaxes(showticklabels=False)
    st.plotly_chart(fig11, use_container_width=True)

with tab5:
    st.markdown("### 💡 핀테크 데이터에서 발견한 10가지 인사이트")
    st.caption("실제 109,500건 데이터 분석 기반 마케팅 인사이트")
    st.divider()

    insights = [
        ("1", "구글이 CPA 최저 — 예산 재배분 기회", "#4285f4",
         "구글 CPA 507원은 네이버검색(1,849원) 대비 3.6배 저렴. 현재 구글 예산 비중은 25%에 불과하나 CPA 기준 최고 효율 채널. 구글 예산 확대 시 전환당 비용 약 40% 절감 가능."),
        ("2", "검색 의도 고객의 전환력 — CTR 17배 차이", "#03c75a",
         "브랜드키워드 CTR 13.25%는 이미지(0.78%) 대비 17배 높음. 검색 의도를 가진 고객이 발견 채널 대비 클릭 가능성이 압도적으로 높아 검색 광고 증설이 ROI 향상의 핵심."),
        ("3", "리타겟이 논타겟보다 효율적 — 그러나 과투자 중", "#9f7aea",
         "리타겟 CTR 1.17% vs 논타겟 0.89% (31% 높음). 그러나 리타겟 광고비(150.9억)가 논타겟(117.5억)보다 28% 더 많이 집행. 모수 한계를 고려한 적정 비중 재검토 필요."),
        ("4", "페이스북 규모의 역설 — 최다 지출·중간 효율", "#1877f2",
         "페이스북이 총 광고비의 42%(112.7억)를 차지하나 CPA는 807원으로 중간. 클릭수(2,059만)는 최다이나 효율은 구글(507원)에 뒤처짐. 전환 품질 지표 추가 모니터링 필요."),
        ("5", "퍼널 최대 누수 — 클릭→설치(56%)가 핵심 게이트", "#f6e05e",
         "클릭 4,624만 중 설치 2,595만(56.1%)으로 절반만 설치. 설치 이후는 실행 90% → 가입 77% → 계좌 77%로 비교적 양호. 랜딩페이지 최적화와 앱스토어 페이지 개선이 최우선 과제."),
        ("6", "영상 광고 최다 지출·적정 CTR — 검색 대비 9배 비효율", "#667eea",
         "영상 광고비 96.3억(36% 최다)이나 CTR은 0.95%로 브랜드키워드(13.25%)의 1/14 수준. 영상 예산 일부를 검색 광고로 이동 시 동일 예산으로 전환 대폭 향상 예상."),
        ("7", "9월·12월 성수기, 7월 비수기 뚜렷", "#68d391",
         "9월 광고비 30.6억·전환 183만건(연간 최고), 12월 31.7억·175만건으로 성수기 확인. 7월 15.8억·127만건으로 비수기 최저. 성수기 예산 증액 + 비수기 크리에이티브 리프레시 전략 권장."),
        ("8", "네이버검색 고비용이지만 퍼널 품질 우수", "#03c75a",
         "네이버 CPA 1,849원으로 최고가이나 CTR 11.09%로 최고. 검색 의도 고객 유입으로 가입 후 계좌개설→첫거래 전환율이 높을 가능성. 단순 CPA가 아닌 LTV 기준 재평가 필요."),
        ("9", "자동이체설정 전환율 21.9% — 딥퍼널 개선 기회", "#ed8936",
         "반복사용 고객 중 자동이체 설정 비율 21.9%로 가장 낮은 병목. 자동이체 설정 고객은 이탈률↓ ARPU↑인 고LTV 세그먼트. 인앱 넛지, 혜택 제공 등으로 30%까지 개선 목표 설정 가능."),
        ("10", "회원가입·계좌개설 예산 균등 — 계좌개설 확대 여지", "#f687b3",
         "회원가입(133.6억) vs 계좌개설(134.9억)이 거의 50:50 배분. 계좌개설이 더 높은 LTV로 이어지므로 계좌개설 캠페인 비중을 60:40으로 확대 시 장기 수익성 향상 예상.")
    ]

    for i in range(0, 10, 2):
        col1, col2 = st.columns(2)
        for col, (num, title, color, body) in zip([col1, col2], insights[i:i+2]):
            with col:
                st.markdown(f"""
                <div style="background:#1a1f35;border:1px solid #2d3748;border-left:4px solid {color};
                    border-radius:10px;padding:16px 20px;margin-bottom:12px">
                    <div style="color:{color};font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">INSIGHT #{num}</div>
                    <div style="font-size:15px;font-weight:700;color:#e2e8f0;margin-bottom:8px">{title}</div>
                    <div style="font-size:13px;color:#a0aec0;line-height:1.7">{body}</div>
                </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 채널별 인사이트 요약 시각화")
    summary = pd.DataFrame({
        "채널": ["구글", "네이버검색", "페이스북"],
        "CPA(원)": [507, 1849, 807],
        "CTR(%)": [0.63, 11.09, 1.26],
        "광고비(억)": [67.0, 88.8, 112.7]
    })
    fig12 = px.scatter(summary, x="CPA(원)", y="CTR(%)", size="광고비(억)",
        color="채널", color_discrete_map=COLORS, text="채널",
        title="채널 포지셔닝 맵 (X=CPA↓낮을수록 효율적, Y=CTR↑높을수록 좋음, 버블=광고비)",
        size_max=60)
    fig12.update_traces(
        textposition="middle center",
        textfont=dict(size=14, color="#ffffff"),
        marker=dict(opacity=0.85)
    )
    fig12.update_layout(height=500, plot_bgcolor="#1a1f35", paper_bgcolor="#0f1117",
        font=dict(color="#e2e8f0", size=13), title_font=dict(color="#e2e8f0", size=14),
        xaxis=dict(gridcolor="#2d3748", range=[300, 2100]),
        yaxis=dict(gridcolor="#2d3748", range=[-1, 16]),
        legend=dict(font=dict(size=13)))
    st.plotly_chart(fig12, use_container_width=True)
