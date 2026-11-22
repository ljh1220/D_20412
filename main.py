import os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="다이아몬드 가격 예측 및 회귀 분석 대시보드",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

plt.rcParams["axes.unicode_minus"] = False


# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 모델 학습 파이프라인 (캐싱 적용)
# -----------------------------------------------------------------------------
def resolve_file_path(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


@st.cache_resource
def load_and_train_models():
    train_path = resolve_file_path([
        "diamonds_train_split.csv",
        "diamonds_train.csv",
        "diamond_split_data/diamonds_train.csv",
        "data/diamonds_train_split.csv",
    ])
    test_path = resolve_file_path([
        "diamonds_test_only.csv",
        "diamonds_test_split.csv",
        "diamonds_test.csv",
        "diamond_split_data/diamonds_test.csv",
        "data/diamonds_test_only.csv",
    ])

    if train_path is None or test_path is None:
        return None

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    feature_cols = [c for c in train_df.columns if c != "log_price"]
    X_train, y_train = train_df[feature_cols], train_df["log_price"]
    X_test, y_test = test_df[feature_cols], test_df["log_price"]

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_train_pred_log = model.predict(X_train)
    y_test_pred_log = model.predict(X_test)

    train_resid_log = y_train - y_train_pred_log
    smearing_factor = float(np.mean(np.exp(train_resid_log)))

    y_test_dollar = np.exp(y_test)
    y_test_pred_dollar = np.exp(y_test_pred_log)
    y_test_pred_smear = y_test_pred_dollar * smearing_factor

    metrics = {
        "train_path": train_path,
        "test_path": test_path,
        "n_train": len(train_df),
        "n_test": len(test_df),
        "log_r2_train": r2_score(y_train, y_train_pred_log),
        "log_r2_test": r2_score(y_test, y_test_pred_log),
        "log_rmse_test": np.sqrt(mean_squared_error(y_test, y_test_pred_log)),
        "log_mae_test": mean_absolute_error(y_test, y_test_pred_log),
        "dollar_r2_test": r2_score(y_test_dollar, y_test_pred_dollar),
        "dollar_rmse_test": np.sqrt(mean_squared_error(y_test_dollar, y_test_pred_dollar)),
        "dollar_mae_test": mean_absolute_error(y_test_dollar, y_test_pred_dollar),
        "dollar_rmse_smear": np.sqrt(mean_squared_error(y_test_dollar, y_test_pred_smear)),
        "smearing_factor": smearing_factor,
        "intercept": float(model.intercept_),
    }

    coef_df = pd.DataFrame({
        "Feature": feature_cols,
        "Coefficient": model.coef_,
        "Pct_Impact (%)": (np.exp(model.coef_) - 1) * 100,
    })

    eval_df = pd.DataFrame({
        "carat": np.exp(X_test["log_carat"].values),
        "depth": X_test["depth"].values,
        "table": X_test["table"].values,
        "actual_log": y_test.values,
        "pred_log": y_test_pred_log,
        "resid_log": y_test.values - y_test_pred_log,
        "actual_dollar": y_test_dollar.values,
        "pred_dollar": y_test_pred_dollar,
        "resid_dollar": y_test_dollar.values - y_test_pred_dollar,
    })

    return {
        "model": model,
        "feature_cols": feature_cols,
        "metrics": metrics,
        "coef_df": coef_df,
        "eval_df": eval_df,
    }


def build_input_vector(carat, cut, color, clarity, depth, table, feature_cols):
    row = {col: 0.0 for col in feature_cols}
    row["depth"] = float(depth)
    row["table"] = float(table)
    row["log_carat"] = float(np.log(carat))

    if cut != "Fair" and f"cut_{cut}" in row:
        row[f"cut_{cut}"] = 1.0
    if color != "D" and f"color_{color}" in row:
        row[f"color_{color}"] = 1.0
    if clarity != "I1" and f"clarity_{clarity}" in row:
        row[f"clarity_{clarity}"] = 1.0

    return pd.DataFrame([row])[feature_cols]


# -----------------------------------------------------------------------------
# 3. 파이프라인 실행 및 예외 처리
# -----------------------------------------------------------------------------
bundle = load_and_train_models()

st.title("💎 다이아몬드 가격 예측 및 선형 회귀 분석 웹앱")
st.markdown(
    "데이터 정제, 로그 변환(`log_carat`, `log_price`), 원-핫 인코딩 및 **8:2 층화 분할**을 거쳐 학습된 "
    "다중 선형 회귀(OLS) 모델의 실시간 가격 예측 및 진단 결과를 제공합니다."
)

if bundle is None:
    st.error(
        "데이터 파일을 찾을 수 없습니다. GitHub 저장소 루트 경로에 "
        "`diamonds_train_split.csv`와 `diamonds_test_only.csv` 파일이 업로드되어 있는지 확인해 주세요."
    )
    st.stop()

model = bundle["model"]
feature_cols = bundle["feature_cols"]
metrics = bundle["metrics"]
coef_df = bundle["coef_df"]
eval_df = bundle["eval_df"]

# -----------------------------------------------------------------------------
# 4. 사이드바: 실시간 예측 입력 패널
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 다이아몬드 스펙 입력")
st.sidebar.caption("원하는 감정 등급과 치수 비율을 입력하면 즉시 달러($) 가격을 예측합니다.")

carat = st.sidebar.slider("캐럿 (Carat)", min_value=0.20, max_value=4.00, value=1.00, step=0.01)
cut = st.sidebar.selectbox(
    "커팅 등급 (Cut)",
    options=["Fair", "Good", "Very Good", "Premium", "Ideal"],
    index=4,
    help="Fair(최하) -> Ideal(최상)",
)
color = st.sidebar.selectbox(
    "색상 등급 (Color)",
    options=["D", "E", "F", "G", "H", "I", "J"],
    index=2,
    help="D(무색·최상) -> J(미세한 황색·하위)",
)
clarity = st.sidebar.selectbox(
    "투명도 등급 (Clarity)",
    options=["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"],
    index=4,
    help="I1(내포물 다수·최하) -> IF(내부 무결점·최상)",
)

with st.sidebar.expander("세부 비율 설정 (Depth / Table)", expanded=False):
    depth = st.slider("깊이 비율 (Depth %)", min_value=50.0, max_value=75.0, value=61.8, step=0.1)
    table = st.slider("테이블 비율 (Table %)", min_value=50.0, max_value=75.0, value=57.0, step=0.1)

st.sidebar.divider()
st.sidebar.markdown(f"**학습 데이터:** `{metrics['train_path']}` ({metrics['n_train']:,}행)")
st.sidebar.markdown(f"**평가 데이터:** `{metrics['test_path']}` ({metrics['n_test']:,}행)")

# -----------------------------------------------------------------------------
# 5. 메인 화면 탭 구성
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "💰 1. 실시간 가격 예측기",
    "📊 2. 모델 성능 및 회귀 계수 분석",
    "🩺 3. 잔차 진단 및 구간별 오차",
])

