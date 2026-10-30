import streamlit as st
import random
import datetime
from ssq_core import (
    fetch_lottery_data, load_cache,
    analyze_frequency, analyze_missing, analyze_hot_cold,
    generate_prediction, generate_wheel, generate_rollover_numbers,
    calc_next_issue, calc_next_draw_date,
)

st.set_page_config(
    page_title="🎊 福运双色球 · 必中大奖 🎊",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        background: linear-gradient(180deg, #8B0000 0%, #C1272D 50%, #8B0000 100%) !important;
        color: #FFF8E7 !important;
        font-family: "STKaiti", "KaiTi", "楷体", serif !important;
    }
    .stApp { background: linear-gradient(180deg, #8B0000 0%, #C1272D 50%, #8B0000 100%) !important; }
    h1, h2, h3, h4, h5, h6 { color: #FFD700 !important; font-family: "STKaiti","KaiTi","楷体",serif !important; text-shadow: 0 2px 6px rgba(0,0,0,0.5) !important; }
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%) !important;
        color: #8B0000 !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        border: 2px solid #FFE4B5 !important;
        box-shadow: 0 4px 15px rgba(255,215,0,0.4) !important;
        transition: all 0.3s !important;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,215,0,0.6) !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(139,0,0,0.6) !important;
        color: #FFD700 !important;
        border-radius: 10px 10px 0 0 !important;
        font-size: 16px !important;
        padding: 10px 16px !important;
        border: 1px solid #FFD700 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FFD700 0%, #DAA520 100%) !important;
        color: #8B0000 !important;
        font-weight: bold !important;
    }
    .ball-red {
        display: inline-flex; align-items: center; justify-content: center;
        width: 42px; height: 42px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #FF6B6B, #C1272D 60%, #8B0000);
        color: white; font-weight: bold; font-size: 17px;
        margin: 3px; box-shadow: 0 3px 8px rgba(0,0,0,0.5), inset 0 -3px 6px rgba(0,0,0,0.3);
        text-shadow: 0 1px 2px rgba(0,0,0,0.6);
    }
    .ball-blue {
        display: inline-flex; align-items: center; justify-content: center;
        width: 42px; height: 42px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #5A9BFF, #1E5AA8 60%, #0A2E6B);
        color: white; font-weight: bold; font-size: 17px;
        margin: 3px; box-shadow: 0 3px 8px rgba(0,0,0,0.5), inset 0 -3px 6px rgba(0,0,0,0.3);
        text-shadow: 0 1px 2px rgba(0,0,0,0.6);
    }
    .row-card {
        background: rgba(255,248,231,0.1) !important;
        border: 1px solid #FFD700 !important;
        border-radius: 15px !important;
        padding: 10px 15px !important;
        margin: 8px 0 !important;
        backdrop-filter: blur(5px) !important;
    }
    .issue-badge {
        display: inline-block; background: linear-gradient(135deg,#FFD700,#DAA520);
        color: #8B0000; font-weight: bold; border-radius: 20px;
        padding: 4px 14px; margin-right: 10px;
    }
    .copy-btn {
        display: inline-block; background: linear-gradient(135deg,#FFD700,#DAA520);
        color: #8B0000; font-weight: bold; border-radius: 8px;
        padding: 4px 12px; cursor: pointer; border: 1px solid #FFE4B5;
        font-size: 13px; text-decoration: none; margin-left: 8px;
    }
    .strategy-tag {
        color: #FFD700; font-size: 14px; font-weight: bold; margin-right: 8px;
    }
    .footer-tip {
        text-align: center; color: #FFD700; font-size: 14px;
        padding: 20px 10px; opacity: 0.9;
    }
    .title-main {
        text-align: center; padding: 15px 10px;
    }
    .title-main h1 {
        font-size: clamp(22px, 6vw, 42px) !important;
    }
    .title-sub {
        text-align: center; color: #FFE4B5; font-size: 14px; margin-bottom: 15px;
    }
    @media (max-width: 600px) {
        .ball-red, .ball-blue { width: 34px; height: 34px; font-size: 14px; margin: 2px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
<div class="title-main">
    <h1>🏆 福运双色球 · 必中大奖 🏆</h1>
</div>
<div class="title-sub">
    🎉 恭喜发财 · 好运连连 · 心想事成 🎉
</div>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch(count):
    data = fetch_lottery_data(count)
    return data


def render_red_balls(red_list):
    balls = "".join(f'<span class="ball-red">{n:02d}</span>' for n in red_list)
    return balls


def render_blue_ball(blue_num):
    return f'<span class="ball-blue">{blue_num:02d}</span>'


def render_row(red_list, blue_num, prefix="", suffix_html=""):
    return f'{prefix}{render_red_balls(red_list)} <span style="color:#FFD700;font-size:20px;margin:0 5px;">+</span> {render_blue_ball(blue_num)}{suffix_html}'


st.markdown('<div class="row-card">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])
with col1:
    load_btn = st.button("🔄 加载开奖数据", use_container_width=True)
with col2:
    count = st.slider("往期期数", 20, 100, 50, 10)
st.markdown('</div>', unsafe_allow_html=True)

if load_btn or "lottery_data" not in st.session_state:
    with st.spinner("🎲 正在从福彩官网抓取数据..."):
        data = cached_fetch(count)
        if not data:
            data = load_cache()
            st.warning("⚠️ 网络请求失败，已加载本地缓存数据")
        st.session_state.lottery_data = data

data = st.session_state.get("lottery_data", [])

if data:
    tabs = st.tabs(["📜 往期开奖", "🎯 本期预测", "💎 必中大奖", "📊 统计分析"])

    with tabs[0]:
        st.markdown("### 📜 往期开奖号码")
        st.markdown("---")
        for item in data:
            st.markdown(
                f"""
                <div class="row-card">
                    <span class="issue-badge">第 {item['issue']} 期</span>
                    <span style="color:#FFE4B5;margin-right:15px;">📅 {item['date']}</span>
                    {render_row(item['red'], item['blue'])}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tabs[1]:
        st.markdown("### 🎯 本期精准预测 (5组)")
        st.markdown("---")
        next_issue = calc_next_issue(data[0]["issue"]) if data else ""
        next_date = calc_next_draw_date(data[0]["date"]) if data else ""
        st.markdown(
            f'<div style="text-align:center;color:#FFD700;font-size:16px;">'
            f'📅 第 <span style="font-weight:bold;font-size:20px;">{next_issue}</span> 期　开奖时间：{next_date}</div>',
            unsafe_allow_html=True,
        )

        if st.button("🎲 生成本期预测号码", use_container_width=True, key="gen_predict"):
            preds = generate_prediction(data, 5)
            st.session_state.predictions = preds

        preds = st.session_state.get("predictions", [])
        for idx, p in enumerate(preds):
            combo_str = " ".join(f"{n:02d}" for n in p["red"]) + f" + {p['blue']:02d}"
            st.markdown(
                f"""
                <div class="row-card">
                    <span class="issue-badge">第 {idx + 1} 组</span>
                    {render_row(p['red'], p['blue'], suffix_html=st.session_state.get(f'cp_{idx}', ''))}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.code(combo_str, language="text")

    with tabs[2]:
        st.markdown("### 💎 必中大奖 · 钻石矩阵 (10组)")
        st.markdown("---")
        next_issue = calc_next_issue(data[0]["issue"]) if data else ""
        st.markdown(
            f'<div style="text-align:center;color:#FFD700;font-size:16px;">'
            f'🏆 第 <span style="font-weight:bold;font-size:20px;">{next_issue}</span> 期 · 10大策略全覆盖</div>',
            unsafe_allow_html=True,
        )

        if st.button("🎊 一键生成必中大奖号码", use_container_width=True, key="gen_jackpot"):
            wheel_results, top_red, top_blue = generate_wheel(data, 10)
            st.session_state.wheel_results = wheel_results
            st.session_state.top_red = top_red
            st.session_state.top_blue = top_blue

        wheel_results = st.session_state.get("wheel_results", [])
        if wheel_results:
            for idx, w in enumerate(wheel_results):
                combo_str = " ".join(f"{n:02d}" for n in w["red"]) + f" + {w['blue']:02d}"
                st.markdown(
                    f"""
                    <div class="row-card">
                        <span class="issue-badge">#{idx + 1}</span>
                        <span class="strategy-tag">{w['strategy']}</span><br><br>
                        {render_row(w['red'], w['blue'])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.code(combo_str, language="text")

            if st.session_state.get("top_red"):
                with st.expander("🎁 热号池 Top 16 & 蓝号池 Top 8"):
                    st.markdown("**🔴 热号池 Top 16:**")
                    st.markdown(render_red_balls(st.session_state["top_red"]), unsafe_allow_html=True)
                    st.markdown("**🔵 蓝号池 Top 8:**")
                    st.markdown(
                        " ".join(f'<span class="ball-blue">{n:02d}</span>' for n in st.session_state["top_blue"]),
                        unsafe_allow_html=True,
                    )

    with tabs[3]:
        st.markdown("### 📊 统计分析")
        red_freq, blue_freq = analyze_frequency(data)
        red_missing, blue_missing = analyze_missing(data)
        hot_red, cold_red, hot_blue, cold_blue = analyze_hot_cold(red_freq, blue_freq, 10)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 🔥 热门红球 TOP 10")
            st.markdown(render_red_balls(hot_red), unsafe_allow_html=True)
        with col_b:
            st.markdown("#### ❄️ 冷门红球 TOP 10")
            st.markdown(render_red_balls(cold_red), unsafe_allow_html=True)

        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("#### 🔵 热门蓝球 TOP 5")
            st.markdown(" ".join(f'<span class="ball-blue">{n:02d}</span>' for n in hot_blue), unsafe_allow_html=True)
        with col_d:
            st.markdown("#### 🥶 冷门蓝球 TOP 5")
            st.markdown(" ".join(f'<span class="ball-blue">{n:02d}</span>' for n in cold_blue), unsafe_allow_html=True)

        st.markdown("#### 📈 全部红球出现频次")
        freq_sorted = sorted(red_freq.items(), key=lambda x: x[1], reverse=True)
        chart_data = {n: f for n, f in freq_sorted}
        st.bar_chart(chart_data, height=300, use_container_width=True)

        st.markdown("#### 📈 全部蓝球出现频次")
        blue_sorted = sorted(blue_freq.items(), key=lambda x: x[1], reverse=True)
        st.bar_chart({n: f for n, f in blue_sorted}, height=250, use_container_width=True)

else:
    st.info("👆 点击上方「🔄 加载开奖数据」按钮开始")

st.markdown("---")
st.markdown(
    '<div class="footer-tip">🎊 数据仅供娱乐参考，请理性购彩 · 祝君好运 🎊</div>',
    unsafe_allow_html=True,
)
