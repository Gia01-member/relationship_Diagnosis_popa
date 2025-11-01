# app.py
# POPA拡張診断（Outcome / Relation / Process / Value）
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="POPA拡張診断", page_icon="🧭", layout="centered")

@st.cache_data
def load_data():
    pillars = pd.read_csv("pillars.csv")
    qs = pd.read_csv("questions.csv")
    return pillars, qs

def compute_scores(df_ans: pd.DataFrame):
    # 各次元の平均 → 1-5 を 0-100% に正規化
    agg = df_ans.groupby("dim")["score"].mean().reindex(
        ["outcome","relation","process","value"]
    ).fillna(0.0)
    norm = (agg - 1.0) / 4.0 * 100.0
    return agg, norm

def radar(norm: pd.Series):
    labels = ["Outcome","Relation","Process","Value"]
    vals = [norm.get("outcome",0), norm.get("relation",0),
            norm.get("process",0), norm.get("value",0)]
    labels_c = labels + [labels[0]]
    vals_c = vals + [vals[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals_c, theta=labels_c, fill='toself', name='Score(%)'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        showlegend=False, margin=dict(l=20,r=20,t=20,b=20), height=450
    )
    return fig

pillars, qs = load_data()

st.title("🧭 POPA拡張診断｜Outcome / Relation / Process / Value")
st.markdown(
    "この診断は、あなたの**報酬指向（何に安心・快感を見出すか）**を "
    "**Outcome（成果）／Relation（関係）／Process（設計）／Value（意味）** の4タイプで可視化します。"
)

with st.form("quiz"):
    answers = []
    for i, row in qs.iterrows():
        v = st.slider(f"Q{i+1}. {row['text']}", 1, 5, 3, key=f"q{i+1}")
        answers.append({"dim": row["dim"], "text": row["text"], "score": v})
    submitted = st.form_submit_button("🧭 診断する")

if submitted:
    df_ans = pd.DataFrame(answers)
    agg, norm = compute_scores(df_ans)
    st.success("診断が完了しました。下部のチャートとアドバイスをご確認ください。")
    st.plotly_chart(radar(norm), use_container_width=True)

    # スコア表
    result = pd.DataFrame({
        "dimension":["Outcome","Relation","Process","Value"],
        "score_mean":[agg.loc['outcome'], agg.loc['relation'], agg.loc['process'], agg.loc['value']],
        "score_percent":[norm.loc['outcome'], norm.loc['relation'], norm.loc['process'], norm.loc['value']]
    })
    st.subheader("タイプ別スコア")
    st.dataframe(result, use_container_width=True)

    # タイプ別アドバイス
    st.subheader("タイプ別の特徴とおすすめアクション")
    dom_key = norm.idxmax()
    st.write(f"主要指向：**{pillars.set_index('key').loc[dom_key,'label']}**")
    cols = st.columns(4)
    for i, key in enumerate(["outcome","relation","process","value"]):
        p = pillars.set_index('key').loc[key]
        with cols[i]:
            st.markdown(f"**{p['label']}**")
            st.caption(f"- 根本欲求：{p['root_need']}")
            st.caption(f"- 傾向：{p['relation_tendency']}")
            st.caption(f"- 依存：{p['dependency']}")
            st.caption(f"- リスク：{p['risk']}")
            st.caption(f"- メリット：{p['merit']}")
            st.write(f"**行動**：{p['actions']}")
            st.write(f"**報酬**：{p['reward']}")

    # CSVダウンロード
    st.download_button(
        "📥 結果CSVをダウンロード",
        data=result.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"popa_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

    # セッション履歴
    hist = st.session_state.get("history", [])
    hist.append({
        "timestamp": datetime.now().isoformat(),
        "outcome": float(norm.loc["outcome"]),
        "relation": float(norm.loc["relation"]),
        "process": float(norm.loc["process"]),
        "value": float(norm.loc["value"])
    })
    st.session_state["history"] = hist

with st.expander("🗂 履歴（この端末のみ／セッション保存）"):
    hist = st.session_state.get("history", [])
    if hist:
        st.dataframe(pd.DataFrame(hist))
    else:
        st.write("まだ履歴はありません。")

st.markdown("---")
st.caption("© 2025 POPA Extended — 教育・セルフリフレクション目的の簡易診断です。")