with tab1:
    input_X = build_input_vector(carat, cut, color, clarity, depth, table, feature_cols)
    pred_log = float(model.predict(input_X)[0])
    pred_dollar = float(np.exp(pred_log))
    pred_smear = pred_dollar * metrics["smearing_factor"]

    log_sigma = metrics["log_rmse_test"]
    ci_low = float(np.exp(pred_log - log_sigma))
    ci_high = float(np.exp(pred_log + log_sigma))

    st.subheader("예측 결과 요약")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("기본 예측 가격 (exp 역변환)", f"${pred_dollar:,.2f}")
    col2.metric("Duan 보정 예측가 (x1.0089)", f"${pred_smear:,.2f}")
    col3.metric("예상 시세 범위 (±1σ 구간)", f"${ci_low:,.0f} ~ ${ci_high:,.0f}")
    col4.metric("예측 로그 가격 (log_price)", f"{pred_log:.4f}")

    st.info(
        f"**입력 스펙:** `{carat:.2f} ct` | Cut: `{cut}` | Color: `{color}` | Clarity: `{clarity}` "
        f"| Depth: `{depth:.1f}%` | Table: `{table:.1f}%`"
    )

    tol = max(0.05, carat * 0.10)
    peer_df = eval_df[(eval_df["carat"] >= carat - tol) & (eval_df["carat"] <= carat + tol)]

    st.subheader(f"유사 캐럿 구간({carat - tol:.2f} ~ {carat + tol:.2f} ct) 시장 분포 내 위치")
    fig, ax = plt.subplots(figsize=(10, 4))
    if len(peer_df) > 10:
        sns.histplot(
            peer_df["actual_dollar"],
            bins=35,
            kde=True,
            color="#4c78a8",
            alpha=0.45,
            ax=ax,
            label="Test Set Actual Prices",
        )
        ax.axvline(pred_dollar, color="#e45756", linestyle="--", lw=2.2, label=f"Predicted Price (${pred_dollar:,.0f})")
        ax.axvline(
            peer_df["actual_dollar"].median(),
            color="#54a24b",
            linestyle=":",
            lw=1.8,
            label=f"Peer Median (${peer_df['actual_dollar'].median():,.0f})",
        )
        ax.set_xlabel("Price ($)")
        ax.set_ylabel("Count")
        ax.set_title(f"Price Distribution for {carat - tol:.2f} - {carat + tol:.2f} Carat Diamonds (n={len(peer_df):,})")
        ax.legend()
    else:
        ax.text(0.5, 0.5, "Not enough peer samples in this extreme carat range.", ha="center", va="center")
    st.pyplot(fig)
    plt.close(fig)

