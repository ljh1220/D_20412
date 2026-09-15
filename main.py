import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

# 웹앱 페이지 기본 설정 (제목, 레이아웃)
st.set_page_config(page_title="박스오피스 데이터 분석", layout="wide")


# [1. 데이터 불러오기]
# @st.cache_data: 데이터를 매번 다시 다운로드하지 않고 캐시에 저장하여 재사용합니다.
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
    df = pd.read_csv(url)

    # [2. 날짜 전처리]
    # 결측치가 포함된 행 삭제
    df = df.dropna()

    # '기준일자' 컬럼을 datetime 형식으로 변환
    df["기준일자"] = pd.to_datetime(df["기준일자"])

    # 기준일자 오름차순 정렬
    df = df.sort_values(by="기준일자", ascending=True)

    return df


# 데이터 로드
df = load_data()

st.title("🎬 영화 박스오피스 데이터 분석 앱")
st.markdown("---")

# [3. 영화 선택 기능]
# 전체 영화 목록 (누적관객수 내림차순 정렬)
movie_rank = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .index.tolist()
)

# 사이드바에 영화 선택 드롭다운 생성
selected_movie = st.sidebar.selectbox("영화를 선택하세요", movie_rank)

# 선택된 영화 데이터만 필터링
filtered_df = df[df["영화명"] == selected_movie]

# -------------------------------------------------------------------
# [구역 1] 선택한 영화 - 일별 관객수 변화 (선그래프)
# -------------------------------------------------------------------
st.header(f"📌 1. {selected_movie} 일별 관객수 추이")

fig_daily_audience = px.line(
    filtered_df,
    x="기준일자",
    y="해당일관객수",
    title=f"[{selected_movie}] 날짜별 해당일관객수 변화",
    markers=True,  # 데이터 지점에 점 표시
    labels={"기준일자": "날짜", "해당일관객수": "일별 관객수(명)"},
)

# 그래프 호버 설정
fig_daily_audience.update_layout(hovermode="x unified")

# 화면에 출력
st.plotly_chart(fig_daily_audience, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 개봉 이후 일자별 관객수의 증감 추이와 주말/평일 간의 관객수 격차를 확인할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------------
# [구역 2] 선택한 영화 - 누적 관객수 변화 (영역차트)
# -------------------------------------------------------------------
st.header(f"📌 2. {selected_movie} 누적 관객수 추이")

# Plotly를 이용한 기준일자별 누적관객수 영역차트(area) 생성
fig_total_audience = px.area(
    filtered_df,
    x="기준일자",
    y="누적관객수",
    title=f"[{selected_movie}] 날짜별 누적관객수 증가 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)"},
)

# 그래프 호버 설정
fig_total_audience.update_layout(hovermode="x unified")

