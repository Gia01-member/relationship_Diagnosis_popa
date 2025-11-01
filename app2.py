# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="POPA拡張診断", page_icon="🧭", layout="centered")

DATA_DIR = Path(__file__).parent  # リポジトリ直下を基準に

@st.cache_data
def load_data():
    pillars_path = DATA_DIR / "pillars.csv"
    questions_path = DATA_DIR / "questions.csv"
    try:
        # エンコーディング差異や全角クォート対策
        pillars = pd.read_csv(pillars_path, encoding="utf-8", engine="python")
        qs = pd.read_csv(questions_path, encoding="utf-8", engine="python")
    except Exception as e:
        st.error("データ読込エラーです。ファイル配置・文字コードをご確認ください。")
        st.code(f"{type(e).__name__}: {e}")
        st.write("カレントディレクトリ:", str(DATA_DIR))
        st.write("存在ファイル一覧:", [p.name for p in DATA_DIR.glob('*')])
        raise
    # 想定列の最終チェック
    assert {"key","label","root_need","relation_tendency","dependency","risk","merit","actions","reward"}.issubset(pillars.columns)
    assert {"dim","text"}.issubset(qs.columns)
    return pillars, qs

def compute_scores(df_ans: pd.DataFrame):
    agg = df_ans.groupby("dim")["score"].mean().reindex(
        ["outcome","relation","process","value"]
    ).fillna(0.0)
    norm = (agg - 1.0) / 4.0 * 100.0  # 1-5 → 0-100%
    return agg, norm

def radar(norm: pd.Series):
    labels = ["Outcome","Relation","Process","Value"]
    vals = [norm.get("outcome",0), norm.get("relation",0),
            norm.get("process",0), norm.get("value",0)]
    labels_c = labels + [labels[0]]
    vals_c = vals + [vals[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals_c, theta=labels_c, fill='toself'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        showlegend=False, margin=dict(l=20,r=20,t=20,b=20), height=450
    )
    return fig

pillars, qs = load_data()

st.title("🧭 POPA拡張診断｜Outcome / Relation / Process / Value")
st.markdown("20問に1〜5で回答し、**Outcome / Relation / Process / Value**の4タイプを可視化します。")

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

    result = pd.DataFrame({
        "dimension": ["Outcome","Relation","Process","Value"],
        "score_mean": [agg.loc['outcome'], agg.loc['relation'], agg.loc['process'], agg.loc['value']],
        "score_percent": [norm.loc['outcome'], norm.loc['relation'], norm.loc['process'], norm.loc['value']]
    })
    st.subheader("タイプ別スコア")
    st.dataframe(result, use_container_width=True)

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

    st.download_button(
        "📥 結果CSVをダウンロード",
        data=result.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"popa_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

with st.expander("🗂 履歴（この端末のみ／セッション保存）"):
    hist = st.session_state.get("history", [])
    if hist:
        st.dataframe(pd.DataFrame(hist))
    else:
        st.write("まだ履歴はありません。")