with tab2:
    st.subheader("모델 검증 지표 (8:2 층화 분할 테스트 셋 기준)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("로그 스케일 R²", f"{metrics['log_r2_test']:.5f}", delta=f"Train {metrics['log_r2_train']:.5f}")
    m2.metric("실제 달러 R²", f"{metrics['dollar_r2_test']:.5f}")
    m3.metric("달러 RMSE", f"${metrics['dollar_rmse_test']:,.2f}")
    m4.metric("달러 MAE", f"${metrics['dollar_mae_test']:,.2f}")

    st.markdown(
        """
        **핵심 설계 요약:**
        - **데이터 정제:** 원본 53,940행 → 완전 중복 146건 및 치수 오기입(`y>20` or `z>20`) 3건 제거 → **53,791행** 확보
        - **다중공선성 해소:** `carat`과 상관계수 0.95 이상인 `x, y, z` 치수 변수 제거 (VIF > 10,000 → 1.48로 안정화)
        - **로그 선형화:** `log(carat)`과 `log(price)` 변환으로 비선형 거듭제곱 관계를 선형화하고 음수 가격 예측 원천 차단
        """
    )

    col_left, col_right = st.columns([1.1, 1.2])

    with col_left:
        st.subheader("회귀 계수 및 기준 등급 대비 가격 변화율")
        st.caption(f"절편 (Intercept): `{metrics['intercept']:.5f}` | 기준 등급: `Cut=Fair`, `Color=D`, `Clarity=I1`")
        display_coef = coef_df.copy()
        display_coef["Coefficient"] = display_coef["Coefficient"].map(lambda x: f"{x:+.5f}")
        display_coef["Pct_Impact (%)"] = display_coef["Pct_Impact (%)"].map(lambda x: f"{x:+.2f}%")
        st.dataframe(display_coef, use_container_width=True, height=440)

    with col_right:
        st.subheader("테스트 셋 실제 가격 vs 예측 가격 ($)")
        fig2, ax2 = plt.subplots(figsize=(6.5, 5.2))
        ax2.scatter(eval_df["actual_dollar"], eval_df["pred_dollar"], alpha=0.18, s=8, color="#2b5c8f")
        max_p = max(eval_df["actual_dollar"].max(), eval_df["pred_dollar"].max())
        ax2.plot([0, max_p], [0, max_p], "r--", lw=1.5, label="Perfect Prediction (y = x)")
        ax2.set_xlabel("Actual Price ($)")
        ax2.set_ylabel("Predicted Price ($)")
        ax2.set_title("Actual vs. Predicted Dollar Price (Test Set)")
        ax2.legend()
        st.pyplot(fig2)
        plt.close(fig2)

with tab3:
    st.subheader("선형 회귀 가정 검정 (잔차 진단 2x2 대시보드)")

    resid_log = eval_df["resid_log"]
    pred_log_arr = eval_df["pred_log"]
    std_resid = (resid_log - resid_log.mean()) / resid_log.std()

    fig3, axes = plt.subplots(2, 2, figsize=(13, 9))

    axes[0, 0].scatter(pred_log_arr, resid_log, alpha=0.15, s=7, color="#2b5c8f")
    axes[0, 0].axhline(0, color="red", linestyle="--", lw=1.4)
    fitted_bins = pd.qcut(pred_log_arr, q=20)
    trend = pd.DataFrame({"fitted": pred_log_arr, "resid": resid_log}).groupby(fitted_bins, observed=False).mean()
    axes[0, 0].plot(trend["fitted"], trend["resid"], color="#ff7f0e", lw=2.0, marker="o", markersize=4, label="Binned Mean")
    axes[0, 0].set_title("1. Residuals vs. Fitted (Log Scale)")
    axes[0, 0].set_xlabel("Fitted log(price)")
    axes[0, 0].set_ylabel("Residual")
    axes[0, 0].legend()

    (osm, osr), (slope, intercept, r_qq) = stats.probplot(std_resid, dist="norm")
    axes[0, 1].scatter(osm, osr, alpha=0.22, s=7, color="#1b9e77")
    axes[0, 1].plot(osm, slope * osm + intercept, "r--", lw=1.4, label=f"Normal Line (R={r_qq:.4f})")
    axes[0, 1].set_title("2. Normal Q-Q Plot")
    axes[0, 1].set_xlabel("Theoretical Quantiles")
    axes[0, 1].set_ylabel("Standardized Residuals")
    axes[0, 1].legend()

    sns.histplot(resid_log, bins=55, stat="density", kde=True, ax=axes[1, 0], color="#7570b3", alpha=0.45)
    x_grid = np.linspace(resid_log.min(), resid_log.max(), 300)
    axes[1, 0].plot(x_grid, stats.norm.pdf(x_grid, resid_log.mean(), resid_log.std()), "r--", lw=1.6, label="Theoretical Normal")
    axes[1, 0].set_title(f"3. Residual Distribution (Skew={resid_log.skew():.2f}, Kurt={resid_log.kurt():.2f})")
    axes[1, 0].set_xlabel("Residual (Log Scale)")
    axes[1, 0].legend()

    sqrt_abs = np.sqrt(np.abs(std_resid))
    axes[1, 1].scatter(pred_log_arr, sqrt_abs, alpha=0.15, s=7, color="#d95f02")
    sl_trend = pd.DataFrame({"fitted": pred_log_arr, "sqrt_resid": sqrt_abs}).groupby(fitted_bins, observed=False).mean()
    axes[1, 1].plot(sl_trend["fitted"], sl_trend["sqrt_resid"], color="black", lw=2.0, marker="o", markersize=4, label="Binned Mean")
    axes[1, 1].set_title("4. Scale-Location Plot (Homoscedasticity)")
    axes[1, 1].set_xlabel("Fitted log(price)")
    axes[1, 1].set_ylabel("sqrt(|Standardized Residuals|)")
    axes[1, 1].legend()

    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

    st.subheader("캐럿 구간별 오차 분해표")
    eval_df["carat_tier"] = pd.cut(
        eval_df["carat"],
        bins=[0, 0.5, 1.0, 1.5, 2.0, 6.0],
        labels=["<= 0.5ct", "0.5 ~ 1.0ct", "1.0 ~ 1.5ct", "1.5 ~ 2.0ct", "> 2.0ct"],
    )
    tier_table = (
        eval_df.groupby("carat_tier", observed=False)
        .agg(
            샘플_수=("resid_log", "count"),
            로그_잔차_평균=("resid_log", "mean"),
            로그_잔차_표준편차=("resid_log", "std"),
            달러_잔차_평균=("resid_dollar", "mean"),
            달러_RMSE=("resid_dollar", lambda x: np.sqrt(np.mean(x**2))),
        )
        .reset_index()
    )
    tier_table["로그_잔차_평균"] = tier_table["로그_잔차_평균"].map(lambda x: f"{x:+.4f}")
    tier_table["로그_잔차_표준편차"] = tier_table["로그_잔차_표준편차"].map(lambda x: f"{x:.4f}")
    tier_table["달러_잔차_평균"] = tier_table["달러_잔차_평균"].map(lambda x: f"${x:+,.2f}")
    tier_table["달러_RMSE"] = tier_table["달러_RMSE"].map(lambda x: f"${x:,.2f}")
    st.dataframe(tier_table, use_container_width=True)