# 화면에 출력
st.plotly_chart(fig_total_audience, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 시간 경과에 따라 관객수가 누적되는 가파른 정도를 통해 흥행 속도와 성수기/비수기 구간의 누적 성장세를 확인할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------------
# [구역 3] 조건에 따른 상위 5개 영화 - 누적 관객수 비교 (다중 선그래프)
# -------------------------------------------------------------------
st.header("📌 3. 장기 흥행 TOP 5 영화 누적 관객수 비교")

# 1) 영화별 TOP 10 차트 등장 일수(행 수) 계산
movie_days = df.groupby("영화명").size()

# 2) 20일 이상 등장한 영화 목록 추출
movies_over_20days = movie_days[movie_days >= 20].index

# 3) 20일 이상 등장한 영화 데이터 중 최대 누적관객수로 정렬하여 상위 5개 영화 선정
top5_long_run_movies = (
    df[df["영화명"].isin(movies_over_20days)]
    .groupby("영화명")["누적관객수"]
    .max()
    .sort_values(ascending=False)
    .head(5)
    .index.tolist()
)

# 4) 상위 5개 영화 데이터 필터링
top5_df = df[df["영화명"].isin(top5_long_run_movies)]

# 5) 다중 선그래프 생성
fig_top5_comparison = px.line(
    top5_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",
    title="TOP10 유지일수 20일 이상인 흥행 상위 5개 영화의 누적 관객수 비교",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수(명)", "영화명": "영화 제목"},
)

# 그래프 호버 및 범례 설정
fig_top5_comparison.update_layout(
    hovermode="x unified",
    legend_title_text="영화 목록",
)

# 화면에 출력
st.plotly_chart(fig_top5_comparison, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 박스오피스 TOP 10에 최소 20일 이상 머무르며 꾸준히 흥행(장기 집권)을 이어간 주요 상위 5개 영화의 관객 증가 양상과 장기 흥행 패턴을 비교할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------------
# [구역 4] 전체 박스오피스 일별 총관객수 및 7일 이동평균선
# -------------------------------------------------------------------
st.header("📌 4. 전체 박스오피스 일별 관객수 흐름 및 7일 이동평균선")

# 1) 기준일자별 TOP10 영화의 '해당일관객수' 전체 합계 계산
daily_total_df = (
    df.groupby("기준일자")["해당일관객수"].sum().reset_index()
)

# 2) 7일 이동평균(Moving Average) 컬럼 생성
daily_total_df["7일_이동평균"] = daily_total_df["해당일관객수"].rolling(window=7).mean()

# 3) Plotly Figure 생성
fig_ma = go.Figure()

# 원본 일별 총 관객수 선 (연하게 표시)
fig_ma.add_trace(
    go.Scatter(
        x=daily_total_df["기준일자"],
        y=daily_total_df["해당일관객수"],
        mode="lines",
        name="일별 총관객수 (원본)",
        line=dict(color="rgba(150, 150, 150, 0.4)", width=1.5),  # 연한 회색/투명도
    )
)

# 7일 이동평균선 (진하게 표시)
fig_ma.add_trace(
    go.Scatter(
        x=daily_total_df["기준일자"],
        y=daily_total_df["7일_이동평균"],
        mode="lines",
        name="7일 이동평균선",
        line=dict(color="#FF4B4B", width=3),  # 진하고 두꺼운 빨간색 선
    )
)

# 레이아웃 설정
fig_ma.update_layout(
    title="전체 박스오피스 일별 총관객수 및 7일 이동평균 추이",
    xaxis_title="날짜",
    yaxis_title="총 관객수(명)",
    hovermode="x unified",
    legend=dict(x=0.01, y=0.99),
)

# 화면에 출력
st.plotly_chart(fig_ma, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 주말과 평일 간 극심한 요일별 변동성을 제거하여, 극장가 전체 시장 규모의 전반적인 상승·하락 흐름(시즌별 성수기 및 비수기 패턴)을 명확하게 파악할 수 있습니다.")

st.markdown("---")

# -------------------------------------------------------------------
# [구역 5] 월별 전체 관객수 합계 (막대그래프)
# -------------------------------------------------------------------
st.header("📌 5. 월별 전체 박스오피스 관객수 합계")

# 1) '기준일자'에서 '연-월(YYYY-MM)' 문자열 추출
daily_total_df["연월"] = daily_total_df["기준일자"].dt.strftime("%Y-%m")

# 2) 연월 단위로 '해당일관객수' 집계
monthly_total_df = (
    daily_total_df.groupby("연월")["해당일관객수"].sum().reset_index()
)

# 3) Plotly 막대그래프 생성
fig_monthly_bar = px.bar(
    monthly_total_df,
    x="연월",
    y="해당일관객수",
    title="월별 극장가 총 관객수 합계",
    text_auto=".2s",  # 막대 위에 축약된 숫자로 관객수 표시 (예: 1.5M, 500k)
    labels={"연월": "연월(Year-Month)", "해당일관객수": "월간 총 관객수(명)"},
    color="해당일관객수",  # 관객수 규모에 따라 색상에 그라데이션 적용
    color_continuous_scale="Viridis",
)

# 레이아웃 설정
fig_monthly_bar.update_layout(
    xaxis_type="category",  # 연-월 라벨이 뭉개지지 않도록 범주형 처리
    hovermode="x unified",
)

# 화면에 출력
st.plotly_chart(fig_monthly_bar, use_container_width=True)

# 그래프 설명문
st.caption("💡 **이 그래프로 알 수 있는 것:** 월별 총 관객 수의 전반적인 분포를 통해 연중 극장가의 최대 성수기 월(여름휴가철, 명절 등)과 비수기 월을 직관적으로 비교·분석할 수 있습니다.")
